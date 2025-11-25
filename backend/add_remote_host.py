#!/usr/bin/env python3
"""
Add remote hosts to the VXLAN controller
"""

import sys
sys.path.insert(0, '/root/vxlan-web-controller/backend')

from ovs_manager import ovs_manager

# Remote VMs to add
remote_hosts = [
    {'ip': '192.168.88.194', 'name': 'VM1 (ovs-01)'},
    {'ip': '192.168.88.195', 'name': 'VM2 (ovs-02)'}
]

print("="*60)
print("Adding Remote Hosts to VXLAN Controller")
print("="*60)

for vm in remote_hosts:
    print(f"\n🔍 Discovering {vm['name']} ({vm['ip']})...")
    host_info = ovs_manager.discover_remote_host(
        ip=vm['ip'],
        username='root',
        password='Xm9909ona'
    )

    if host_info:
        print(f"   ✅ Successfully added!")
        print(f"      Hostname: {host_info['hostname']}")
        print(f"      OVS Version: {host_info['ovs_version']}")
        print(f"      Bridges: {len(host_info['bridges'])}")
        for bridge in host_info['bridges']:
            print(f"         - {bridge['name']} (DPID: {bridge['dpid']}, {bridge['ports']} ports)")
    else:
        print(f"   ❌ Failed to add {vm['name']}")

print("\n" + "="*60)
print("📊 UNIFIED TOPOLOGY - All Managed Switches")
print("="*60)

all_hosts = ovs_manager.get_all_hosts()
all_switches = ovs_manager.get_all_switches()

print(f"\n📍 Total Hosts: {len(all_hosts)}")
for host in all_hosts:
    print(f"   - {host['hostname']} ({host['ip']}) - {host['type']}")

print(f"\n🔌 Total Switches: {len(all_switches)}")
for switch in all_switches:
    print(f"   - {switch['name']}@{switch['hostname']} (DPID: {switch['dpid']}, Host: {switch['host_ip']})")

print("\n" + "="*60)
print("✅ Controller now managing all hosts!")
print("="*60)
