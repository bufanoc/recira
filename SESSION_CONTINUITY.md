# Recira VXLAN Web Controller - Session Continuity Document

**Date**: 2025-11-25
**Version**: v0.7.6 - STP Loop Prevention
**Status**: Full-mesh VXLAN with STP loop prevention, DHCP working
**GitHub**: https://github.com/bufanoc/recira

---

## SECURITY WARNING

> **LAB/DEVELOPMENT USE ONLY**
>
> This software stores SSH credentials in **cleartext** for convenience.
> Do NOT use in production without implementing proper credential management.
>
> Sensitive data files:
> - `/var/lib/recira/hosts.json` - Host SSH credentials
> - `/var/lib/recira/dhcp.json` - DHCP configurations
> - `/var/lib/recira/networks.json` - Network configurations

---

## Project Overview

**Recira** is an open-source SDN platform for managing VXLAN overlay networks across multiple hosts. Originally built by repurposing the Citrix DVSC web UI (27MB Dojo Toolkit frontend).

### Features:
- Professional web UI with D3.js topology visualization
- Auto-provisioning hosts with Open vSwitch
- Managing VXLAN tunnels between switches
- Creating virtual networks with full-mesh topology
- Dual-interface support (management + VXLAN data plane)
- DHCP server integration using dnsmasq
- Host persistence (survives server restarts)
- Tunnel discovery (auto-discovers existing VXLAN tunnels)
- Host management (detach/forget/re-attach)

### Current Setup:
- Server: http://192.168.88.164:8080
- Backend: Python HTTP server with OVS integration
- Storage: `/var/lib/recira/` (persistent)
- Version: 0.7.4

---

## Network Architecture

### Networks:
| Network | CIDR | Purpose |
|---------|------|---------|
| Management | 192.168.88.0/24 | SSH, web UI, control plane |
| VXLAN Underlay | 10.172.88.0/24 | VXLAN tunnel endpoints (MTU 9000) |

### Current Hosts:

| Host | ID | Management IP | VXLAN IP | Bridge | OS/OVS |
|------|-----|---------------|----------|--------|--------|
| ovs-01 | 7 | 192.168.88.194 | 10.172.88.232 | br0 | Ubuntu 22.04 / OVS 2.17.9 |
| ovs-02 | 8 | 192.168.88.195 | 10.172.88.233 | br0 | Ubuntu 22.04 / OVS 2.17.9 |
| ovs-3 | 9 | 192.168.88.197 | 10.172.88.234 | br0 | Ubuntu 22.04 / OVS 2.17.9 |
| carmine | 10 | 192.168.49.217 | N/A | (none) | Localhost |

### SSH Credentials:
- All hosts: `root` / `Xm9909ona`

---

## Current Session Status (Nov 25)

**Last Updated**: 2025-11-25 ~21:15 UTC

### What Was Done (Latest Session):

1. **Cleaned up all 3 hosts** - Removed leftover OVS ports and routes from previous experiments
   - ovs-01: Removed vxlan100, vxlan101, dhcp-test, old IPs/routes
   - ovs-02: Removed vxlan100, vxlan101, vxlan1001, vxlan1009, vxlan2000
   - ovs-3: Removed vxlan1001, vxlan1004_217, vxlan1009, vxlan2000

2. **Fixed DHCP VLAN tag bug** (commit 57b4f51)
   - Gateway port was incorrectly tagged with VLAN matching VNI
   - This prevented DHCP from working across VXLAN tunnels
   - VXLAN uses VNI for encapsulation - VLAN tags in bridge broke traffic flow
   - Now gateway ports are untagged; existing configs auto-fixed

3. **Fixed L2 Broadcast Storm** - Critical!
   - Full-mesh VXLAN without STP caused broadcast loops
   - ~24,000 packets/sec looping, 2.8 billion total, 183M drops
   - IPv6 Neighbor Discovery from deleted dhcp-test was circulating forever
   - **Solution**: Enabled STP on all bridges
   - ovs-01 is root bridge, ovs-02's link to ovs-3 is blocking
   - Traffic now: 0 packets/sec storm (fixed!)

