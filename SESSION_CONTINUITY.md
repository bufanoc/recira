# Recira VXLAN Web Controller - Session Continuity Document

**Date**: 2025-11-25
**Version**: v0.7.0 - DHCP Integration
**Status**: Fully Functional with DHCP Support

---

## System Overview

**Recira** is an open-source SDN platform for managing VXLAN overlay networks across multiple hosts. It provides a web-based UI for:
- Auto-provisioning hosts with Open vSwitch
- Managing VXLAN tunnels between switches
- Creating virtual networks with full-mesh topology
- Dual-interface support (separate management and VXLAN data plane networks)
- **NEW in v0.7**: DHCP server integration using dnsmasq

**Current Setup**:
- Server running on: http://192.168.88.164:8080
- Frontend: Dojo-based UI (repurposed from DVSC)
- Backend: Python HTTP server with OVS integration
- Version: 0.7.0

---

## Network Architecture

### User's Network Design:
- **Management Network**: 192.168.88.0/24 (for SSH, web UI, control plane)
- **VXLAN Network**: 10.172.88.0/24 (for VXLAN tunnel endpoints, MTU 9000)

### Current Hosts:
1. **carmine** (localhost - 192.168.49.217)
   - Management IP: 192.168.49.217
   - VXLAN IP: (using default IP)
   - Switches: s1, s2 (connected to external controller at 192.168.88.192:6633)

2. **ovs-3** (192.168.88.197)
   - Management IP: 192.168.88.197
   - VXLAN IP: 10.172.88.234 (ens34)
   - Switches: br0
   - MTU: 9000 on ens34

3. **ovs-02** (192.168.88.195)
   - Management IP: 192.168.88.195
   - VXLAN IP: 10.172.88.233
   - Switches: br0
   - Has existing VXLAN tunnels (vxlan100, vxlan101)

4. **ovs-01** (192.168.88.194)
   - Management IP: 192.168.88.194
   - VXLAN IP: 10.172.88.232
   - Switches: br0
   - Has existing VXLAN tunnels (vxlan100, vxlan101)

---

## Features Implemented in v0.7

### DHCP Integration

**Goal**: Automatic IP assignment in overlay networks using dnsmasq

**Features Implemented**:
- Enable/disable DHCP per network via web UI
- Select which host runs the DHCP server
- Configure DHCP scope (IP range, lease time, DNS servers)
- Auto-configure dnsmasq on selected host
- View active DHCP leases
- DHCP reservations (MAC -> IP mapping)

#### Backend Changes:

**File: `backend/dhcp_manager.py`** (NEW)
- `DHCPManager` class for managing DHCP services
- `enable_dhcp()` - Enable DHCP for a network on a specific host
- `disable_dhcp()` - Disable DHCP for a network
- `get_dhcp_config()` - Get DHCP configuration
- `get_dhcp_leases()` - Read active leases from dnsmasq
- `add_reservation()` - Add MAC -> IP reservation
- `delete_reservation()` - Remove reservation
- Auto-installs dnsmasq if not present
- Creates OVS internal port for gateway
- Generates dnsmasq configuration file
- Persists DHCP config to `/tmp/recira-dhcp.json`

**File: `backend/server.py`**
- Updated version to 0.7.0
- Added `dhcp_manager` initialization
- Added DHCP API endpoints:
  - `POST /api/dhcp/enable` - Enable DHCP for network
  - `POST /api/dhcp/disable` - Disable DHCP for network
  - `GET /api/dhcp/config` - Get DHCP configuration
  - `GET /api/dhcp/leases` - View active leases
  - `POST /api/dhcp/reservation` - Add MAC reservation
  - `POST /api/dhcp/reservation/delete` - Delete reservation
- Updated `/api/networks` to include `dhcp_enabled` status
- Updated `/api/networks/delete` to auto-disable DHCP
- Added `SO_REUSEADDR` to avoid port reuse errors

#### Frontend Changes:

**File: `frontend/37734/index.html`**
- Updated version to 0.7
- Added DHCP column to networks table
- Networks row shows:
  - If DHCP enabled: "ON" badge + range + Leases button + Off button
  - If DHCP disabled (with subnet): "Disabled" + Enable button
  - If no subnet: "N/A - Need subnet"
- Added "Enable DHCP" modal:
  - Network name (read-only)
  - DHCP server host selection dropdown
  - DHCP range start/end inputs (auto-suggested from subnet)
  - DNS servers input
  - Lease time dropdown
  - SSH password input
- Added "DHCP Leases" modal:
  - Table of active leases (IP, MAC, hostname, expiry)
  - Refresh button
- JavaScript functions:
  - `showEnableDHCPModal()` - Show enable dialog
  - `closeEnableDHCPModal()` - Close dialog
  - `enableDHCP()` - Submit enable request
  - `disableDHCP()` - Disable DHCP with confirmation
  - `showDHCPLeases()` - Show leases modal
  - `closeDHCPLeasesModal()` - Close leases
  - `refreshDHCPLeases()` - Reload leases

---

## How to Use DHCP

### Prerequisites:
1. Network must have subnet and gateway configured
2. At least one host must be added to Recira

### Enable DHCP for a Network:

1. Open web UI: http://192.168.88.164:8080
2. In the Networks table, find your network
3. Click "Enable" button in the DHCP column
4. In the modal:
   - Select which host will run DHCP server
   - DHCP range is auto-suggested based on gateway
   - Optionally modify DNS servers and lease time
   - Enter SSH password for the selected host
