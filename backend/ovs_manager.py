#!/usr/bin/env python3
"""
OVS Manager - Discovers and manages Open vSwitch bridges
Supports both localhost and remote hosts via SSH
"""

import subprocess
import json
import re
from typing import Dict, List, Optional, Tuple


class OVSManager:
    """Manages OVS bridges on local and remote hosts"""

    def __init__(self):
        self.hosts = {}  # {host_id: {hostname, ip, bridges, ...}}
        self.next_host_id = 1

    def discover_localhost(self) -> Dict:
        """
        Discover OVS bridges on localhost
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
                            key_file: Optional[str] = None) -> Optional[Dict]:
        """
        Discover OVS bridges on remote host via SSH

        Args:
            ip: IP address of remote host
            username: SSH username
            password: SSH password (if using password auth)
            key_file: Path to SSH key file (if using key auth)

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
                'type': 'remote',
                'status': 'online',
                'ovs_version': ovs_version,
                'bridges': bridges,
                'ssh_user': username
            }

            self.hosts[self.next_host_id] = host_info
            self.next_host_id += 1

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
        """Get all discovered hosts"""
        return list(self.hosts.values())

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