4. **Added STP to Host Provisioner** (permanent fix)
   - `enable_stp_on_bridges()` method added to host_provisioner.py
   - STP now enabled automatically during host optimization
   - All new hosts will have STP enabled by default

5. **Verified DHCP still works** with STP topology
   - ovs-02 got 10.0.0.127 from DHCP server on ovs-01
   - ovs-3 got 10.0.0.109 from DHCP server on ovs-01

### Previous Session Work:

1. **Fixed dhcp_manager.py Gateway Port Tagging** (commit 1a8fed5)

2. **Fixed VXLAN Tunnel Deletion Bug** (commit dc8ce30)
   - Was using `switch_id` instead of `host_id` to find hosts

3. **Added Host Management (v0.7.3)** (commit dc8ce30)
   - Detach/Forget/Re-attach hosts from web UI
   - API: `/api/hosts/remove`, `/api/hosts/reattach`, `/api/hosts/detached`

4. **Fixed VXLAN IP not showing in UI** (commit 568018d)
   - Bug introduced in v0.6 when host_copy formatting was added

5. **Moved storage to permanent location** (commit a98ecbf)
   - Changed from `/tmp/` to `/var/lib/recira/`

### Current State:
- 4 hosts loaded (3 remote + localhost)
- Network "devs" (VNI 1005) with full-mesh tunnels
- DHCP working on ovs-01 serving 10.0.0.100-150
- Underlay network (10.172.88.0/24) fully operational

---

## Project Structure

```
/root/vxlan-web-controller/
├── backend/
│   ├── server.py              # Main HTTP server
│   ├── ovs_manager.py         # OVS discovery (local + SSH)
│   ├── vxlan_manager.py       # VXLAN tunnel management
│   ├── network_manager.py     # Virtual network management
│   ├── dhcp_manager.py        # DHCP/dnsmasq integration
│   └── host_provisioner.py    # Host auto-provisioning
├── frontend/
│   └── 37734/                 # DVSC web UI (27MB, 1905 JS files)
│       ├── dojo/              # Dojo Toolkit framework
│       ├── dijit/             # Widgets
│       └── index.html         # Dashboard with D3.js topology
├── docs/
│   └── ROADMAP.md             # Development roadmap
├── README.md
└── SESSION_CONTINUITY.md      # This file
```

---

## API Reference

### Host Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hosts` | List all hosts |
| GET | `/api/hosts/detached` | List detached hosts |
| POST | `/api/hosts/add` | Add remote host via SSH |
| POST | `/api/hosts/provision` | Auto-provision with OVS |
| POST | `/api/hosts/remove` | Detach or forget host |
| POST | `/api/hosts/reattach` | Re-attach detached host |
| GET | `/api/hosts/health` | Host health status |

### Network Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/networks` | List virtual networks |
| POST | `/api/networks/create` | Create network with full-mesh |
| POST | `/api/networks/delete` | Delete network and tunnels |

### Tunnel Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tunnels` | List VXLAN tunnels |
| POST | `/api/tunnels/create` | Create VXLAN tunnel |
| POST | `/api/tunnels/delete` | Delete tunnel |

### DHCP Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/dhcp/enable` | Enable DHCP for network |
| POST | `/api/dhcp/disable` | Disable DHCP |
| GET | `/api/dhcp/config` | Get DHCP configuration |
| GET | `/api/dhcp/leases` | View active leases |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Controller status |
| GET | `/api/switches` | All OVS switches |
| GET | `/api/topology` | Network topology |

---

## Quick Commands

### Start Server
```bash
cd /root/vxlan-web-controller
python3 backend/server.py
```

### Add Remote Host (API)
```bash
curl -X POST http://localhost:8080/api/hosts/add \
  -H "Content-Type: application/json" \
  -d '{"ip":"192.168.88.194","username":"root","password":"Xm9909ona","vxlan_ip":"10.172.88.232"}'
```

### Create VXLAN Tunnel
```bash
curl -X POST http://localhost:8080/api/tunnels/create \
  -H "Content-Type: application/json" \
  -d '{"src_switch_id":1,"dst_switch_id":2,"vni":100}'
```

### Test DHCP
```bash
ssh root@192.168.88.195 'dhcp-test test <VNI>'
```

### Check OVS on Remote Host
```bash
ssh root@192.168.88.194 'ovs-vsctl show'
```

