#!/usr/bin/env python3
"""
DHCP Manager - dnsmasq Integration for Overlay Networks (v0.7)

This module provides DHCP server management for Recira overlay networks.
It uses dnsmasq on a selected host to provide:
- Automatic IP assignment within overlay networks
- DNS forwarding for overlay hosts
- DHCP reservations (MAC -> IP mapping)

Usage:
    dhcp_mgr = DHCPManager(ovs_manager)
    dhcp_mgr.enable_dhcp(
        network_id=1,
        host_ip='192.168.88.197',
        dhcp_start='10.0.1.10',
        dhcp_end='10.0.1.250'
    )
"""

import subprocess
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class DHCPManager:
    """Manages DHCP services for overlay networks using dnsmasq"""

    def __init__(self, ovs_manager, network_manager, config_file: str = '/tmp/recira-dhcp.json'):
        self.ovs_manager = ovs_manager
        self.network_manager = network_manager
        self.config_file = config_file
        self.dhcp_configs: Dict[int, Dict] = {}  # network_id -> dhcp config

        # Load existing DHCP configs
        self._load_config()

    def _load_config(self):
        """Load DHCP configurations from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.dhcp_configs = {int(k): v for k, v in data.get('dhcp_configs', {}).items()}
                    print(f"   Loaded {len(self.dhcp_configs)} DHCP config(s) from {self.config_file}")
            except Exception as e:
                print(f"   Warning: Error loading DHCP config: {e}")
        else:
            print(f"   No existing DHCP config found at {self.config_file}")

    def _save_config(self):
        """Save DHCP configurations to JSON file"""
        try:
            data = {
                'dhcp_configs': self.dhcp_configs,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving DHCP config: {e}")
            return False

    def _ssh_exec(self, host_ip: str, username: str, password: str,
                  command: str, timeout: int = 60) -> Tuple[int, str, str]:
        """Execute command on remote host via SSH"""
        ssh_cmd = [
            'sshpass', '-p', password,
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            f'{username}@{host_ip}',
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

    def _get_host_credentials(self, host_ip: str) -> Tuple[str, str]:
        """Get SSH credentials for a host from ovs_manager"""
        hosts = self.ovs_manager.get_all_hosts()
        for host in hosts:
            if host.get('ip') == host_ip or host.get('management_ip') == host_ip:
                return host.get('username', 'root'), host.get('password', '')
        return 'root', ''

    def _install_dnsmasq(self, host_ip: str, username: str, password: str) -> bool:
        """Install dnsmasq on host if not present"""
        print(f"   Checking dnsmasq on {host_ip}...")

        # Check if dnsmasq is installed
        rc, stdout, stderr = self._ssh_exec(host_ip, username, password, 'which dnsmasq')
        if rc == 0:
            print(f"   dnsmasq already installed")
            return True

        # Detect OS and install
        rc, stdout, stderr = self._ssh_exec(host_ip, username, password, 'cat /etc/os-release')
        if rc != 0:
            print(f"   Failed to detect OS")
            return False

        os_id = ''
        for line in stdout.split('\n'):
            if line.startswith('ID='):
                os_id = line.split('=')[1].strip('"').lower()
                break

        print(f"   Installing dnsmasq on {os_id}...")

        if os_id in ['ubuntu', 'debian']:
            rc, stdout, stderr = self._ssh_exec(
                host_ip, username, password,
                'DEBIAN_FRONTEND=noninteractive apt-get install -y dnsmasq',
                timeout=300
            )
        elif os_id in ['centos', 'rhel', 'rocky', 'almalinux']:
            rc, stdout, stderr = self._ssh_exec(
                host_ip, username, password,
                'yum install -y dnsmasq',
                timeout=300
            )
        else:
            print(f"   Unsupported OS: {os_id}")
            return False

        if rc != 0:
            print(f"   Failed to install dnsmasq: {stderr}")
            return False

        print(f"   dnsmasq installed successfully")
        return True

    def _create_gateway_port(self, host_ip: str, username: str, password: str,
                             bridge: str, port_name: str, gateway_ip: str,
                             prefix: str = '24') -> bool:
        """Create OVS internal port and assign gateway IP"""
        print(f"   Creating gateway port {port_name} on {bridge}...")

        # Check if port already exists
        rc, stdout, stderr = self._ssh_exec(
            host_ip, username, password,
            f'ovs-vsctl list-ports {bridge} | grep -w {port_name}'
        )

        if rc == 0 and port_name in stdout:
            print(f"   Port {port_name} already exists")
        else:
            # Create internal port
            rc, stdout, stderr = self._ssh_exec(
                host_ip, username, password,
                f'ovs-vsctl add-port {bridge} {port_name} -- set interface {port_name} type=internal'
            )
            if rc != 0:
                print(f"   Failed to create port: {stderr}")
                return False
            print(f"   Created internal port {port_name}")

        # Assign IP address
        rc, stdout, stderr = self._ssh_exec(
            host_ip, username, password,
            f'ip addr add {gateway_ip}/{prefix} dev {port_name} 2>/dev/null || true'
        )

        # Bring interface up
        rc, stdout, stderr = self._ssh_exec(
            host_ip, username, password,
            f'ip link set {port_name} up'
        )
        if rc != 0:
            print(f"   Failed to bring up interface: {stderr}")
            return False

        print(f"   Gateway {gateway_ip}/{prefix} assigned to {port_name}")
        return True

    def _generate_dnsmasq_config(self, network_id: int, vni: int, interface: str,
                                  dhcp_start: str, dhcp_end: str, gateway: str,
                                  netmask: str = '255.255.255.0',
                                  lease_time: str = '24h',
                                  dns_servers: List[str] = None,
                                  reservations: List[Dict] = None) -> str:
        """Generate dnsmasq configuration file content"""
        dns_servers = dns_servers or ['8.8.8.8', '8.8.4.4']
        reservations = reservations or []

        config = f"""# Recira DHCP Configuration for Network {network_id} (VNI {vni})
