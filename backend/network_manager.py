#!/usr/bin/env python3
"""
Network Manager - Virtual Network Abstraction Layer (v0.5)

This module provides network-level abstraction over individual VXLAN tunnels.
Instead of manually creating point-to-point tunnels, users create "networks"
that automatically provision full-mesh tunnels between all participating switches.

Key Concepts:
- Network: A named virtual network with VNI, subnet, and gateway
- Full-mesh: Automatically create VXLAN tunnels between all switches in a network
- Persistence: Network configurations saved to JSON file
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class Network:
    """Represents a virtual overlay network"""

    def __init__(self, network_id: int, name: str, vni: int, subnet: str,
                 gateway: str, switches: List[int] = None):
        self.id = network_id
        self.name = name
        self.vni = vni
        self.subnet = subnet
        self.gateway = gateway
        self.switches = switches or []  # List of switch IDs
        self.created_at = datetime.now().isoformat()
        self.tunnels = []  # List of tunnel IDs created for this network

    def to_dict(self) -> dict:
        """Convert network to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'vni': self.vni,
            'subnet': self.subnet,
            'gateway': self.gateway,
            'switches': self.switches,
            'created_at': self.created_at,
            'tunnels': self.tunnels
        }

    @staticmethod
    def from_dict(data: dict) -> 'Network':
        """Create Network object from dictionary"""
        network = Network(
            network_id=data['id'],
            name=data['name'],
            vni=data['vni'],
            subnet=data['subnet'],
            gateway=data['gateway'],
            switches=data.get('switches', [])
        )
        network.created_at = data.get('created_at', datetime.now().isoformat())
        network.tunnels = data.get('tunnels', [])
        return network