5. Click "Enable DHCP"

### View DHCP Leases:

1. For networks with DHCP enabled, click "Leases" button
2. View table of active leases:
   - IP address assigned
   - MAC address of client
   - Hostname (if provided)
   - Lease expiration time

### Disable DHCP:

1. Click "Off" button in the DHCP column
2. Confirm the action
3. Enter SSH password when prompted
4. DHCP server will be stopped and gateway port removed

---

## API Endpoints

### Existing Endpoints (unchanged):
- `GET /api/status` - Controller status
- `GET /api/switches` - Connected switches
- `GET /api/hosts` - OVS hosts
- `POST /api/hosts/add` - Add remote host
- `POST /api/hosts/provision` - Auto-provision host
- `GET /api/hosts/health` - Host health status
- `GET /api/hosts/scan-interfaces` - Scan host interfaces
- `GET /api/networks` - Virtual networks (now includes DHCP status)
- `POST /api/networks/create` - Create network
- `POST /api/networks/delete` - Delete network (auto-disables DHCP)
- `GET /api/tunnels` - VXLAN tunnels
- `POST /api/tunnels/create` - Create tunnel
- `POST /api/tunnels/delete` - Delete tunnel
- `GET /api/topology` - Network topology

### New DHCP Endpoints (v0.7):
- `POST /api/dhcp/enable` - Enable DHCP for network
  - Body: `{network_id, host_ip, dhcp_start, dhcp_end, dns_servers?, lease_time?, password}`
- `POST /api/dhcp/disable` - Disable DHCP for network
  - Body: `{network_id, password?}`
- `GET /api/dhcp/config?network_id=X` - Get DHCP configuration
- `GET /api/dhcp/leases?network_id=X` - View active leases
- `POST /api/dhcp/reservation` - Add DHCP reservation
  - Body: `{network_id, mac, ip, hostname?, password?}`
- `POST /api/dhcp/reservation/delete` - Delete reservation
  - Body: `{network_id, mac, password?}`

---

## File Structure

```
/root/vxlan-web-controller/
├── backend/
│   ├── server.py              # Main HTTP server (v0.7)
│   ├── ovs_manager.py         # OVS discovery and management
│   ├── vxlan_manager.py       # VXLAN tunnel creation
│   ├── network_manager.py     # Virtual network management
│   ├── host_provisioner.py    # Auto-provisioning and interface scanning
│   └── dhcp_manager.py        # NEW - DHCP/dnsmasq management
├── frontend/37734/
│   └── index.html             # Web UI (Dojo-based) v0.7
└── SESSION_CONTINUITY.md      # This file
```

---

## Data Storage

- **Networks**: `/tmp/recira-networks.json` (persisted)
- **DHCP Configs**: `/tmp/recira-dhcp.json` (persisted) - NEW
- **Hosts/Switches**: In-memory only (lost on server restart)
- **Tunnels**: In-memory only (lost on server restart)

**Note**: When server restarts, you need to re-add hosts through the UI.

---

## Troubleshooting

### DHCP Not Starting:
```bash
# Check if dnsmasq is installed
ssh root@HOST_IP 'which dnsmasq'

# Check dnsmasq status
ssh root@HOST_IP 'systemctl status dnsmasq'

# Check dnsmasq config
ssh root@HOST_IP 'cat /etc/dnsmasq.d/recira-network-*.conf'

# Check logs
ssh root@HOST_IP 'journalctl -u dnsmasq -n 50'
```

### No DHCP Leases:
- Verify gateway port was created: `ovs-vsctl show`
- Check if client is on the correct network/VLAN
- Verify dnsmasq is listening: `ss -ulnp | grep dnsmasq`

### DHCP Enable Button Not Showing:
- Network must have both subnet AND gateway configured
- Verify in network list that both fields have values

---

## Known Issues and Limitations

1. **In-Memory Host Storage**: Hosts are lost on server restart
2. **No Authentication**: Web UI has no login/authentication
3. **No SSL/TLS**: Server runs on HTTP only
4. **Single DHCP Server**: Each network can only have one DHCP server
5. **No DHCP Failover**: No high-availability for DHCP

---

## Future Enhancements (Roadmap)

- [x] v0.7 - DHCP Integration (COMPLETE)
- [ ] v0.8 - Port Management (assign ports to networks)
- [ ] v0.9 - Visual Topology (D3.js network diagram)
- [ ] v1.0 - OpenFlow Management
- [ ] v1.1 - Statistics & Monitoring
- [ ] v1.2 - KVM Integration
- [ ] v1.3+ - Production Hardening (auth, TLS)

---

## Quick Reference - SSH Credentials

**Current Hosts**:
- All hosts use: `root` / `Xm9909ona`
- Management Network: 192.168.88.0/24
- VXLAN Network: 10.172.88.0/24

---

## Session Status

**Last Updated**: 2025-11-25 10:00 UTC

### v0.7 DHCP Integration Complete

**New Files**:
- `backend/dhcp_manager.py` - Full DHCP management module

**Modified Files**:
- `backend/server.py` - DHCP endpoints and initialization
- `frontend/37734/index.html` - DHCP UI controls

**Testing**:
- Server starts successfully with DHCP manager
- API endpoints return correct responses
- Networks endpoint includes dhcp_enabled status
- Frontend loads with DHCP controls

---

*End of Session Continuity Document*