# Auto-generated - do not edit manually

# Listen only on the overlay interface
interface={interface}
bind-interfaces

# DHCP range
dhcp-range={dhcp_start},{dhcp_end},{netmask},{lease_time}

# Gateway
dhcp-option=option:router,{gateway}

# DNS servers
dhcp-option=option:dns-server,{','.join(dns_servers)}

# Lease file
dhcp-leasefile=/var/lib/misc/dnsmasq-recira-{network_id}.leases

# Log DHCP transactions
log-dhcp

# Don't use /etc/hosts
no-hosts

# Don't read /etc/resolv.conf
no-resolv

# Upstream DNS
"""
        for dns in dns_servers:
            config += f"server={dns}\n"

        # Add MAC reservations
        if reservations:
            config += "\n# Static DHCP reservations\n"
            for res in reservations:
                mac = res.get('mac', '')
                ip = res.get('ip', '')
                hostname = res.get('hostname', '')
                if mac and ip:
                    if hostname:
                        config += f"dhcp-host={mac},{ip},{hostname}\n"
                    else:
                        config += f"dhcp-host={mac},{ip}\n"

        return config

    def enable_dhcp(self, network_id: int, host_ip: str,
                    dhcp_start: str, dhcp_end: str,
                    username: str = None, password: str = None,
                    dns_servers: List[str] = None,
                    lease_time: str = '24h') -> Dict:
        """
        Enable DHCP for a network on a specific host

        Args:
            network_id: ID of the network to enable DHCP for
            host_ip: IP of host that will run DHCP server (management IP)
            dhcp_start: First IP in DHCP range
            dhcp_end: Last IP in DHCP range
            username: SSH username (optional, uses stored credentials)
            password: SSH password (optional, uses stored credentials)
            dns_servers: List of DNS server IPs
            lease_time: DHCP lease duration (default: 24h)

        Returns:
            Dictionary with result status
        """
        result = {
            'success': False,
            'network_id': network_id,
            'host_ip': host_ip,
            'message': ''
        }

        # Get network info
        network = self.network_manager.get_network(network_id)
        if not network:
            result['message'] = f'Network {network_id} not found'
            return result

        if not network.gateway:
            result['message'] = 'Network must have a gateway IP configured'
            return result

        if not network.subnet:
            result['message'] = 'Network must have a subnet configured'
            return result

        # Parse subnet to get netmask
        try:
            prefix = network.subnet.split('/')[1]
            # Convert prefix to netmask
            prefix_int = int(prefix)
            netmask_int = (0xFFFFFFFF << (32 - prefix_int)) & 0xFFFFFFFF
            netmask = '.'.join([str((netmask_int >> (24 - i*8)) & 0xFF) for i in range(4)])
        except:
            netmask = '255.255.255.0'
            prefix = '24'

        # Get credentials - default username to 'root' if not provided
        if not username:
            username = 'root'
        if not password:
            # Try to get from stored host info
            stored_user, stored_pass = self._get_host_credentials(host_ip)
            if stored_pass:
                password = stored_pass
                username = stored_user or username
        if not password:
            result['message'] = 'No SSH credentials available for host'
            return result

        # Find which bridge on this host is part of the network
        bridge = None
        switches = self.ovs_manager.get_all_switches()
        for sw in switches:
            if sw.get('host_ip') == host_ip and sw.get('id') in network.switches:
                bridge = sw.get('name')
                break

        if not bridge:
            result['message'] = f'No switch found on host {host_ip} that is part of network {network_id}'
            return result

        vni = network.vni
        gateway = network.gateway

        print(f"\nEnabling DHCP for network '{network.name}' (VNI {vni})")
        print(f"   Host: {host_ip}")
        print(f"   Bridge: {bridge}")
        print(f"   Gateway: {gateway}")
        print(f"   DHCP Range: {dhcp_start} - {dhcp_end}")

        # Step 1: Install dnsmasq if needed
        if not self._install_dnsmasq(host_ip, username, password):
            result['message'] = 'Failed to install dnsmasq'
            return result

        # Step 2: Create gateway internal port
        port_name = f"vni{vni}-gw"
        if not self._create_gateway_port(host_ip, username, password,
                                         bridge, port_name, gateway, prefix):
            result['message'] = 'Failed to create gateway port'
            return result

        # Step 3: Generate and deploy dnsmasq config
        config_content = self._generate_dnsmasq_config(
            network_id=network_id,
            vni=vni,
            interface=port_name,
            dhcp_start=dhcp_start,
            dhcp_end=dhcp_end,
            gateway=gateway,
            netmask=netmask,
            lease_time=lease_time,
            dns_servers=dns_servers or ['8.8.8.8', '8.8.4.4']
        )

        config_path = f'/etc/dnsmasq.d/recira-network-{network_id}.conf'
        print(f"   Writing dnsmasq config to {config_path}...")

        # Escape the config content for shell
        escaped_content = config_content.replace("'", "'\\''")
        rc, stdout, stderr = self._ssh_exec(
            host_ip, username, password,
            f"mkdir -p /etc/dnsmasq.d && echo '{escaped_content}' > {config_path}"
        )
        if rc != 0:
            result['message'] = f'Failed to write dnsmasq config: {stderr}'
            return result

        # Create lease file directory
        self._ssh_exec(host_ip, username, password,
                       'mkdir -p /var/lib/misc')

        # Step 4: Restart dnsmasq
        print(f"   Restarting dnsmasq...")
        rc, stdout, stderr = self._ssh_exec(
            host_ip, username, password,
            'systemctl restart dnsmasq'
        )
        if rc != 0:
            # Try to start if restart fails
            rc, stdout, stderr = self._ssh_exec(
                host_ip, username, password,
                'systemctl start dnsmasq'
            )
            if rc != 0:
                result['message'] = f'Failed to start dnsmasq: {stderr}'
                return result

        # Enable dnsmasq on boot
        self._ssh_exec(host_ip, username, password,
                       'systemctl enable dnsmasq')

        # Step 5: Save DHCP config
        self.dhcp_configs[network_id] = {
            'enabled': True,
            'host_ip': host_ip,
            'bridge': bridge,
            'port_name': port_name,
            'gateway': gateway,
            'dhcp_start': dhcp_start,
            'dhcp_end': dhcp_end,
            'netmask': netmask,
            'lease_time': lease_time,
            'dns_servers': dns_servers or ['8.8.8.8', '8.8.4.4'],
            'reservations': [],
            'config_path': config_path,
            'enabled_at': datetime.now().isoformat()
        }
        self._save_config()

        result['success'] = True
        result['message'] = f'DHCP enabled for network {network_id}'
        result['dhcp_config'] = self.dhcp_configs[network_id]

        print(f"   DHCP enabled successfully!")
        return result

    def disable_dhcp(self, network_id: int, username: str = None,
                     password: str = None) -> Dict:
        """
        Disable DHCP for a network

        Args:
            network_id: ID of the network
            username: SSH username (optional)
            password: SSH password (optional)

        Returns:
            Dictionary with result status
        """
        result = {
            'success': False,
            'network_id': network_id,
            'message': ''
        }

        if network_id not in self.dhcp_configs:
            result['message'] = f'DHCP not enabled for network {network_id}'
            return result

        config = self.dhcp_configs[network_id]
        host_ip = config.get('host_ip')

        # Get credentials - default username to 'root' if not provided
        if not username:
            username = 'root'
        if not password:
            stored_user, stored_pass = self._get_host_credentials(host_ip)
            if stored_pass:
                password = stored_pass
                username = stored_user or username
        if not password:
            result['message'] = 'No SSH credentials available for host'
            return result

        print(f"\nDisabling DHCP for network {network_id}...")

        # Remove dnsmasq config
        config_path = config.get('config_path', f'/etc/dnsmasq.d/recira-network-{network_id}.conf')
        self._ssh_exec(host_ip, username, password, f'rm -f {config_path}')

        # Restart dnsmasq
        self._ssh_exec(host_ip, username, password, 'systemctl restart dnsmasq')

        # Remove gateway port
        port_name = config.get('port_name')
        bridge = config.get('bridge')
        if port_name and bridge:
            self._ssh_exec(host_ip, username, password,
                          f'ovs-vsctl del-port {bridge} {port_name}')

        # Remove from config
        del self.dhcp_configs[network_id]
        self._save_config()

        result['success'] = True
        result['message'] = f'DHCP disabled for network {network_id}'
        print(f"   DHCP disabled successfully!")
        return result

    def get_dhcp_config(self, network_id: int) -> Optional[Dict]:
        """Get DHCP configuration for a network"""
        return self.dhcp_configs.get(network_id)

    def get_dhcp_leases(self, network_id: int, username: str = None,
                        password: str = None) -> Dict:
        """
        Get active DHCP leases for a network

        Args:
            network_id: ID of the network

        Returns:
            Dictionary with leases list
        """
        result = {
            'success': False,
            'network_id': network_id,
            'leases': []
        }

        if network_id not in self.dhcp_configs:
            result['message'] = f'DHCP not enabled for network {network_id}'
            return result

        config = self.dhcp_configs[network_id]
        host_ip = config.get('host_ip')

        # Get credentials - default username to 'root' if not provided
        if not username:
            username = 'root'
        if not password:
            stored_user, stored_pass = self._get_host_credentials(host_ip)
            if stored_pass:
                password = stored_pass
                username = stored_user or username
        if not password:
            result['message'] = 'No SSH credentials available for host'
            return result

        # Read lease file
        lease_file = f'/var/lib/misc/dnsmasq-recira-{network_id}.leases'
        rc, stdout, stderr = self._ssh_exec(
            host_ip, username, password,
            f'cat {lease_file} 2>/dev/null || echo ""'
        )

        leases = []
        for line in stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 4:
                # Format: timestamp mac ip hostname client-id
                lease = {
                    'expires': int(parts[0]) if parts[0].isdigit() else 0,
                    'mac': parts[1],
                    'ip': parts[2],
                    'hostname': parts[3] if parts[3] != '*' else '',
                }
                if len(parts) >= 5:
                    lease['client_id'] = parts[4]

                # Convert timestamp to ISO format
                if lease['expires'] > 0:
                    lease['expires_at'] = datetime.fromtimestamp(lease['expires']).isoformat()
                else:
                    lease['expires_at'] = 'infinite'

                leases.append(lease)

        result['success'] = True
        result['leases'] = leases
        return result

    def add_reservation(self, network_id: int, mac: str, ip: str,
                        hostname: str = '', username: str = None,
                        password: str = None) -> Dict:
        """
        Add a DHCP reservation (MAC -> IP mapping)

        Args:
            network_id: ID of the network
            mac: MAC address (e.g., '00:11:22:33:44:55')
            ip: Reserved IP address
            hostname: Optional hostname

        Returns:
            Dictionary with result status
        """
        result = {
            'success': False,
            'network_id': network_id,
            'message': ''
        }

        if network_id not in self.dhcp_configs:
            result['message'] = f'DHCP not enabled for network {network_id}'
            return result

        config = self.dhcp_configs[network_id]
        host_ip = config.get('host_ip')

        # Get credentials - default username to 'root' if not provided
        if not username:
            username = 'root'
        if not password:
            stored_user, stored_pass = self._get_host_credentials(host_ip)
            if stored_pass:
                password = stored_pass
                username = stored_user or username
        if not password:
            result['message'] = 'No SSH credentials available for host'
            return result

        # Normalize MAC address
        mac = mac.lower().replace('-', ':')

        # Add to reservations
        reservation = {'mac': mac, 'ip': ip, 'hostname': hostname}
        if 'reservations' not in config:
            config['reservations'] = []

        # Check for duplicate
        for res in config['reservations']:
            if res['mac'] == mac:
                res['ip'] = ip
                res['hostname'] = hostname
                break
        else:
            config['reservations'].append(reservation)

        # Regenerate config and restart dnsmasq
        network = self.network_manager.get_network(network_id)
        if network:
            new_config = self._generate_dnsmasq_config(
                network_id=network_id,
                vni=network.vni,
                interface=config['port_name'],
                dhcp_start=config['dhcp_start'],
                dhcp_end=config['dhcp_end'],
                gateway=config['gateway'],
                netmask=config['netmask'],
                lease_time=config['lease_time'],
                dns_servers=config['dns_servers'],
                reservations=config['reservations']
            )

            escaped_content = new_config.replace("'", "'\\''")
            config_path = config['config_path']

            rc, stdout, stderr = self._ssh_exec(
                host_ip, username, password,
                f"echo '{escaped_content}' > {config_path}"
            )

            if rc == 0:
                self._ssh_exec(host_ip, username, password,
                              'systemctl restart dnsmasq')

        self._save_config()

        result['success'] = True
        result['message'] = f'Reservation added: {mac} -> {ip}'
        result['reservation'] = reservation
        return result

    def delete_reservation(self, network_id: int, mac: str,
                           username: str = None, password: str = None) -> Dict:
        """
        Delete a DHCP reservation

        Args:
            network_id: ID of the network
            mac: MAC address to remove

        Returns:
            Dictionary with result status
        """
        result = {
            'success': False,
            'network_id': network_id,
            'message': ''
        }

        if network_id not in self.dhcp_configs:
            result['message'] = f'DHCP not enabled for network {network_id}'
            return result

        config = self.dhcp_configs[network_id]
        host_ip = config.get('host_ip')

        # Get credentials - default username to 'root' if not provided
        if not username:
            username = 'root'
        if not password:
            stored_user, stored_pass = self._get_host_credentials(host_ip)
            if stored_pass:
                password = stored_pass
                username = stored_user or username
        if not password:
            result['message'] = 'No SSH credentials available for host'
            return result

        # Normalize MAC address
        mac = mac.lower().replace('-', ':')

        # Remove from reservations
        if 'reservations' not in config:
            result['message'] = 'No reservations exist'
            return result

        original_len = len(config['reservations'])
        config['reservations'] = [r for r in config['reservations'] if r['mac'] != mac]

        if len(config['reservations']) == original_len:
            result['message'] = f'Reservation for {mac} not found'
            return result

        # Regenerate config and restart dnsmasq
        network = self.network_manager.get_network(network_id)
        if network:
            new_config = self._generate_dnsmasq_config(
                network_id=network_id,
                vni=network.vni,
                interface=config['port_name'],
                dhcp_start=config['dhcp_start'],
                dhcp_end=config['dhcp_end'],
                gateway=config['gateway'],
                netmask=config['netmask'],
                lease_time=config['lease_time'],
                dns_servers=config['dns_servers'],
                reservations=config['reservations']
            )

            escaped_content = new_config.replace("'", "'\\''")
            config_path = config['config_path']

            rc, stdout, stderr = self._ssh_exec(
                host_ip, username, password,
                f"echo '{escaped_content}' > {config_path}"
            )

            if rc == 0:
                self._ssh_exec(host_ip, username, password,
                              'systemctl restart dnsmasq')

        self._save_config()

        result['success'] = True
        result['message'] = f'Reservation for {mac} deleted'
        return result

    def get_all_dhcp_configs(self) -> List[Dict]:
        """Get all DHCP configurations"""
        configs = []
        for network_id, config in self.dhcp_configs.items():
            config_copy = config.copy()
            config_copy['network_id'] = network_id
            configs.append(config_copy)
        return configs


# Global DHCP manager instance
dhcp_manager = None


def initialize(ovs_mgr, network_mgr, config_file: str = '/tmp/recira-dhcp.json') -> DHCPManager:
    """Initialize the global DHCP manager instance"""
    global dhcp_manager
    dhcp_manager = DHCPManager(ovs_mgr, network_mgr, config_file)
    return dhcp_manager
