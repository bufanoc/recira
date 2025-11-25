#!/usr/bin/env python3
"""
VXLAN Tunnel Manager - Creates and manages VXLAN tunnels between OVS bridges
"""

import subprocess
from typing import Dict, List, Optional, Tuple
import re


class VXLANManager:
    """Manages VXLAN tunnels between OVS bridges"""

    def __init__(self, ovs_manager):
        self.ovs_manager = ovs_manager
        self.tunnels = {}  # {tunnel_id: tunnel_info}
        self.next_tunnel_id = 1
        self.next_vni = 100  # Start VNI from 100

    def discover_tunnels(self):
        """Discover existing VXLAN tunnels from all OVS bridges"""
        print("   Discovering existing VXLAN tunnels...")
        discovered = 0

        # Track unique tunnels by (vni, local_ip, remote_ip) to avoid duplicates
        seen_tunnels = set()

        hosts = self.ovs_manager.get_all_hosts()
        for host in hosts:
            host_ip = host.get('vxlan_ip') or host.get('ip')
            vxlan_ports = self._get_vxlan_ports(host)

            for port_info in vxlan_ports:
                vni = port_info['vni']
                remote_ip = port_info['remote_ip']
                bridge = port_info['bridge']
                port_name = port_info['port_name']

                # Create a canonical key (smaller IP first) to dedupe bidirectional tunnels
                ips = tuple(sorted([host_ip, remote_ip]))
                tunnel_key = (vni, ips[0], ips[1])

                if tunnel_key in seen_tunnels:
                    continue
                seen_tunnels.add(tunnel_key)

                # Find the remote host
                remote_host = self._find_host_by_vxlan_ip(remote_ip)
                if not remote_host:
                    # Remote host not managed by us, skip
                    continue

                # Find switches
                src_switch = self._find_switch_on_host(host['id'], bridge)
                dst_switch = self._find_switch_on_host_by_vxlan_ip(remote_ip)

                if not src_switch or not dst_switch:
                    continue

                # Calculate port names
                dst_ip_suffix = remote_ip.split('.')[-1]
                src_ip_suffix = host_ip.split('.')[-1]

                tunnel_info = {
                    'id': self.next_tunnel_id,
                    'src_switch_id': src_switch['id'],
                    'dst_switch_id': dst_switch['id'],
                    'src_switch_name': src_switch['name'],
                    'dst_switch_name': dst_switch['name'],
                    'src_host': host['hostname'],
                    'dst_host': remote_host['hostname'],
                    'vni': vni,
                    'src_vxlan_ip': host_ip,
                    'dst_vxlan_ip': remote_ip,
                    'tunnel_name_src': f"vxlan{vni}_{dst_ip_suffix}",
                    'tunnel_name_dst': f"vxlan{vni}_{src_ip_suffix}",
                    'status': 'up',
                    'discovered': True
                }

                self.tunnels[self.next_tunnel_id] = tunnel_info
                self.next_tunnel_id += 1
                discovered += 1

                # Update next_vni to avoid conflicts
                if vni >= self.next_vni:
                    self.next_vni = vni + 1

        print(f"      Discovered {discovered} existing tunnel(s)")
        return discovered

    def _get_vxlan_ports(self, host: Dict) -> List[Dict]:
        """Get all VXLAN ports from a host's bridges"""
        vxlan_ports = []
        try:
            if host['type'] == 'localhost':
                cmd = ['ovs-vsctl', 'show']
                result = subprocess.check_output(cmd, text=True)
            else:
                ssh_cmd = self._build_ssh_cmd(host)
                cmd = ssh_cmd + ['ovs-vsctl', 'show']
                result = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)

            # Parse ovs-vsctl show output
            current_bridge = None
            current_port = None
            current_type = None
            current_options = {}

            for line in result.split('\n'):
                line = line.strip()
                if line.startswith('Bridge '):
                    current_bridge = line.split()[1].strip('"')
                elif line.startswith('Port '):
                    # Save previous port if it was vxlan
                    if current_port and current_type == 'vxlan' and 'remote_ip' in current_options:
                        vni = int(current_options.get('key', '0').strip('"'))
                        remote_ip = current_options.get('remote_ip', '').strip('"')
                        if vni and remote_ip:
                            vxlan_ports.append({
                                'bridge': current_bridge,
                                'port_name': current_port,
                                'vni': vni,
                                'remote_ip': remote_ip
                            })
                    current_port = line.split()[1].strip('"')
                    current_type = None
                    current_options = {}
                elif line.startswith('type: '):
                    current_type = line.split(': ')[1]
                elif line.startswith('options: '):
                    # Parse options: {key="1003", remote_ip="10.172.88.233"}
                    opts_str = line.split(': ', 1)[1]
                    opts_str = opts_str.strip('{}')
                    for opt in opts_str.split(', '):
                        if '=' in opt:
                            k, v = opt.split('=', 1)
                            current_options[k] = v.strip('"')

            # Don't forget last port
            if current_port and current_type == 'vxlan' and 'remote_ip' in current_options:
                vni = int(current_options.get('key', '0').strip('"'))
                remote_ip = current_options.get('remote_ip', '').strip('"')
                if vni and remote_ip:
                    vxlan_ports.append({
                        'bridge': current_bridge,
                        'port_name': current_port,
                        'vni': vni,
                        'remote_ip': remote_ip
                    })

        except Exception as e:
            print(f"      Error getting VXLAN ports from {host['hostname']}: {e}")

        return vxlan_ports

    def _find_host_by_vxlan_ip(self, vxlan_ip: str) -> Optional[Dict]:
        """Find a host by its VXLAN IP"""
        hosts = self.ovs_manager.get_all_hosts()
        for host in hosts:
            if host.get('vxlan_ip') == vxlan_ip or host.get('ip') == vxlan_ip:
                return host
        return None

    def _find_switch_on_host(self, host_id: int, bridge_name: str) -> Optional[Dict]:
        """Find a switch by host ID and bridge name"""
        switches = self.ovs_manager.get_all_switches()
        for switch in switches:
            if switch['host_id'] == host_id and switch['name'] == bridge_name:
                return switch
        return None

    def _find_switch_on_host_by_vxlan_ip(self, vxlan_ip: str) -> Optional[Dict]:
        """Find the first switch on a host identified by VXLAN IP"""
        host = self._find_host_by_vxlan_ip(vxlan_ip)
        if not host:
            return None
        switches = self.ovs_manager.get_all_switches()
        for switch in switches:
            if switch['host_id'] == host['id']:
                return switch
        return None

    def create_tunnel(self, src_switch_id: int, dst_switch_id: int,
                     vni: Optional[int] = None) -> Optional[Dict]:
        """
        Create a VXLAN tunnel between two switches

        Args:
            src_switch_id: Source switch ID
            dst_switch_id: Destination switch ID
            vni: VXLAN Network Identifier (auto-assigned if None)

        Returns:
            Tunnel info dict or None on failure
        """
        # Get switch info
        switches = self.ovs_manager.get_all_switches()
        src_switch = next((s for s in switches if s['id'] == src_switch_id), None)
        dst_switch = next((s for s in switches if s['id'] == dst_switch_id), None)

        if not src_switch or not dst_switch:
            print(f"Error: Could not find switches {src_switch_id} or {dst_switch_id}")
            return None

        # Auto-assign VNI if not provided
        if vni is None:
            vni = self.next_vni
            self.next_vni += 1

        # Get host info to determine if local or remote
        src_host = self._get_host_by_id(src_switch['host_id'])
        dst_host = self._get_host_by_id(dst_switch['host_id'])

        if not src_host or not dst_host:
            print("Error: Could not find host information")
            return None

        # Determine VXLAN endpoint IPs (use 10.172.88.x network)
        src_vxlan_ip = self._get_vxlan_ip(src_host)
        dst_vxlan_ip = self._get_vxlan_ip(dst_host)

        if not src_vxlan_ip or not dst_vxlan_ip:
            print("Error: Could not determine VXLAN endpoint IPs")
            return None

        # Create unique tunnel names (include remote IP last octet to avoid conflicts)
        # For multiple tunnels with same VNI, we need unique port names
        dst_ip_suffix = dst_vxlan_ip.split('.')[-1]  # Get last octet of remote IP
        src_ip_suffix = src_vxlan_ip.split('.')[-1]
        tunnel_name_src = f"vxlan{vni}_{dst_ip_suffix}"  # e.g., vxlan1009_233
        tunnel_name_dst = f"vxlan{vni}_{src_ip_suffix}"  # e.g., vxlan1009_234

        # Create VXLAN interface on source switch
        print(f"Creating VXLAN tunnel: {src_switch['name']}@{src_host['hostname']} -> {dst_switch['name']}@{dst_host['hostname']}")
        print(f"  VNI: {vni}, Remote IP: {dst_vxlan_ip}, Port: {tunnel_name_src}")

        if not self._add_vxlan_port(src_host, src_switch['name'], tunnel_name_src, dst_vxlan_ip, vni):
            print("Error: Failed to create VXLAN port on source switch")
            return None

        # Create reverse tunnel on destination switch
        print(f"Creating reverse tunnel: {dst_switch['name']}@{dst_host['hostname']} -> {src_switch['name']}@{src_host['hostname']}")
        print(f"  VNI: {vni}, Remote IP: {src_vxlan_ip}, Port: {tunnel_name_dst}")

        if not self._add_vxlan_port(dst_host, dst_switch['name'], tunnel_name_dst, src_vxlan_ip, vni):
            print("Error: Failed to create VXLAN port on destination switch")
            # Cleanup source port
            self._del_vxlan_port(src_host, src_switch['name'], tunnel_name_src)
            return None

        # Store tunnel info
        tunnel_info = {
            'id': self.next_tunnel_id,
            'src_switch_id': src_switch_id,
            'dst_switch_id': dst_switch_id,
            'src_switch_name': src_switch['name'],
            'dst_switch_name': dst_switch['name'],
            'src_host': src_host['hostname'],
            'dst_host': dst_host['hostname'],
            'vni': vni,
            'src_vxlan_ip': src_vxlan_ip,
            'dst_vxlan_ip': dst_vxlan_ip,
            'tunnel_name_src': tunnel_name_src,
            'tunnel_name_dst': tunnel_name_dst,
            'status': 'up'
        }

        self.tunnels[self.next_tunnel_id] = tunnel_info
        self.next_tunnel_id += 1

        print(f"✅ Tunnel created successfully!")
        return tunnel_info

    def _get_host_by_id(self, host_id: int) -> Optional[Dict]:
        """Get host info by host ID"""
        hosts = self.ovs_manager.get_all_hosts()
        return next((h for h in hosts if h['id'] == host_id), None)

    def _get_vxlan_ip(self, host: Dict) -> Optional[str]:
        """Get the VXLAN endpoint IP for a host"""
        # Use stored vxlan_ip if available, otherwise fall back to management IP
        vxlan_ip = host.get('vxlan_ip')
        if vxlan_ip:
            return vxlan_ip

        # Fall back to management IP (for backward compatibility)
        return host.get('ip')

    def _add_vxlan_port(self, host: Dict, bridge_name: str, port_name: str,
                       remote_ip: str, vni: int) -> bool:
        """Add a VXLAN port to a bridge"""
        try:
            if host['type'] == 'localhost':
                # Local execution
                cmd = [
                    'ovs-vsctl', 'add-port', bridge_name, port_name, '--',
                    'set', 'interface', port_name, 'type=vxlan',
                    f'options:remote_ip={remote_ip}',
                    f'options:key={vni}'
                ]
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Remote execution via SSH
                ssh_cmd = self._build_ssh_cmd(host)
                cmd = ssh_cmd + [
                    'ovs-vsctl', 'add-port', bridge_name, port_name, '--',
                    'set', 'interface', port_name, 'type=vxlan',
                    f'options:remote_ip={remote_ip}',
                    f'options:key={vni}'
                ]
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            return True
        except Exception as e:
            print(f"Error adding VXLAN port: {e}")
            return False

    def _del_vxlan_port(self, host: Dict, bridge_name: str, port_name: str) -> bool:
        """Delete a VXLAN port from a bridge"""
        try:
            if host['type'] == 'localhost':
                cmd = ['ovs-vsctl', 'del-port', bridge_name, port_name]
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                ssh_cmd = self._build_ssh_cmd(host)
                cmd = ssh_cmd + ['ovs-vsctl', 'del-port', bridge_name, port_name]
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            return True
        except Exception as e:
            print(f"Error deleting VXLAN port: {e}")
            return False

    def _build_ssh_cmd(self, host: Dict) -> List[str]:
        """Build SSH command for remote host using stored credentials"""
        # Get credentials from ovs_manager
        username, password = self.ovs_manager.get_host_credentials(host.get('ip'))
        if not password:
            # Fallback for backward compatibility
            password = 'Xm9909ona'
        if not username:
            username = 'root'
        ssh_cmd = ['sshpass', '-p', password, 'ssh', '-o', 'StrictHostKeyChecking=no']
        ssh_cmd.append(f"{username}@{host['ip']}")
        return ssh_cmd

    def get_all_tunnels(self) -> List[Dict]:
        """Get all tunnels"""
        return list(self.tunnels.values())

    def _get_switch_by_id(self, switch_id: int) -> Optional[Dict]:
        """Get switch info by switch ID"""
        switches = self.ovs_manager.get_all_switches()
        return next((s for s in switches if s['id'] == switch_id), None)

    def _get_host_for_switch(self, switch_id: int) -> Optional[Dict]:
        """Get the host that a switch belongs to"""
        switch = self._get_switch_by_id(switch_id)
        if not switch:
            return None
        return self._get_host_by_id(switch['host_id'])

    def delete_tunnel(self, tunnel_id: int) -> bool:
        """Delete a tunnel"""
        if tunnel_id not in self.tunnels:
            print(f"Tunnel {tunnel_id} not found in tunnel list")
            return False

        tunnel = self.tunnels[tunnel_id]

        # Get host info by looking up the switch first, then getting its host
        src_host = self._get_host_for_switch(tunnel['src_switch_id'])
        dst_host = self._get_host_for_switch(tunnel['dst_switch_id'])

        if not src_host or not dst_host:
            print(f"Could not find hosts for tunnel {tunnel_id}")
            print(f"  src_switch_id={tunnel['src_switch_id']}, dst_switch_id={tunnel['dst_switch_id']}")
            # Still remove from our tracking even if we can't delete the ports
            # (e.g., if host was removed)
            del self.tunnels[tunnel_id]
            return True

        # Delete both tunnel endpoints
        # Handle both old and new tunnel name formats for backward compatibility
        tunnel_name_src = tunnel.get('tunnel_name_src', tunnel.get('tunnel_name'))
        tunnel_name_dst = tunnel.get('tunnel_name_dst', tunnel.get('tunnel_name'))

        print(f"Deleting tunnel {tunnel_id}: {tunnel_name_src} on {src_host['hostname']}, {tunnel_name_dst} on {dst_host['hostname']}")

        src_deleted = self._del_vxlan_port(src_host, tunnel['src_switch_name'], tunnel_name_src)
        dst_deleted = self._del_vxlan_port(dst_host, tunnel['dst_switch_name'], tunnel_name_dst)

        if not src_deleted:
            print(f"  Warning: Failed to delete {tunnel_name_src} on {src_host['hostname']}")
        if not dst_deleted:
            print(f"  Warning: Failed to delete {tunnel_name_dst} on {dst_host['hostname']}")

        # Remove from dict regardless of port deletion success
        del self.tunnels[tunnel_id]

        return True


# This will be initialized when imported by server.py
vxlan_manager = None


def initialize(ovs_mgr):
    """Initialize the VXLAN manager with OVS manager"""
    global vxlan_manager
    vxlan_manager = VXLANManager(ovs_mgr)
    return vxlan_manager
