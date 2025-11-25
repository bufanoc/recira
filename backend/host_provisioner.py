#!/usr/bin/env python3
"""
Host Provisioner - Automatic OVS Installation and Configuration (v0.6)

This module provides automated host provisioning for Recira. It can:
- Detect OS type (Ubuntu/Debian/CentOS/RHEL)
- Install Open vSwitch automatically
- Configure MTU to 9000 for VXLAN optimization
- Monitor host health and OVS status
- Optimize OVS configuration for production use

Usage:
    provisioner = HostProvisioner(ip='192.168.1.100', username='root', password='secret')
    result = provisioner.provision_host()
"""

import subprocess
import json
from typing import Dict, Optional, Tuple
from datetime import datetime


class HostProvisioner:
    """Manages automatic host provisioning and OVS installation"""

    def __init__(self, ip: str, username: str = 'root', password: str = None):
        self.ip = ip
        self.username = username
        self.password = password
        self.os_type = None
        self.os_version = None
        self.ovs_installed = False
        self.ovs_version = None

    def _ssh_exec(self, command: str, timeout: int = 300) -> Tuple[int, str, str]:
        """
        Execute command on remote host via SSH

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds (default 300 for package installs)

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if self.password:
            # Use sshpass for password authentication
            ssh_cmd = [
                'sshpass', '-p', self.password,
                'ssh', '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                f'{self.username}@{self.ip}',
                command
            ]
        else:
            # Use SSH key authentication
            ssh_cmd = [
                'ssh', '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                f'{self.username}@{self.ip}',
                command
            ]

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, '', f'Command timed out after {timeout} seconds'
        except Exception as e:
            return -1, '', str(e)

    def detect_os(self) -> Dict[str, str]:
        """
        Detect OS type and version on remote host

        Returns:
            Dictionary with 'type' (ubuntu/debian/centos/rhel) and 'version'
        """
        print(f"🔍 Detecting OS on {self.ip}...")

        # Try to read /etc/os-release (standard on modern Linux)
        rc, stdout, stderr = self._ssh_exec('cat /etc/os-release')

        if rc == 0:
            os_info = {}
            for line in stdout.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os_info[key] = value.strip('"')

            os_id = os_info.get('ID', '').lower()
            version = os_info.get('VERSION_ID', 'unknown')

            # Map OS ID to our supported types
            if os_id in ['ubuntu']:
                self.os_type = 'ubuntu'
                self.os_version = version
            elif os_id in ['debian']:
                self.os_type = 'debian'
                self.os_version = version
            elif os_id in ['centos', 'rhel', 'rocky', 'almalinux']:
                self.os_type = 'centos'  # Treat all RHEL-based as centos
                self.os_version = version
            else:
                print(f"   ⚠️  Unsupported OS: {os_id}")
                return {'type': 'unsupported', 'version': version}

            print(f"   ✅ Detected: {self.os_type.capitalize()} {self.os_version}")
            return {'type': self.os_type, 'version': self.os_version}

        else:
            print(f"   ❌ Failed to detect OS: {stderr}")
            return {'type': 'unknown', 'version': 'unknown'}

    def check_ovs_installed(self) -> bool:
        """
        Check if Open vSwitch is already installed

        Returns:
            True if OVS is installed, False otherwise
        """
        rc, stdout, stderr = self._ssh_exec('ovs-vsctl --version')

        if rc == 0:
            # Parse version from output
            for line in stdout.split('\n'):
                if 'ovs-vsctl' in line.lower():
                    parts = line.split()
                    if len(parts) >= 3:
                        self.ovs_version = parts[2]
                        break

            self.ovs_installed = True
            print(f"   ✅ OVS already installed: {self.ovs_version}")
            return True
        else:
            self.ovs_installed = False
            print(f"   ℹ️  OVS not installed")
            return False

    def install_ovs_ubuntu(self) -> bool:
        """Install OVS on Ubuntu/Debian"""
        print(f"📦 Installing OVS on Ubuntu/Debian...")

        # Update package cache
        print("   - Updating package cache...")
        rc, stdout, stderr = self._ssh_exec('apt-get update', timeout=300)
        if rc != 0:
            print(f"   ❌ Failed to update packages: {stderr}")
            return False

        # Install OVS
        print("   - Installing openvswitch-switch...")
        rc, stdout, stderr = self._ssh_exec(
            'DEBIAN_FRONTEND=noninteractive apt-get install -y openvswitch-switch',
            timeout=600
        )

        if rc != 0:
            print(f"   ❌ Failed to install OVS: {stderr}")
            return False

        # Enable and start OVS service
        print("   - Starting OVS service...")
        self._ssh_exec('systemctl enable openvswitch-switch')
        self._ssh_exec('systemctl start openvswitch-switch')

        # Verify installation
        if self.check_ovs_installed():
            print(f"   ✅ OVS installed successfully: {self.ovs_version}")
            return True
        else:
            print(f"   ❌ OVS installation verification failed")
            return False

    def install_ovs_centos(self) -> bool:
        """Install OVS on CentOS/RHEL"""
        print(f"📦 Installing OVS on CentOS/RHEL...")

        # Install OVS from default repos
        print("   - Installing openvswitch...")
        rc, stdout, stderr = self._ssh_exec(
            'yum install -y openvswitch',
            timeout=600
        )

        if rc != 0:
            print(f"   ❌ Failed to install OVS: {stderr}")
            return False

        # Enable and start OVS service
        print("   - Starting OVS service...")
        self._ssh_exec('systemctl enable openvswitch')
        self._ssh_exec('systemctl start openvswitch')

        # Verify installation
        if self.check_ovs_installed():
            print(f"   ✅ OVS installed successfully: {self.ovs_version}")
            return True
        else:
            print(f"   ❌ OVS installation verification failed")
            return False

    def configure_mtu(self, mtu: int = 9000, target_interface: Optional[str] = None) -> bool:
        """
        Configure MTU for optimal VXLAN performance

        Args:
            mtu: MTU size (default 9000 for jumbo frames)
            target_interface: Specific interface to configure (if None, configure all)

        Returns:
            True if successful, False otherwise
        """
        print(f"⚙️  Configuring MTU to {mtu}...")

        if target_interface:
            # Configure only the specified interface
            print(f"   - Targeting specific interface: {target_interface}")
            rc, stdout, stderr = self._ssh_exec(f'ip link set {target_interface} mtu {mtu}')
            if rc == 0:
                print(f"   ✅ Set MTU {mtu} on {target_interface}")
                return True
            else:
                print(f"   ⚠️  Failed to set MTU on {target_interface}: {stderr}")
                return False
        else:
            # Get list of physical network interfaces (exclude lo, ovs, docker, etc.)
            rc, stdout, stderr = self._ssh_exec(
                "ip -o link show | awk -F': ' '{print $2}' | grep -v '^lo\\|^ovs\\|^docker\\|^veth'"
            )

            if rc != 0:
                print(f"   ⚠️  Could not list network interfaces")
                return False

            interfaces = [iface.strip() for iface in stdout.split('\n') if iface.strip()]

            if not interfaces:
                print(f"   ⚠️  No suitable network interfaces found")
                return False

            # Set MTU on each physical interface
            success_count = 0
            for iface in interfaces:
                rc, stdout, stderr = self._ssh_exec(f'ip link set {iface} mtu {mtu}')
                if rc == 0:
                    print(f"   ✅ Set MTU {mtu} on {iface}")
                    success_count += 1
                else:
                    print(f"   ⚠️  Failed to set MTU on {iface}: {stderr}")

            return success_count > 0

    def optimize_ovs(self) -> bool:
        """
        Apply OVS optimization settings for production use

        Returns:
            True if successful, False otherwise
        """
        print(f"⚙️  Applying OVS optimizations...")

        optimizations = [
            # Enable connection tracking cleanup
            ('other-config:max-idle', '30000'),
            # Set flow eviction threshold
            ('other-config:flow-eviction-threshold', '10000'),
        ]

        for config_key, config_value in optimizations:
            rc, stdout, stderr = self._ssh_exec(
                f'ovs-vsctl set Open_vSwitch . {config_key}={config_value}'
            )
            if rc == 0:
                print(f"   ✅ Set {config_key}={config_value}")
            else:
                print(f"   ⚠️  Failed to set {config_key}: {stderr}")

        return True

    def get_host_health(self) -> Dict:
        """
        Get comprehensive host health status

        Returns:
            Dictionary with health metrics
        """
        health = {
            'timestamp': datetime.now().isoformat(),
            'ip': self.ip,
            'reachable': False,
            'ovs_installed': False,
            'ovs_running': False,
            'ovs_version': None,
            'os_type': None,
            'os_version': None,
            'uptime': None,
            'load_average': None
        }

        # Check if host is reachable
        rc, stdout, stderr = self._ssh_exec('echo "ping"')
        if rc != 0:
            return health

        health['reachable'] = True

        # Get OS info
        os_info = self.detect_os()
        health['os_type'] = os_info.get('type')
        health['os_version'] = os_info.get('version')

        # Check OVS installation
        if self.check_ovs_installed():
            health['ovs_installed'] = True
            health['ovs_version'] = self.ovs_version

            # Check if OVS is running
            rc, stdout, stderr = self._ssh_exec('systemctl is-active openvswitch-switch || systemctl is-active openvswitch')
            health['ovs_running'] = (rc == 0 and 'active' in stdout)

        # Get system uptime
        rc, stdout, stderr = self._ssh_exec('uptime -p')
        if rc == 0:
            health['uptime'] = stdout.strip()

        # Get load average
        rc, stdout, stderr = self._ssh_exec('uptime | awk -F"load average:" \'{print $2}\'')
        if rc == 0:
            health['load_average'] = stdout.strip()

        return health

    def provision_host(self, configure_mtu: bool = True, optimize: bool = True,
                      vxlan_interface: Optional[str] = None) -> Dict:
        """
        Fully provision a host with OVS

        Args:
            configure_mtu: Set MTU to 9000 for VXLAN optimization
            optimize: Apply OVS optimizations
            vxlan_interface: Specific interface to use for VXLAN (optional)

        Returns:
            Dictionary with provisioning results
        """
        result = {
            'success': False,
            'ip': self.ip,
            'os_detected': False,
            'ovs_installed': False,
            'mtu_configured': False,
            'optimizations_applied': False,
            'vxlan_interface': vxlan_interface,
            'errors': []
        }

        print(f"\n{'='*60}")
        print(f"🚀 Provisioning Host: {self.ip}")
        if vxlan_interface:
            print(f"   VXLAN Interface: {vxlan_interface}")
        print(f"{'='*60}\n")

        # Step 1: Detect OS
        os_info = self.detect_os()
        if os_info['type'] in ['unknown', 'unsupported']:
            result['errors'].append(f"Unsupported or unknown OS: {os_info['type']}")
            return result

        result['os_detected'] = True
        result['os_type'] = os_info['type']
        result['os_version'] = os_info['version']

        # Step 2: Check/Install OVS
        if not self.check_ovs_installed():
            if self.os_type in ['ubuntu', 'debian']:
                if not self.install_ovs_ubuntu():
                    result['errors'].append('Failed to install OVS on Ubuntu/Debian')
                    return result
            elif self.os_type == 'centos':
                if not self.install_ovs_centos():
                    result['errors'].append('Failed to install OVS on CentOS/RHEL')
                    return result

        result['ovs_installed'] = True
        result['ovs_version'] = self.ovs_version

        # Step 3: Configure MTU (only on specified VXLAN interface if provided)
        if configure_mtu:
            if self.configure_mtu(9000, target_interface=vxlan_interface):
                result['mtu_configured'] = True
            else:
                result['errors'].append('MTU configuration had warnings (non-fatal)')

        # Step 4: Apply optimizations
        if optimize:
            if self.optimize_ovs():
                result['optimizations_applied'] = True

        result['success'] = True

        print(f"\n{'='*60}")
        print(f"✅ Host Provisioning Complete!")
        print(f"{'='*60}\n")

        return result


# Module-level functions for easier API integration

def provision_new_host(ip: str, username: str = 'root', password: str = None,
                      vxlan_interface: Optional[str] = None, configure_mtu: bool = True,
                      optimize: bool = True) -> Dict:
    """
    Convenience function to provision a new host

    Args:
        ip: Host IP address
        username: SSH username (default: root)
        password: SSH password
        vxlan_interface: Specific interface to use for VXLAN (optional)
        configure_mtu: Set MTU to 9000 for VXLAN optimization
        optimize: Apply OVS optimizations

    Returns:
        Dictionary with provisioning results
    """
    provisioner = HostProvisioner(ip=ip, username=username, password=password)
    return provisioner.provision_host(
        configure_mtu=configure_mtu,
        optimize=optimize,
        vxlan_interface=vxlan_interface
    )


def get_host_status(ip: str, username: str = 'root', password: str = None) -> Dict:
    """
    Get health status of a host

    Args:
        ip: Host IP address
        username: SSH username (default: root)
        password: SSH password

    Returns:
        Dictionary with health metrics
    """
    provisioner = HostProvisioner(ip=ip, username=username, password=password)
    return provisioner.get_host_health()


def scan_host_interfaces(ip: str, username: str = 'root', password: str = None) -> Dict:
    """
    Scan all network interfaces on a host

    Args:
        ip: Host IP address
        username: SSH username (default: root)
        password: SSH password

    Returns:
        Dictionary with interfaces list
    """
    provisioner = HostProvisioner(ip=ip, username=username, password=password)

    # Get all interfaces with IPs
    rc, stdout, stderr = provisioner._ssh_exec(
        "ip -4 addr show | grep -E '^[0-9]+:|inet ' | sed 's/^[0-9]*: //' | sed 's/: <.*$//' | paste -d ' ' - -"
    )

    if rc != 0:
        return {'success': False, 'error': 'Failed to query interfaces'}

    interfaces = []
    for line in stdout.strip().split('\n'):
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) >= 2:
            iface_name = parts[0]

            # Skip loopback and docker interfaces
            if iface_name == 'lo' or iface_name.startswith('docker') or iface_name.startswith('veth'):
                continue

            # Extract IP and netmask from "inet 192.168.88.1/24"
            inet_parts = [p for p in parts if 'inet' in p or '/' in p]
            if inet_parts:
                for part in inet_parts:
                    if '/' in part and not part.startswith('inet'):
                        ip_cidr = part
                        ip_addr, prefix = ip_cidr.split('/')

                        # Get MTU for this interface
                        rc_mtu, stdout_mtu, _ = provisioner._ssh_exec(f"cat /sys/class/net/{iface_name}/mtu")
                        mtu = stdout_mtu.strip() if rc_mtu == 0 else 'unknown'

                        # Get link state
                        rc_state, stdout_state, _ = provisioner._ssh_exec(f"cat /sys/class/net/{iface_name}/operstate")
                        state = stdout_state.strip() if rc_state == 0 else 'unknown'

                        interfaces.append({
                            'name': iface_name,
                            'ip': ip_addr,
                            'prefix': prefix,
                            'cidr': ip_cidr,
                            'mtu': mtu,
                            'state': state
                        })
                        break

    return {
        'success': True,
        'interfaces': interfaces
    }
