#!/usr/bin/env python3
"""
OVS Manager - Discovers and manages Open vSwitch bridges
Supports both localhost and remote hosts via SSH

v0.7.1 - Added host persistence (hosts saved to JSON file)

WARNING: This version stores SSH credentials in cleartext.
         For lab/development use only. Do not use in production.
"""

import subprocess
import json
import re
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class OVSManager:
    """Manages OVS bridges on local and remote hosts"""

    def __init__(self, config_file: str = '/tmp/recira-hosts.json'):
        self.hosts = {}  # {host_id: {hostname, ip, bridges, ...}}
        self.next_host_id = 1
        self.config_file = config_file

        # Load saved hosts on startup
        self._load_config()

    def _load_config(self):
        """Load host configurations from JSON file and reconnect"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)

                saved_hosts = data.get('hosts', {})
                self.next_host_id = data.get('next_host_id', 1)

                print(f"   Loading {len(saved_hosts)} saved host(s) from {self.config_file}")

                # Reconnect to each saved host
                for host_id_str, host_data in saved_hosts.items():
                    host_type = host_data.get('type', 'remote')

                    if host_type == 'localhost':
                        # Localhost is auto-discovered, skip
                        continue

                    # Try to reconnect to remote host
                    ip = host_data.get('management_ip') or host_data.get('ip')
                    username = host_data.get('ssh_user', 'root')
                    password = host_data.get('ssh_password')
                    vxlan_ip = host_data.get('vxlan_ip')

                    if ip and password:
                        print(f"   Reconnecting to {host_data.get('hostname', ip)}...")
                        # Use internal method to avoid incrementing ID
                        self._reconnect_host(
                            host_id=int(host_id_str),
                            ip=ip,
                            username=username,
                            password=password,
                            vxlan_ip=vxlan_ip,
                            saved_hostname=host_data.get('hostname')
                        )

                # Update next_host_id to be higher than any loaded host
                if self.hosts:
                    max_id = max(self.hosts.keys())
                    if max_id >= self.next_host_id:
                        self.next_host_id = max_id + 1

            except Exception as e:
                print(f"   Warning: Error loading host config: {e}")
        else:
            print(f"   No saved host config found at {self.config_file}")

    def _save_config(self):
        """Save host configurations to JSON file"""
        try:
            # Prepare hosts for saving (include credentials)
            hosts_to_save = {}
            for host_id, host in self.hosts.items():
                # Don't save localhost (it's auto-discovered)
                if host.get('type') == 'localhost':
                    continue

                hosts_to_save[str(host_id)] = {
                    'hostname': host.get('hostname'),
                    'ip': host.get('ip'),
                    'management_ip': host.get('management_ip'),
                    'vxlan_ip': host.get('vxlan_ip'),
                    'type': host.get('type'),
                    'ssh_user': host.get('ssh_user', 'root'),
                    'ssh_password': host.get('ssh_password'),  # WARNING: Cleartext!
                    'ovs_version': host.get('ovs_version'),
                    'saved_at': datetime.now().isoformat()
                }

            data = {
                'hosts': hosts_to_save,
                'next_host_id': self.next_host_id,
                'last_updated': datetime.now().isoformat(),
                'warning': 'CONTAINS CLEARTEXT PASSWORDS - LAB USE ONLY'
            }

            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving host config: {e}")
            return False

    def _reconnect_host(self, host_id: int, ip: str, username: str,
                        password: str, vxlan_ip: Optional[str] = None,
                        saved_hostname: Optional[str] = None) -> bool:
        """Reconnect to a previously saved host"""
        try:
            ssh_cmd = ['sshpass', '-p', password, 'ssh',
                      '-o', 'StrictHostKeyChecking=no',
                      '-o', 'ConnectTimeout=5',
                      f'{username}@{ip}']

            # Get hostname
            try:
                hostname = subprocess.check_output(
                    ssh_cmd + ['hostname'],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=10
                ).strip()
            except:
                hostname = saved_hostname or ip

            # Get OVS version
            try:
                ovs_output = subprocess.check_output(
                    ssh_cmd + ['ovs-vsctl', '--version'],
                    text=True,
                    stderr=subprocess.STDOUT,
                    timeout=10
                )
                match = re.search(r'ovs-vsctl.*?(\d+\.\d+\.\d+)', ovs_output)
                ovs_version = match.group(1) if match else 'unknown'
            except:
                ovs_version = 'unknown'

            # Get bridges
            bridges = []
            try:
                bridges_output = subprocess.check_output(
                    ssh_cmd + ['ovs-vsctl', 'list-br'],
                    text=True,
                    timeout=10
                ).strip()

                if bridges_output:
                    bridge_names = bridges_output.split('\n')
                    for br_name in bridge_names:
                        br_name = br_name.strip()
                        if br_name:
                            br_info = self._get_remote_bridge_details(ssh_cmd, br_name)
                            if br_info:
                                bridges.append(br_info)
            except:
                pass

            host_info = {
                'id': host_id,
                'hostname': hostname,
                'ip': ip,
                'management_ip': ip,
                'vxlan_ip': vxlan_ip if vxlan_ip else ip,
                'type': 'remote',
                'status': 'online',
                'ovs_version': ovs_version,
                'bridges': bridges,
                'ssh_user': username,
                'ssh_password': password  # Store for persistence
            }

            self.hosts[host_id] = host_info
            print(f"      Reconnected to {hostname} ({ip}) - {len(bridges)} bridge(s)")
            return True

        except Exception as e:
            print(f"      Failed to reconnect to {ip}: {e}")
            return False

    def discover_localhost(self, vxlan_ip: Optional[str] = None) -> Dict:
        """
        Discover OVS bridges on localhost

        Args:
            vxlan_ip: IP address to use for VXLAN tunnels (optional)

        Returns host info with discovered bridges
        """
        try:
            hostname = subprocess.check_output(['hostname'], text=True).strip()

            # Get IP address
            ip_output = subprocess.check_output(
                ['hostname', '-I'], text=True
            ).strip()
            ip = ip_output.split()[0] if ip_output else '127.0.0.1'

            # Get OVS version
            ovs_version = self._get_local_ovs_version()

            # Get all bridges
            bridges = self._get_local_bridges()

            host_info = {
                'id': self.next_host_id,
                'hostname': hostname,
                'ip': ip,
                'management_ip': ip,  # For localhost, management IP is same as IP
                'vxlan_ip': vxlan_ip if vxlan_ip else ip,  # Use provided or default to IP
                'type': 'localhost',
                'status': 'online',
                'ovs_version': ovs_version,
                'bridges': bridges
            }

            self.hosts[self.next_host_id] = host_info
            self.next_host_id += 1

            return host_info

        except Exception as e:
            print(f"Error discovering localhost: {e}")
            return None

    def _get_local_ovs_version(self) -> str:
        """Get OVS version from local system"""
        try:
            output = subprocess.check_output(
                ['ovs-vsctl', '--version'],
                text=True,
                stderr=subprocess.STDOUT
            )
            # Parse version from output
            match = re.search(r'ovs-vsctl.*?(\d+\.\d+\.\d+)', output)
            if match:
                return match.group(1)
            return 'unknown'
        except:
            return 'unknown'

    def _get_local_bridges(self) -> List[Dict]:
        """Get all OVS bridges on localhost"""
        bridges = []

        try:
            # Get list of bridge names
            output = subprocess.check_output(
                ['ovs-vsctl', 'list-br'],
                text=True
            ).strip()

            if not output:
                return bridges

            bridge_names = output.split('\n')

            for br_name in bridge_names:
                br_name = br_name.strip()
                if not br_name:
                    continue

                # Get bridge details
                bridge_info = self._get_bridge_details(br_name)
                if bridge_info:
                    bridges.append(bridge_info)

        except Exception as e:
            print(f"Error getting bridges: {e}")

        return bridges

    def _get_bridge_details(self, bridge_name: str) -> Optional[Dict]:
        """Get detailed info about a specific bridge"""
        try:
            # Get datapath ID
            dpid_hex = subprocess.check_output(
                ['ovs-vsctl', 'get', 'bridge', bridge_name, 'datapath-id'],
                text=True
            ).strip().strip('"')

            # Convert hex DPID to decimal
            dpid = int(dpid_hex, 16) if dpid_hex else 0

            # Get controller
            try:
                controller = subprocess.check_output(
                    ['ovs-vsctl', 'get-controller', bridge_name],
                    text=True
                ).strip()
            except:
                controller = ''

            # Get fail mode
            try:
                fail_mode = subprocess.check_output(
                    ['ovs-vsctl', 'get-fail-mode', bridge_name],
                    text=True
                ).strip()
            except:
                fail_mode = 'standalone'

            # Get ports
            ports_output = subprocess.check_output(
                ['ovs-vsctl', 'list-ports', bridge_name],
                text=True
            ).strip()
            ports = ports_output.split('\n') if ports_output else []
            port_count = len([p for p in ports if p.strip()])

            # Check if connected to controller
            connected = False
            if controller:
                try:
                    # Try to check OpenFlow connection
                    of_output = subprocess.check_output(
                        ['ovs-vsctl', 'show'],
                        text=True
                    )
                    # Simple heuristic: if bridge shows controller and no error, assume connected
                    connected = controller in of_output
                except:
                    pass

            return {
                'name': bridge_name,
                'dpid': dpid,
                'dpid_hex': dpid_hex,
                'controller': controller,
                'fail_mode': fail_mode,
                'ports': port_count,
                'connected': connected,
                'port_list': [p.strip() for p in ports if p.strip()]
            }

        except Exception as e:
            print(f"Error getting bridge details for {bridge_name}: {e}")
            return None

    def discover_remote_host(self, ip: str, username: str,
                            password: Optional[str] = None,
                            key_file: Optional[str] = None,
                            vxlan_ip: Optional[str] = None) -> Optional[Dict]:
        """
        Discover OVS bridges on remote host via SSH

        Args:
            ip: IP address of remote host (management IP)
            username: SSH username
            password: SSH password (if using password auth)
            key_file: Path to SSH key file (if using key auth)
            vxlan_ip: IP address to use for VXLAN tunnels (optional)

        Returns:
            Host info dict or None on error
        """
        try:
            # Build SSH command prefix
            ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no']

            if key_file:
                ssh_cmd.extend(['-i', key_file])

            if password:
                # Use sshpass if password provided
                ssh_cmd = ['sshpass', '-p', password] + ssh_cmd

            ssh_cmd.append(f'{username}@{ip}')

            # Get hostname
            hostname = subprocess.check_output(
                ssh_cmd + ['hostname'],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()

            # Get OVS version
            ovs_version_cmd = ssh_cmd + ['ovs-vsctl', '--version']
            ovs_output = subprocess.check_output(
                ovs_version_cmd,
                text=True,
                stderr=subprocess.STDOUT
            )
            match = re.search(r'ovs-vsctl.*?(\d+\.\d+\.\d+)', ovs_output)
            ovs_version = match.group(1) if match else 'unknown'

            # Get bridges
            bridges_output = subprocess.check_output(
                ssh_cmd + ['ovs-vsctl', 'list-br'],
                text=True
            ).strip()

            bridges = []
            if bridges_output:
                bridge_names = bridges_output.split('\n')
                for br_name in bridge_names:
                    br_name = br_name.strip()
                    if br_name:
                        br_info = self._get_remote_bridge_details(
                            ssh_cmd, br_name
                        )
                        if br_info:
                            bridges.append(br_info)

            host_info = {
                'id': self.next_host_id,
                'hostname': hostname,
                'ip': ip,
                'management_ip': ip,  # IP we use to connect/manage
                'vxlan_ip': vxlan_ip if vxlan_ip else ip,  # IP for VXLAN tunnels
                'type': 'remote',
                'status': 'online',
                'ovs_version': ovs_version,
                'bridges': bridges,
                'ssh_user': username,
                'ssh_password': password  # Store for persistence (WARNING: cleartext!)
            }

            self.hosts[self.next_host_id] = host_info
            self.next_host_id += 1

            # Save hosts to disk for persistence
            self._save_config()

            return host_info

        except Exception as e:
            print(f"Error discovering remote host {ip}: {e}")
            return None

    def _get_remote_bridge_details(self, ssh_cmd: List[str],
                                   bridge_name: str) -> Optional[Dict]:
        """Get bridge details from remote host"""
        try:
            # Get DPID
            dpid_hex = subprocess.check_output(
                ssh_cmd + ['ovs-vsctl', 'get', 'bridge', bridge_name, 'datapath-id'],
                text=True
            ).strip().strip('"')
            dpid = int(dpid_hex, 16) if dpid_hex else 0

            # Get controller
            try:
                controller = subprocess.check_output(
                    ssh_cmd + ['ovs-vsctl', 'get-controller', bridge_name],
                    text=True
                ).strip()
            except:
                controller = ''

            # Get ports
            ports_output = subprocess.check_output(
                ssh_cmd + ['ovs-vsctl', 'list-ports', bridge_name],
                text=True
            ).strip()
            ports = ports_output.split('\n') if ports_output else []
            port_count = len([p for p in ports if p.strip()])

            return {
                'name': bridge_name,
                'dpid': dpid,
                'dpid_hex': dpid_hex,
                'controller': controller,
                'fail_mode': 'unknown',
                'ports': port_count,
                'connected': bool(controller),
                'port_list': [p.strip() for p in ports if p.strip()]
            }

        except Exception as e:
            print(f"Error getting remote bridge details for {bridge_name}: {e}")
            return None

    def get_all_hosts(self) -> List[Dict]:
        """Get all discovered hosts (without exposing passwords)"""
        hosts_list = []
        for host in self.hosts.values():
            # Create a copy without the password
            host_copy = {k: v for k, v in host.items() if k != 'ssh_password'}
            hosts_list.append(host_copy)
        return hosts_list

    def get_host_credentials(self, host_ip: str) -> Tuple[str, str]:
        """Get stored credentials for a host (for internal use)"""
        for host in self.hosts.values():
            if host.get('ip') == host_ip or host.get('management_ip') == host_ip:
                return host.get('ssh_user', 'root'), host.get('ssh_password', '')
        return 'root', ''

    def get_all_switches(self) -> List[Dict]:
        """
        Get all switches from all hosts
        Returns list of switches with host info included
        """
        switches = []
        switch_id = 1

        for host in self.hosts.values():
            for bridge in host.get('bridges', []):
                switch = {
                    'id': switch_id,
                    'dpid': bridge['dpid'],
                    'dpid_hex': bridge['dpid_hex'],
                    'name': bridge['name'],
                    'host_id': host['id'],
                    'hostname': host['hostname'],
                    'host_ip': host['ip'],
                    'controller': bridge.get('controller', ''),
                    'fail_mode': bridge.get('fail_mode', 'unknown'),
                    'ports': bridge.get('ports', 0),
                    'connected': bridge.get('connected', False),
                    'port_list': bridge.get('port_list', [])
                }
                switches.append(switch)
                switch_id += 1

        return switches


# Global instance
ovs_manager = OVSManager()


if __name__ == '__main__':
    # Test localhost discovery
    print("Testing OVS Manager...")
    print("\n=== Discovering localhost ===")

    host = ovs_manager.discover_localhost()
    if host:
        print(f"\nHost: {host['hostname']} ({host['ip']})")
        print(f"OVS Version: {host['ovs_version']}")
        print(f"\nBridges found: {len(host['bridges'])}")

        for bridge in host['bridges']:
            print(f"\n  Bridge: {bridge['name']}")
            print(f"    DPID: {bridge['dpid']} (0x{bridge['dpid_hex']})")
            print(f"    Ports: {bridge['ports']}")
            print(f"    Controller: {bridge.get('controller', 'none')}")
            print(f"    Fail Mode: {bridge.get('fail_mode', 'unknown')}")

    print("\n=== All Switches ===")
    switches = ovs_manager.get_all_switches()
    print(json.dumps(switches, indent=2))
