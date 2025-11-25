# Recira VXLAN Web Controller - Session Continuity Document

**Date**: 2025-11-25
**Version**: v0.7.1 - Host Persistence + DHCP Integration
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
- **NEW in v0.7.1**: Host persistence (survives server restarts)

**Current Setup**:
- Server running on: http://192.168.88.164:8080
- Frontend: Dojo-based UI (repurposed from DVSC)
- Backend: Python HTTP server with OVS integration
- Version: 0.7.1

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

## Features Implemented in v0.7.1

### Host Persistence (NEW!)

**Problem Solved**: Previously, hosts were lost on server restart.

**Solution**: Hosts are now saved to `/tmp/recira-hosts.json` and automatically reconnected on startup.

**How It Works**:
1. When you add a host, credentials are saved to JSON file
2. On server restart, OVSManager loads saved hosts
3. Server automatically reconnects to each saved host via SSH
4. Bridges are re-discovered and switches appear in UI

**Files Changed**:
- `backend/ovs_manager.py`:
  - Added `_load_config()` - Load hosts on startup
  - Added `_save_config()` - Save hosts when added
  - Added `_reconnect_host()` - Reconnect to saved host
  - Added `get_host_credentials()` - Get stored credentials
  - Modified `discover_remote_host()` - Store password and save
  - Modified `get_all_hosts()` - Filter out passwords from API

- `backend/server.py`:
  - Filter passwords from `/api/hosts/add` response
  - Filter passwords from `/api/hosts/provision` response

- `backend/dhcp_manager.py`:
  - Uses `ovs_manager.get_host_credentials()` for stored passwords

### DHCP Integration (v0.7.0)

**Features**:
- Enable/disable DHCP per network via web UI
- Select which host runs the DHCP server
- Configure DHCP scope (IP range, lease time, DNS servers)
- Auto-configure dnsmasq on selected host
- View active DHCP leases
- DHCP reservations (MAC -> IP mapping)

---

## Data Storage (All Persisted!)

| Data | File | Survives Restart |
|------|------|------------------|
| Hosts | `/tmp/recira-hosts.json` | Yes |
| Networks | `/tmp/recira-networks.json` | Yes |
| DHCP | `/tmp/recira-dhcp.json` | Yes |
| Tunnels | In-memory | No (but networks recreate them) |

**Note**: Tunnels are stored as part of network config, so deleting and recreating a network will restore tunnels.

---

## Current Active Network

**Network: DEVNET**
- VNI: 1003
- Subnet: 10.0.1.0/24
- Gateway: 10.0.1.1
- DHCP: Enabled on ovs-01 (192.168.88.194)
- DHCP Range: 10.0.1.10 - 10.0.1.20
- Switches: ovs-01, ovs-02, ovs-3 (full-mesh)

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
- `GET /api/tunnels` - VXLAN tunnels
- `GET /api/topology` - Network topology

---

## File Structure

```
/root/vxlan-web-controller/
├── backend/
│   ├── server.py              # Main HTTP server (v0.7.1)
│   ├── ovs_manager.py         # OVS discovery + host persistence
│   ├── vxlan_manager.py       # VXLAN tunnel creation
│   ├── network_manager.py     # Virtual network management
│   ├── host_provisioner.py    # Auto-provisioning
│   └── dhcp_manager.py        # DHCP/dnsmasq management
├── frontend/37734/
│   └── index.html             # Web UI (Dojo-based)
├── docs/
│   └── ROADMAP.md             # Development roadmap
├── README.md                  # Project documentation
└── SESSION_CONTINUITY.md      # This file
```

---

## Troubleshooting

### Hosts Not Reconnecting on Restart:
```bash
# Check hosts file exists
cat /tmp/recira-hosts.json

# Check server log for reconnection messages
tail -50 /tmp/recira-server.log | grep -i "reconnect"

# Verify SSH connectivity
sshpass -p 'PASSWORD' ssh root@HOST_IP 'hostname'
```

### DHCP Not Working:
```bash
# Check dnsmasq on DHCP host
ssh root@192.168.88.194 'systemctl status dnsmasq'

# Check config file
ssh root@192.168.88.194 'cat /etc/dnsmasq.d/recira-network-*.conf'

# Check gateway port
ssh root@192.168.88.194 'ovs-vsctl show | grep vni'
ssh root@192.168.88.194 'ip addr show vni1003-gw'
```

### Network Tunnels Missing:
- Delete and recreate the network (tunnels are created automatically)
- Or manually check each host's OVS bridges

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
- [ ] v0.8 - Port Management (assign ports to networks)
- [ ] v0.9 - Visual Topology (D3.js network diagram)
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

**Last Updated**: 2025-11-25 10:30 UTC

### v0.7.1 Host Persistence Complete

**Changes**:
- Hosts now persist across server restarts
- Credentials stored with hosts (cleartext for lab)
- Auto-reconnect on startup
- DHCP uses stored credentials automatically
- API responses filter out passwords
- Security warning added to README

**Verified**:
- Added 3 hosts, restarted server, all 3 reconnected automatically
- DHCP enabled on DEVNET network
- All tunnels and bridges verified on all hosts

---

*End of Session Continuity Document*
