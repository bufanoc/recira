# Recira VXLAN Web Controller - Session Continuity Document

**Date**: 2025-11-25
**Version**: v0.7.2 - Visual Topology + Tunnel Discovery
**Status**: Fully Functional

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
- **NEW in v0.7.2**: Stunning visual topology with D3.js

**Current Setup**:
- Server running on: http://192.168.88.164:8080
- Frontend: Dojo-based UI + D3.js Topology (repurposed from DVSC)
- Backend: Python HTTP server with OVS integration
- Version: 0.7.2

---

## Network Architecture

### User's Network Design:
- **Management Network**: 192.168.88.0/24 (for SSH, web UI, control plane)
- **VXLAN Network**: 10.172.88.0/24 (for VXLAN tunnel endpoints, MTU 9000)

### Current Hosts (Persisted):
1. **carmine** (localhost - 192.168.49.217)
   - Management IP: 192.168.49.217
   - Type: localhost (auto-discovered on startup)
   - Switches: s1, s2

2. **ovs-01** (192.168.88.194)
   - Management IP: 192.168.88.194
   - VXLAN IP: 10.172.88.232
   - Switches: br0
   - DHCP Server: Running for DEVNET network

3. **ovs-02** (192.168.88.195)
   - Management IP: 192.168.88.195
   - VXLAN IP: 10.172.88.233
   - Switches: br0

4. **ovs-3** (192.168.88.197)
   - Management IP: 192.168.88.197
   - VXLAN IP: 10.172.88.234
   - Switches: br0
   - MTU: 9000 on ens34

---

## Features Implemented in v0.7.2

### Visual Topology (NEW!)

**Stunning D3.js-powered network visualization showing your entire VXLAN fabric!**

**Visual Elements**:
- Dark gradient background with subtle grid pattern (space-like theme)
- Purple gradient host nodes (servers) with hostname and VXLAN IP displayed
- Blue circular switch nodes showing OVS bridge names
- Animated curved tunnel lines with vibrant gradient colors per VNI
- Dashed lines connecting hosts to their OVS switches
- Glowing effects on all nodes

**Interactivity**:
- **Drag nodes** - Rearrange the layout to your liking
- **Zoom/Pan** - Scroll to zoom, drag background to pan
- **Hover tooltips** - Shows detailed info for hosts, switches, and tunnels
- **Pause/Play** - Toggle the flowing animation on tunnel lines
- **Reset** - Restore the force-directed layout
- **Expand** - Make the visualization larger (500px -> 800px)

**Real-time Updates**:
- Stats panel: Hosts, Switches, Tunnels, VNIs count
- Legend dynamically shows VNI colors
- Auto-refreshes when data changes (30-second interval)