class NetworkManager:
    """Manages virtual networks and their full-mesh tunnel provisioning"""

    def __init__(self, ovs_manager, vxlan_manager, config_file: str = '/tmp/recira-networks.json'):
        self.ovs_manager = ovs_manager
        self.vxlan_manager = vxlan_manager
        self.config_file = config_file
        self.networks: Dict[int, Network] = {}
        self.next_network_id = 1
        self.next_vni = 1000  # Start VNI allocation at 1000

        # Load existing networks from config file
        self._load_config()

    def _load_config(self):
        """Load network configurations from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)

                    # Restore networks
                    for net_data in data.get('networks', []):
                        network = Network.from_dict(net_data)
                        self.networks[network.id] = network

                    # Restore ID counters
                    self.next_network_id = data.get('next_network_id', 1)
                    self.next_vni = data.get('next_vni', 1000)

                    print(f"✅ Loaded {len(self.networks)} network(s) from {self.config_file}")
            except Exception as e:
                print(f"⚠️  Error loading network config: {e}")
        else:
            print(f"ℹ️  No existing network config found at {self.config_file}")

    def _save_config(self):
        """Save network configurations to JSON file"""
        try:
            data = {
                'networks': [net.to_dict() for net in self.networks.values()],
                'next_network_id': self.next_network_id,
                'next_vni': self.next_vni,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"❌ Error saving network config: {e}")
            return False

    def _allocate_vni(self) -> int:
        """Allocate next available VNI"""
        # Check if VNI is already in use
        used_vnis = {net.vni for net in self.networks.values()}

        while self.next_vni in used_vnis:
            self.next_vni += 1

        vni = self.next_vni
        self.next_vni += 1
        return vni

    def create_network(self, name: str, switches: List[int],
                      vni: Optional[int] = None, subnet: Optional[str] = None,
                      gateway: Optional[str] = None) -> Optional[Network]:
        """
        Create a new virtual network with full-mesh tunnels between switches

        Args:
            name: Human-readable network name (e.g., "Production", "DMZ")
            switches: List of switch IDs to include in this network
            vni: VXLAN Network Identifier (auto-allocated if not specified)
            subnet: Network subnet in CIDR notation (e.g., "10.0.0.0/24")
            gateway: Gateway IP address (e.g., "10.0.0.1")

        Returns:
            Network object if successful, None otherwise
        """

        # Validate switches exist
        all_switches = {sw['id']: sw for sw in self.ovs_manager.get_all_switches()}
        for switch_id in switches:
            if switch_id not in all_switches:
                print(f"❌ Switch ID {switch_id} not found")
                return None

        # Allocate VNI if not provided
        if vni is None:
            vni = self._allocate_vni()
        else:
            # Check if VNI already in use
            for net in self.networks.values():
                if net.vni == vni:
                    print(f"❌ VNI {vni} already in use by network '{net.name}'")
                    return None

        # Create network object
        network = Network(
            network_id=self.next_network_id,
            name=name,
            vni=vni,
            subnet=subnet or "",
            gateway=gateway or "",
            switches=switches
        )

        # Create full-mesh tunnels between all switches
        print(f"🔗 Creating full-mesh tunnels for network '{name}' (VNI {vni})...")
        created_tunnels = []

        for i, src_switch_id in enumerate(switches):
            for dst_switch_id in switches[i+1:]:  # Only create each tunnel once
                tunnel = self.vxlan_manager.create_tunnel(
                    src_switch_id=src_switch_id,
                    dst_switch_id=dst_switch_id,
                    vni=vni
                )

                if tunnel:
                    created_tunnels.append(tunnel['id'])
                    src_name = all_switches[src_switch_id]['name']
                    dst_name = all_switches[dst_switch_id]['name']
                    print(f"   ✅ Tunnel: {src_name} ↔ {dst_name}")
                else:
                    print(f"   ⚠️  Failed to create tunnel between {src_switch_id} and {dst_switch_id}")

        # Store tunnel IDs in network
        network.tunnels = created_tunnels

        # Add to networks dict
        self.networks[network.id] = network
        self.next_network_id += 1

        # Persist to disk
        self._save_config()

        print(f"✅ Network '{name}' created with {len(created_tunnels)} tunnels")
        return network

    def delete_network(self, network_id: int) -> bool:
        """
        Delete a network and all its associated tunnels

        Args:
            network_id: ID of network to delete

        Returns:
            True if successful, False otherwise
        """
        if network_id not in self.networks:
            print(f"❌ Network ID {network_id} not found")
            return False

        network = self.networks[network_id]

        print(f"🗑️  Deleting network '{network.name}' (VNI {network.vni})...")

        # Delete all tunnels associated with this network
        deleted_count = 0
        for tunnel_id in network.tunnels:
            if self.vxlan_manager.delete_tunnel(tunnel_id):
                deleted_count += 1

        print(f"   ✅ Deleted {deleted_count}/{len(network.tunnels)} tunnels")

        # Remove from networks dict
        del self.networks[network_id]

        # Persist to disk
        self._save_config()

        print(f"✅ Network '{network.name}' deleted")
        return True

    def get_network(self, network_id: int) -> Optional[Network]:
        """Get network by ID"""
        return self.networks.get(network_id)

    def get_network_by_vni(self, vni: int) -> Optional[Network]:
        """Get network by VNI"""
        for network in self.networks.values():
            if network.vni == vni:
                return network
        return None

    def get_all_networks(self) -> List[dict]:
        """Get all networks as dictionaries"""
        all_switches = {sw['id']: sw for sw in self.ovs_manager.get_all_switches()}

        networks_list = []
        for network in self.networks.values():
            net_dict = network.to_dict()

            # Add switch names for display
            net_dict['switch_names'] = [
                all_switches[sw_id]['name'] if sw_id in all_switches else f"Unknown-{sw_id}"
                for sw_id in network.switches
            ]

            # Add tunnel count
            net_dict['tunnel_count'] = len(network.tunnels)

            networks_list.append(net_dict)

        return networks_list

    def add_switch_to_network(self, network_id: int, switch_id: int) -> bool:
        """
        Add a switch to existing network and create tunnels to all other switches

        Args:
            network_id: ID of network
            switch_id: ID of switch to add

        Returns:
            True if successful, False otherwise
        """
        if network_id not in self.networks:
            print(f"❌ Network ID {network_id} not found")
            return False

        network = self.networks[network_id]

        if switch_id in network.switches:
            print(f"⚠️  Switch {switch_id} already in network '{network.name}'")
            return False

        # Verify switch exists
        all_switches = {sw['id']: sw for sw in self.ovs_manager.get_all_switches()}
        if switch_id not in all_switches:
            print(f"❌ Switch ID {switch_id} not found")
            return False

        # Create tunnels to all existing switches in network
        print(f"🔗 Adding switch to network '{network.name}'...")
        new_tunnels = []

        for existing_switch_id in network.switches:
            tunnel = self.vxlan_manager.create_tunnel(
                src_switch_id=switch_id,
                dst_switch_id=existing_switch_id,
                vni=network.vni
            )

            if tunnel:
                new_tunnels.append(tunnel['id'])
                src_name = all_switches[switch_id]['name']
                dst_name = all_switches[existing_switch_id]['name']
                print(f"   ✅ Tunnel: {src_name} ↔ {dst_name}")

        # Add switch and tunnels to network
        network.switches.append(switch_id)
        network.tunnels.extend(new_tunnels)

        # Persist to disk
        self._save_config()

        print(f"✅ Switch added to network '{network.name}' with {len(new_tunnels)} new tunnels")
        return True


# Global network manager instance (initialized by server.py)
network_manager = None


def initialize(ovs_mgr, vxlan_mgr, config_file: str = '/tmp/recira-networks.json') -> NetworkManager:
    """Initialize the global network manager instance"""
    global network_manager
    network_manager = NetworkManager(ovs_mgr, vxlan_mgr, config_file)
    return network_manager