---

## DHCP Test Script

Installed on all 3 hosts at `/usr/local/bin/dhcp-test`

```bash
dhcp-test              # Interactive mode
dhcp-test test <VNI>   # Quick test specific VNI
dhcp-test list         # List available VNIs
dhcp-test cleanup      # Remove test interface
```

---

## Storage Location

```
/var/lib/recira/
├── hosts.json      # Host configs + credentials
├── networks.json   # Virtual network definitions
└── dhcp.json       # DHCP configurations
```

---

## Pending Tasks

1. **Continue with v0.8 Port Management**
   - VM port attachment to overlay networks
   - Port tagging for VMs

2. **Consider updating dhcp-test script**
   - Currently uses VLAN tags which may not work
   - Should create untagged test ports instead

---

## Version History

| Version | Date | Features |
|---------|------|----------|
| v0.1 | Nov 24 | Foundation - extracted DVSC UI, mock API |
| v0.2 | Nov 24 | Real OVS discovery (local + SSH) |
| v0.3 | Nov 24 | VXLAN tunnel creation |
| v0.4 | Nov 24 | Interactive tunnel management UI |
| v0.5 | Nov 24 | Network abstraction layer |
| v0.6 | Nov 24 | Host auto-provisioning, dual-interface |
| v0.7.0 | Nov 25 | DHCP integration |
| v0.7.1 | Nov 25 | Host persistence |
| v0.7.2 | Nov 25 | D3.js visual topology |
| v0.7.3 | Nov 25 | Host management, bug fixes |
| v0.7.4 | Nov 25 | Storage location, API fixes |
| v0.7.5 | Nov 25 | DHCP cross-host fix, host cleanup |
| v0.7.6 | Nov 25 | STP loop prevention (critical fix) |

---

## Roadmap

| Version | Feature | Status |
|---------|---------|--------|
| v0.7.6 | STP Loop Prevention | **Current** |
| v0.8 | Port Management | Next |
| v1.0 | OpenFlow | Planned |
| v1.1 | Monitoring | Planned |
| v1.2 | KVM Integration | Planned |
| v1.3 | Windows Support | Future |

---

## Troubleshooting

### Server won't start (port 8080 in use)
```bash
lsof -ti:8080 | xargs kill -9
python3 backend/server.py
```

### Can't SSH to VMs
```bash
ssh root@192.168.88.194  # Password: Xm9909ona
```

### VXLAN tunnel not working
```bash
# Check VXLAN ports exist
ssh root@192.168.88.194 'ovs-vsctl list-ports br0'

# Check underlay connectivity
ping -c 4 10.172.88.232
```

---

## Recent Commits

| Commit | Description |
|--------|-------------|
| (pending) | Enable STP by default in host provisioner |
| 3035eb9 | Update session continuity for v0.7.5 |
| 57b4f51 | Fix DHCP not working across VXLAN tunnels (remove VLAN tags) |
| 4f29ab8 | Merge session continuity documents |
| a98ecbf | Move storage from /tmp to /var/lib/recira |
| 568018d | Fix vxlan_ip missing in /api/hosts response |

---

## Troubleshooting

### L2 Broadcast Storm (high CPU, millions of packets)
```bash
# Check for storm
ssh root@<host> 'cat /sys/class/net/br0/statistics/rx_packets; sleep 5; cat /sys/class/net/br0/statistics/rx_packets'

# Enable STP on all bridges (fix)
ssh root@<host> 'ovs-vsctl set bridge br0 stp_enable=true'

# Verify STP topology
ssh root@<host> 'ovs-appctl stp/show br0'
```

### Server won't start (port 8080 in use)
```bash
lsof -ti:8080 | xargs kill -9
python3 backend/server.py
```

### Can't SSH to VMs
```bash
ssh root@192.168.88.194  # Password: Xm9909ona
```

### VXLAN tunnel not working
```bash
# Check VXLAN ports exist
ssh root@192.168.88.194 'ovs-vsctl list-ports br0'

# Check underlay connectivity
ping -c 4 10.172.88.232
```

---

*End of Session Continuity Document*
*Last updated: 2025-11-25 ~21:15 UTC*
