# Recira VXLAN Web Controller - Session Continuity Document

**Date**: 2025-11-25
**Version**: v0.7.3 - Host Management + Bug Fixes
**Status**: Troubleshooting DHCP / Underlay Network

---

## SECURITY WARNING

> **LAB/DEVELOPMENT USE ONLY**
>
> This software stores SSH credentials in **cleartext** for convenience.
> Do NOT use in production without implementing proper credential management.
>
> Sensitive data files:
> - `/tmp/recira-hosts.json` - Host SSH credentials
> - `/tmp/recira-dhcp.json` - DHCP configurations
> - `/tmp/recira-networks.json` - Network configurations

---

## System Overview

**Recira** is an open-source SDN platform for managing VXLAN overlay networks across multiple hosts. It provides a web-based UI for:
- Auto-provisioning hosts with Open vSwitch
- Managing VXLAN tunnels between switches
- Creating virtual networks with full-mesh topology
- Dual-interface support (separate management and VXLAN data plane networks)
- DHCP server integration using dnsmasq
- Host persistence (survives server restarts)
- Tunnel discovery (auto-discovers existing VXLAN tunnels)
- Stunning visual topology with D3.js

**Current Setup**:
- Server running on: http://192.168.88.164:8080
- Frontend: Dojo-based UI + D3.js Topology
- Backend: Python HTTP server with OVS integration
- Version: 0.7.2

---

## Network Architecture

### User's Network Design:
- **Management Network**: 192.168.88.0/24 (for SSH, web UI, control plane)
- **VXLAN Network**: 10.172.88.0/24 (for VXLAN tunnel endpoints, MTU 9000)

### Current Hosts (3 Remote + 1 Localhost):

| Host | Management IP | VXLAN IP | Bridge | Notes |
|------|---------------|----------|--------|-------|
| ovs-01 | 192.168.88.194 | 10.172.88.232 | br0 | DHCP server host |
| ovs-02 | 192.168.88.195 | 10.172.88.233 | br0 | |
| ovs-3 | 192.168.88.197 | 10.172.88.234 | br0 | MTU 9000 on ens34 |
| carmine | 192.168.49.217 | N/A | (none) | Localhost, mininet removed |

**Note**: Mininet bridges (s1, s2) were deleted from localhost. Carmine now shows 0 bridges.

---

## Current Session Status

**Last Updated**: 2025-11-25 ~13:00 UTC

### What Was Done This Session:

1. **Cleaned up problematic networks**:
   - Deleted INTERCONNECT network (had mininet switches)
   - Deleted and recreated DEVNET with only real hosts (switches 1, 2, 3)
   - Removed old dnsmasq config files from hosts

2. **Removed mininet from localhost**:
   ```bash
   ovs-vsctl del-br s1
   ovs-vsctl del-br s2
   ```

3. **Created DHCP test script**:
   - Deployed to all 3 hosts as `/usr/local/bin/dhcp-test`
   - Interactive script to test DHCP on any VNI
   - Usage: `dhcp-test` (interactive) or `dhcp-test test 1003`

4. **DHCP Bug Found & Fixed**:
   - Gateway port (vni1003-gw) was NOT tagged with VNI
   - Fixed with: `ovs-vsctl set port vni1003-gw tag=1003`
   - **This fix needs to be added to dhcp_manager.py**

5. **Underlay Network Issue Discovered**:
   - DHCP still failing after gateway port fix
   - Root cause: VXLAN underlay network (10.172.88.0/24) not reachable
   - ovs-02 cannot ping ovs-01's VXLAN IP (10.172.88.232)
   - **User is recreating tunnels/networks to fix this**

6. **Fixed dhcp_manager.py Gateway Port Tagging** (commit 1a8fed5):
   - Added `vni` parameter to `_create_gateway_port` method
   - Gateway port now properly tagged with VNI for overlay isolation
   - Fix works for both new and existing ports

7. **Fixed VXLAN Tunnel Deletion Bug** (commit dc8ce30):
   - Was using `switch_id` instead of `host_id` to find hosts
   - Added `_get_switch_by_id()` and `_get_host_for_switch()` helper methods
   - Tunnel deletion now works correctly