**VNI Color Palette**:
Each VNI gets a unique gradient color:
- Blue (#00d2ff → #3a7bd5)
- Pink-Red (#f857a6 → #ff5858)
- Green (#11998e → #38ef7d)
- Orange (#fc4a1a → #f7b733)
- Purple (#8E2DE2 → #4A00E0)
- And 5 more vibrant gradients!

**Files Changed**:
- `frontend/37734/index.html`:
  - Added D3.js v7 library from CDN
  - Added ~200 lines of CSS for topology styling
  - Added ~500 lines of JavaScript for D3 visualization
  - New topology container with controls, legend, stats

### Tunnel Discovery (v0.7.2)

**Problem Solved**: Tunnels were lost on server restart (stored in-memory only).

**Solution**: Tunnels are now auto-discovered by scanning OVS bridges on all hosts.

**How It Works**:
1. On startup, `vxlan_manager.discover_tunnels()` is called
2. Scans all hosts' OVS bridges via SSH for VXLAN ports
3. Parses VNI and remote_ip from port options
4. Deduplicates bidirectional tunnels (same VNI between same hosts)
5. Creates tunnel records in memory with status "up"

**Files Changed**:
- `backend/vxlan_manager.py`:
  - Added `discover_tunnels()` - Main discovery method
  - Added `_get_vxlan_ports()` - Parse OVS show output
  - Added `_find_host_by_vxlan_ip()` - Lookup host by IP
  - Added `_find_switch_on_host()` - Find switch by host/bridge
  - Updated `_build_ssh_cmd()` - Uses stored credentials

- `backend/server.py`:
  - Calls `discover_tunnels()` during initialization
  - Version updated to 0.7.2

---

## Previous Features

### Host Persistence (v0.7.1)
- Hosts saved to `/tmp/recira-hosts.json`
- Auto-reconnect on server restart
- Credentials stored with hosts

### DHCP Integration (v0.7.0)
- Enable/disable DHCP per network
- dnsmasq configuration
- Leases viewer and reservations

---

## Data Storage (All Persisted!)

| Data | File | Survives Restart |
|------|------|------------------|
| Hosts | `/tmp/recira-hosts.json` | Yes |
| Networks | `/tmp/recira-networks.json` | Yes |
| DHCP | `/tmp/recira-dhcp.json` | Yes |
| Tunnels | Discovered from OVS | Yes (via discovery) |

---

## Current Active Network

**Network: DEVNET**
- VNI: 1003
- Subnet: 10.0.1.0/24
- Gateway: 10.0.1.1
- DHCP: Enabled on ovs-01 (192.168.88.194)
- DHCP Range: 10.0.1.10 - 10.0.1.20
- Switches: ovs-01, ovs-02, ovs-3 (full-mesh)

**Current Statistics**:
- 4 Hosts
- 5 Switches
- 14 Tunnels
- 9 Unique VNIs

---

## API Endpoints

### Host Endpoints:
- `GET /api/hosts` - List hosts (passwords hidden)
- `POST /api/hosts/add` - Add host (saves credentials)
- `POST /api/hosts/provision` - Auto-provision with OVS
- `GET /api/hosts/health` - Host health status
- `GET /api/hosts/scan-interfaces` - Scan interfaces

### Network Endpoints:
- `GET /api/networks` - List networks (includes DHCP status)
- `POST /api/networks/create` - Create network
- `POST /api/networks/delete` - Delete network

### Tunnel Endpoints:
- `GET /api/tunnels` - VXLAN tunnels (now persisted via discovery!)
- `POST /api/tunnels/create` - Create tunnel
- `POST /api/tunnels/delete` - Delete tunnel

### DHCP Endpoints:
- `POST /api/dhcp/enable` - Enable DHCP
- `POST /api/dhcp/disable` - Disable DHCP
- `GET /api/dhcp/config?network_id=X` - Get config
- `GET /api/dhcp/leases?network_id=X` - View leases
- `POST /api/dhcp/reservation` - Add reservation
- `POST /api/dhcp/reservation/delete` - Delete reservation

### Other Endpoints:
- `GET /api/status` - Controller status
- `GET /api/switches` - Connected switches
- `GET /api/topology` - Network topology

---

## File Structure

```
/root/vxlan-web-controller/
├── backend/
│   ├── server.py              # Main HTTP server (v0.7.2)
│   ├── ovs_manager.py         # OVS discovery + host persistence
│   ├── vxlan_manager.py       # VXLAN tunnel creation + discovery
│   ├── network_manager.py     # Virtual network management
│   ├── host_provisioner.py    # Auto-provisioning
│   └── dhcp_manager.py        # DHCP/dnsmasq management
├── frontend/37734/
│   └── index.html             # Web UI (Dojo + D3.js topology)
├── docs/
│   └── ROADMAP.md             # Development roadmap
├── README.md                  # Project documentation
└── SESSION_CONTINUITY.md      # This file
```

---

## Troubleshooting

### Topology Not Showing:
```bash
# Check D3.js is loading (browser console)
# Should see no errors related to d3

# Check API returns data
curl http://localhost:8080/api/hosts
curl http://localhost:8080/api/switches
curl http://localhost:8080/api/tunnels
```

### Tunnels Not Discovered:
```bash
# Check server log
tail -20 /tmp/recira-server.log | grep -i "tunnel"

# Should see: "Discovered X existing tunnel(s)"

# Verify VXLAN ports exist on hosts
ssh root@192.168.88.194 'ovs-vsctl show | grep vxlan'
```

### Hosts Not Reconnecting on Restart:
```bash
# Check hosts file exists
cat /tmp/recira-hosts.json

# Check server log for reconnection messages
tail -50 /tmp/recira-server.log | grep -i "reconnect"
```

### DHCP Not Working:
```bash
# Check dnsmasq on DHCP host
ssh root@192.168.88.194 'systemctl status dnsmasq'

# Check config file
ssh root@192.168.88.194 'cat /etc/dnsmasq.d/recira-network-*.conf'
```

---

## Known Issues and Limitations

1. **Cleartext Passwords**: SSH credentials stored in plaintext (lab use only)
2. **No Authentication**: Web UI has no login
3. **No SSL/TLS**: Server runs on HTTP only
4. **Single DHCP Server**: One DHCP server per network
5. **No DHCP Failover**: No HA for DHCP

---

## Future Enhancements (Roadmap)

- [x] v0.7.0 - DHCP Integration (COMPLETE)
- [x] v0.7.1 - Host Persistence (COMPLETE)
- [x] v0.7.2 - Tunnel Discovery (COMPLETE)
- [x] v0.7.2 - Visual Topology (COMPLETE) - Originally planned for v0.9!
- [ ] v0.8 - Port Management (assign ports to networks)
- [ ] v1.0 - OpenFlow Management
- [ ] v1.1 - Statistics & Monitoring
- [ ] v1.2 - KVM Integration
- [ ] v1.3+ - Production Hardening (auth, TLS, encrypted credentials)

---

## Quick Reference

### SSH Credentials:
- All hosts: `root` / `Xm9909ona`

### Networks:
- Management: 192.168.88.0/24
- VXLAN: 10.172.88.0/24
- DEVNET Overlay: 10.0.1.0/24

### Start Server:
```bash
cd /root/vxlan-web-controller
python3 backend/server.py
```

### GitHub:
https://github.com/bufanoc/recira

---

## Session Status

**Last Updated**: 2025-11-25 11:00 UTC

### v0.7.2 Visual Topology + Tunnel Discovery Complete

**Major Additions**:
1. **Stunning D3.js Topology Visualization**
   - Force-directed graph layout
   - Animated gradient tunnel lines
   - Interactive drag, zoom, pan
   - Hover tooltips with details
   - Real-time stats display
   - VNI color-coded legend

2. **Tunnel Discovery**
   - Auto-discovers existing VXLAN ports on startup
   - Scans all OVS bridges on all hosts
   - Deduplicates bidirectional tunnels
   - Uses stored SSH credentials
   - 14 tunnels discovered automatically

**Verified**:
- Topology displays all 4 hosts, 5 switches, 14 tunnels
- Animation flows smoothly on tunnel lines
- Tooltips show correct data
- Zoom/pan/drag all working
- Real-time updates when data changes
- Tunnels persist across server restarts via discovery

---

*End of Session Continuity Document*
