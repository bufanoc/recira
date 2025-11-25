# Recira VXLAN Web Controller - Session Continuity Document

**Date**: 2025-11-25
**Version**: v0.7.4 - Storage & API Fixes
**Status**: Hosts re-added, networks created, ready for DHCP testing

---

## SECURITY WARNING

> **LAB/DEVELOPMENT USE ONLY**
>
> This software stores SSH credentials in **cleartext** for convenience.
> Do NOT use in production without implementing proper credential management.
>
> Sensitive data files (NEW LOCATION as of v0.7.4):
> - `/var/lib/recira/hosts.json` - Host SSH credentials
> - `/var/lib/recira/dhcp.json` - DHCP configurations
> - `/var/lib/recira/networks.json` - Network configurations

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
- Host management (detach/forget/re-attach)

**Current Setup**:
- Server running on: http://192.168.88.164:8080
- Frontend: Dojo-based UI + D3.js Topology
- Backend: Python HTTP server with OVS integration
- Version: 0.7.4
- Storage: `/var/lib/recira/` (persistent across reboots)

---

## Network Architecture

### User's Network Design:
- **Management Network**: 192.168.88.0/24 (for SSH, web UI, control plane)
- **VXLAN Network**: 10.172.88.0/24 (for VXLAN tunnel endpoints, MTU 9000)

### Current Hosts (3 Remote + 1 Localhost):

| Host | ID | Management IP | VXLAN IP | Bridge | Notes |
|------|-----|---------------|----------|--------|-------|
| ovs-01 | 7 | 192.168.88.194 | 10.172.88.232 | br0 | Ubuntu 22.04, OVS 2.17.9 |
| ovs-02 | 8 | 192.168.88.195 | 10.172.88.233 | br0 | Ubuntu 22.04, OVS 2.17.9 |
| ovs-3 | 9 | 192.168.88.197 | 10.172.88.234 | br0 | Ubuntu 22.04, OVS 2.17.9 |
| carmine | 10 | 192.168.49.217 | N/A | (none) | Localhost |

**Note**: Hosts were re-provisioned this session with correct dual-interface config.

---

## Current Session Status

**Last Updated**: 2025-11-25 ~14:15 UTC

### What Was Done This Session:

1. **Fixed dhcp_manager.py Gateway Port Tagging** (commit 1a8fed5):
   - Added `vni` parameter to `_create_gateway_port` method
   - Gateway port now properly tagged with VNI for overlay isolation

2. **Fixed VXLAN Tunnel Deletion Bug** (commit dc8ce30):
   - Was using `switch_id` instead of `host_id` to find hosts
   - Added `_get_switch_by_id()` and `_get_host_for_switch()` helper methods
   - Tunnel deletion now works correctly

3. **Added Host Management (v0.7.3)** (commit dc8ce30):
   - **Detach Host**: Remove from active management but keep data
   - **Forget Host**: Permanently delete all host data
   - **Re-attach Host**: Reconnect a previously detached host
   - New Managed Hosts table with full details and actions
   - API: `/api/hosts/remove`, `/api/hosts/reattach`, `/api/hosts/detached`

4. **Fixed VXLAN IP not showing in UI** (commit 568018d):
   - `/api/hosts` endpoint was missing `vxlan_ip` and `management_ip` fields
   - Bug was introduced in v0.6 when host_copy formatting was added
   - Now UI shows correct VXLAN IPs in Managed Hosts table and topology

5. **Moved storage to permanent location** (commit a98ecbf):
   - Changed from `/tmp/recira-*.json` to `/var/lib/recira/*.json`
   - Data now persists across reboots on all systems
   - Migrated existing data to new location

6. **User re-provisioned all 3 hosts**:
   - Removed and re-added hosts through web UI
   - All hosts now have correct Management IP and VXLAN IP configured
   - Network created successfully with tunnels

### Current State:
- Server running with v0.7.4 code
- 4 hosts loaded (3 remote + localhost)
- 17 tunnels discovered
- Storage in `/var/lib/recira/`
- VXLAN IPs correctly displayed in UI

---

## Bug Analysis: VXLAN IP Display Issue

**Root Cause**: The `/api/hosts` endpoint in `server.py` manually constructed a `host_copy` dict but forgot to include `vxlan_ip` and `management_ip` fields.

**When Introduced**: v0.6 (commit 27d13b7) - the same commit that added dual-interface support!

**Why Not Noticed Earlier**:
- Provisioning success message came from provisioner (correct data)
- Tunnels table got IPs from tunnel data (stored correctly)
- Only hosts table/topology relied on the broken endpoint

**Fix**: Added `vxlan_ip` and `management_ip` to the API response formatting.

---

## Pending Tasks

### 1. Test DHCP on Virtual Network
Now that hosts are properly configured with VXLAN IPs:
```bash
# From ovs-02, test DHCP
ssh root@192.168.88.195 'dhcp-test test <VNI>'
```

### 2. Verify Underlay Connectivity
```bash
# From ovs-02, ping ovs-01 VXLAN IP
ssh root@192.168.88.195 'ping -c 3 10.172.88.232'
```

### 3. Continue with v0.8 Port Management
Once DHCP is verified working.

---

## Quick Reference

### SSH Credentials:
- All hosts: `root` / `Xm9909ona`

### Networks:
- Management: 192.168.88.0/24
- VXLAN Underlay: 10.172.88.0/24

### Storage Location:
```
/var/lib/recira/
├── hosts.json      # Host configs + credentials
├── networks.json   # Virtual network definitions
└── dhcp.json       # DHCP configurations
```

### Start Server:
```bash
cd /root/vxlan-web-controller
python3 backend/server.py
```

### GitHub:
https://github.com/bufanoc/recira

---

## Recent Commits (This Session)

| Commit | Description |
|--------|-------------|
| a98ecbf | feat: Move persistent storage from /tmp to /var/lib/recira |
| 568018d | fix: Include vxlan_ip and management_ip in /api/hosts response |
| b87a534 | docs: Update session continuity and roadmap for v0.7.3 |
| dc8ce30 | feat: Add host management and fix tunnel deletion (v0.7.3) |
| d234f18 | docs: Update session continuity - DHCP gateway fix applied |
| 1a8fed5 | fix(dhcp): Tag gateway port with VNI for overlay network isolation |

---

## Roadmap Summary

| Version | Feature | Status |
|---------|---------|--------|
| v0.7.2 | Visual Topology | Complete |
| v0.7.3 | Host Management + Bug Fixes | Complete |
| v0.7.4 | Storage & API Fixes | Complete |
| v0.8 | Port Management | Next |
| v1.0 | OpenFlow | Planned |
| v1.1 | Monitoring | Planned |
| v1.2 | KVM Integration | Planned |
| v1.3 | Windows Support | Future |

---

## DHCP Test Script

Installed on all 3 hosts at `/usr/local/bin/dhcp-test`

**Usage:**
```bash
dhcp-test              # Interactive mode
dhcp-test test <VNI>   # Quick test specific VNI
dhcp-test list         # List available VNIs
dhcp-test cleanup      # Remove test interface
```

---

*End of Session Continuity Document*
*Last updated: 2025-11-25 ~14:15 UTC*