8. **Added Host Management (v0.7.3)** (commit dc8ce30):
   - **Detach Host**: Remove from active management but keep data for later re-attach
   - **Forget Host**: Permanently delete all host data
   - **Re-attach Host**: Reconnect a previously detached host
   - New Managed Hosts table showing all hosts with management actions
   - Detached Hosts section shows hosts that can be re-attached
   - API: `/api/hosts/remove`, `/api/hosts/reattach`, `/api/hosts/detached`

### Current Network State:

**DEVNET** (Network ID: 7):
- VNI: 1003
- Subnet: 10.0.1.0/24
- Gateway: 10.0.1.1
- DHCP: Enabled on ovs-01 (192.168.88.194)
- DHCP Range: 10.0.1.10 - 10.0.1.100
- Switches: 1, 2, 3 (ovs-01, ovs-02, ovs-3)

---

## Pending Issues to Fix

### 1. DHCP Manager Bug - Gateway Port Tagging
**File**: `backend/dhcp_manager.py`
**Status**: FIXED (commit 1a8fed5)

The `_create_gateway_port` method now:
- Accepts `vni` parameter
- Tags the gateway port with the VNI after creation
- Works for both new ports and existing ports (re-tagging)

### 2. Underlay Network Connectivity
The VXLAN underlay network (10.172.88.0/24) needs to be verified:
- Check that each host has the correct VXLAN IP on the correct interface
- Verify routing between hosts on this network
- May need to recreate tunnels with correct remote_ip settings

---

## DHCP Test Script

Installed on all 3 hosts at `/usr/local/bin/dhcp-test`

**Usage:**
```bash
# Interactive mode
dhcp-test

# Quick test
dhcp-test test 1003

# Other commands
dhcp-test list      # List available VNIs
dhcp-test status    # Show test interface status
dhcp-test cleanup   # Remove test interface
dhcp-test help      # Show help
```

**What it does:**
1. Creates OVS internal port tagged with VNI
2. Runs dhclient to request DHCP
3. Shows DHCP handshake in real-time
4. Reports success/failure with IP
5. Cleans up when done

---

## DHCP Architecture Notes

**Q: Is dnsmasq using network namespaces?**
A: No - dnsmasq runs in default namespace, binds to OVS internal port via `interface=` directive

**Q: Can one host run DHCP for multiple networks?**
A: Yes! Each network gets its own config file in `/etc/dnsmasq.d/recira-network-X.conf`

---

## Quick Reference

### SSH Credentials:
- All hosts: `root` / `Xm9909ona`

### Networks:
- Management: 192.168.88.0/24
- VXLAN Underlay: 10.172.88.0/24
- DEVNET Overlay: 10.0.1.0/24

### Start Server:
```bash
cd /root/vxlan-web-controller
python3 backend/server.py
```

### Test DHCP:
```bash
ssh root@192.168.88.195 'dhcp-test test 1003'
```

### GitHub:
https://github.com/bufanoc/recira

---

## Next Steps (When Resuming)

1. **User is recreating tunnels/networks** - wait for completion
2. **Verify underlay connectivity**:
   ```bash
   # From ovs-02, ping ovs-01 VXLAN IP
   ssh root@192.168.88.195 'ping -c 3 10.172.88.232'
   ```
3. **Test DHCP again**:
   ```bash
   ssh root@192.168.88.195 'dhcp-test test 1003'
   ```
4. ~~**Fix dhcp_manager.py** to tag gateway port with VNI~~ **DONE** (commit 1a8fed5)
5. **Continue with v0.8 Port Management** once DHCP is verified

---

## Roadmap Summary

| Version | Feature | Status |
|---------|---------|--------|
| v0.7.2 | Visual Topology | Complete |
| v0.7.3 | Host Management + Bug Fixes | Complete |
| v0.8 | Port Management | Next |
| v1.0 | OpenFlow | Planned |
| v1.1 | Monitoring | Planned |
| v1.2 | KVM Integration | Planned |
| v1.3 | Windows Support | Future |

---

*End of Session Continuity Document*
