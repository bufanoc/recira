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

        # Create tunnel name
        tunnel_name = f"vxlan{vni}"

        # Create VXLAN interface on source switch
        print(f"Creating VXLAN tunnel: {src_switch['name']}@{src_host['hostname']} -> {dst_switch['name']}@{dst_host['hostname']}")
        print(f"  VNI: {vni}, Remote IP: {dst_vxlan_ip}")

        if not self._add_vxlan_port(src_host, src_switch['name'], tunnel_name, dst_vxlan_ip, vni):
            print("Error: Failed to create VXLAN port on source switch")
            return None

        # Create reverse tunnel on destination switch
        reverse_tunnel_name = f"vxlan{vni}"
        print(f"Creating reverse tunnel: {dst_switch['name']}@{dst_host['hostname']} -> {src_switch['name']}@{src_host['hostname']}")
        print(f"  VNI: {vni}, Remote IP: {src_vxlan_ip}")

        if not self._add_vxlan_port(dst_host, dst_switch['name'], reverse_tunnel_name, src_vxlan_ip, vni):
            print("Error: Failed to create VXLAN port on destination switch")
            # Cleanup source port
            self._del_vxlan_port(src_host, src_switch['name'], tunnel_name)
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
            'tunnel_name': tunnel_name,
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
        """Get the VXLAN endpoint IP for a host (10.172.88.x network)"""
        if host['type'] == 'localhost':
            # For localhost, return eth4 IP
            return '10.172.88.231'  # Hard-coded for now
        else:
            # For remote hosts, extract from IP
            # VM1: 192.168.88.194 -> 10.172.88.232
            # VM2: 192.168.88.195 -> 10.172.88.233
            if '192.168.88.194' in host['ip']:
                return '10.172.88.232'
            elif '192.168.88.195' in host['ip']:
                return '10.172.88.233'
        return None

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
        """Build SSH command for remote host"""
        ssh_cmd = ['sshpass', '-p', 'Xm9909ona', 'ssh', '-o', 'StrictHostKeyChecking=no']
        ssh_cmd.append(f"root@{host['ip']}")
        return ssh_cmd

    def get_all_tunnels(self) -> List[Dict]:
        """Get all tunnels"""
        return list(self.tunnels.values())

    def delete_tunnel(self, tunnel_id: int) -> bool:
        """Delete a tunnel"""
        if tunnel_id not in self.tunnels:
            return False

        tunnel = self.tunnels[tunnel_id]

        # Get host info
        src_host = self._get_host_by_id(tunnel['src_switch_id'])
        dst_host = self._get_host_by_id(tunnel['dst_switch_id'])

        if not src_host or not dst_host:
            return False

        # Delete both tunnel endpoints
        self._del_vxlan_port(src_host, tunnel['src_switch_name'], tunnel['tunnel_name'])
        self._del_vxlan_port(dst_host, tunnel['dst_switch_name'], tunnel['tunnel_name'])

        # Remove from dict
        del self.tunnels[tunnel_id]

        return True


# This will be initialized when imported by server.py
vxlan_manager = None


def initialize(ovs_mgr):
    """Initialize the VXLAN manager with OVS manager"""
    global vxlan_manager
    vxlan_manager = VXLANManager(ovs_mgr)
    return vxlan_manager
