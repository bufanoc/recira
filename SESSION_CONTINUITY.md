# Recira VXLAN Web Controller - Session Continuity Document

**Date**: 2025-11-25
**Version**: v0.6.1 - Bug Fixes (Frontend Timing + VXLAN Port Naming)
**Status**: Fully Functional with Dual-Interface Support

---

## System Overview

**Recira** is an open-source SDN platform for managing VXLAN overlay networks across multiple hosts. It provides a web-based UI for:
- Auto-provisioning hosts with Open vSwitch
- Managing VXLAN tunnels between switches
- Creating virtual networks with full-mesh topology
- Dual-interface support (separate management and VXLAN data plane networks)

**Current Setup**:
- Server running on: http://192.168.88.164:8080
- Frontend: Dojo-based UI (repurposed from DVSC)
- Backend: Python HTTP server with OVS integration
- Version: 0.6.1

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

## Features Implemented This Session

### 1. Interface Selection for Dual-Network Hosts

**Problem**: User has dual-interface hosts where management and VXLAN traffic use different networks. Need to select which interface is used for VXLAN tunnel endpoints.

**Solution**: Two-step workflow for both "Add Host" and "Provision Host" modals.

#### Backend Changes:

**File: `backend/host_provisioner.py`**
- Added `scan_host_interfaces()` function:
  - Connects via SSH to remote host
  - Runs `ip -4 addr show` to discover all interfaces
  - Returns interface name, IP/CIDR, MTU, and link state
  - Filters out loopback, Docker, and veth interfaces

- Updated `configure_mtu(mtu, target_interface=None)`:
  - Now accepts optional `target_interface` parameter
  - If specified, only sets MTU on that interface (not all interfaces)
  - Prevents accidentally changing MTU on management interface

- Updated `provision_host(vxlan_interface=None)`:
  - Accepts optional `vxlan_interface` parameter
  - Passes it to `configure_mtu()` for targeted MTU configuration

**File: `backend/server.py`**
- Added `/api/hosts/scan-interfaces` endpoint (GET):
  - Parameters: `ip`, `username`, `password`
  - Returns: `{success: true, interfaces: [...]}`
  - Used by frontend before adding/provisioning host

- Updated `/api/hosts/add` endpoint (POST):
  - Now accepts optional `vxlan_ip` parameter
  - Passes to `ovs_manager.discover_remote_host()`

- Updated `/api/hosts/provision` endpoint (POST):
  - Now accepts `vxlan_interface` and `vxlan_ip` parameters
  - Provisions host with MTU only on selected interface
  - Stores both management and VXLAN IPs

**File: `backend/ovs_manager.py`**
- Updated `discover_localhost(vxlan_ip=None)`:
  - Stores both `management_ip` and `vxlan_ip` fields in host record
  - Falls back to regular IP if vxlan_ip not provided

- Updated `discover_remote_host(vxlan_ip=None)`:
  - Stores both `management_ip` and `vxlan_ip` fields in host record
  - Management IP used for SSH connections
  - VXLAN IP used for tunnel endpoints

**File: `backend/vxlan_manager.py`**
- Updated `_get_vxlan_ip(host)`:
  - Removed hard-coded IP mappings
  - Now uses `host.get('vxlan_ip')` from stored host record
  - Falls back to management IP for backward compatibility

#### Frontend Changes:

**File: `frontend/37734/index.html`**

**Add Host Modal** - Converted to two-step workflow:
- Step 1: Enter credentials (IP, username, password)
- Step 2: Scan interfaces and select VXLAN interface
  - Shows table with: Interface name, IP/CIDR, MTU, Link state
  - Auto-suggests interfaces with 10.172.x IP or MTU 9000
  - Radio button selection for VXLAN interface

**Provision Host Modal** - Same two-step workflow:
- Step 1: Enter credentials
- Step 2: Select VXLAN interface
- After provisioning, displays success with both IPs

**JavaScript Functions Added**:
- `scanAddHostInterfaces()` - Calls `/api/hosts/scan-interfaces`
- `displayAddHostInterfaces()` - Renders interface table
- `submitAddHost()` - Submits with selected `vxlan_ip`
- `backToAddHostStep1()` - Navigation between steps
- Same functions for Provision Host modal

---

## How to Use the System

### Starting the Server:

```bash
cd /root/vxlan-web-controller
nohup python3 backend/server.py > /tmp/recira-server.log 2>&1 &
```

Check status:
```bash
curl http://localhost:8080/api/status
```

### Adding a Host (with Interface Selection):

1. Open web UI: http://192.168.88.164:8080
2. Click "Add Host" button
3. **Step 1**: Enter credentials
   - Host IP: 192.168.88.X (management IP)
   - Username: root
   - Password: (your password)
4. Click "Scan Interfaces"
5. **Step 2**: Select VXLAN interface
   - System auto-suggests 10.172.x interfaces
   - Select the interface for VXLAN traffic
6. Click "Add Host"

### Provisioning a New Host:

1. Click "Provision Host" button
2. **Step 1**: Enter credentials (same as above)
3. Click "Scan Interfaces"
4. **Step 2**: Select VXLAN interface
5. Click "Start Provisioning"
   - Installs OVS via apt-get/yum
   - Sets MTU to 9000 on selected interface ONLY
   - Applies OVS optimizations
   - May take 5-10 minutes

### Creating a Virtual Network (Full-Mesh):

1. Click "Create Network" button
2. Enter network details:
   - **Name**: e.g., "Production Network"
   - **VNI**: e.g., 1009 (or leave empty for auto-assign)
   - **Subnet**: e.g., 10.0.1.0/24 (optional)
   - **Gateway**: e.g., 10.0.1.1 (optional)
3. **Select switches** to include (checkboxes)
   - Can select switches from any/all hosts
4. Click "Create Network"

**What Happens**:
- Creates full-mesh of VXLAN tunnels between all selected switches
- All tunnels use the same VNI
- Uses VXLAN IPs (10.172.88.x) as tunnel endpoints, not management IPs
- Tunnels are grouped as a single logical network

---

## API Endpoints

### Host Management:
- `GET /api/hosts` - List all hosts
- `POST /api/hosts/add` - Add existing host (with OVS already installed)
  - Body: `{ip, username, password, vxlan_ip?}`
- `POST /api/hosts/provision` - Auto-provision new host
  - Body: `{ip, username, password, vxlan_interface?, vxlan_ip?, configure_mtu?, optimize?}`
- `GET /api/hosts/scan-interfaces` - Scan network interfaces on host
  - Query: `?ip=X&username=Y&password=Z`
- `GET /api/hosts/health` - Get host health status

### Network Management:
- `GET /api/networks` - List all virtual networks
- `POST /api/networks/create` - Create virtual network with full-mesh
  - Body: `{name, switches: [ids], vni?, subnet?, gateway?}`
- `POST /api/networks/delete` - Delete network and all its tunnels
  - Body: `{network_id}`

### Tunnel Management:
- `GET /api/tunnels` - List all VXLAN tunnels
- `POST /api/tunnels/create` - Create single point-to-point tunnel
  - Body: `{src_switch_id, dst_switch_id, vni?}`
- `POST /api/tunnels/delete` - Delete tunnel
  - Body: `{tunnel_id}`

### Switch Management:
- `GET /api/switches` - List all OVS switches (bridges) across all hosts
- `GET /api/topology` - Network topology (nodes and links)
- `GET /api/status` - Controller status and uptime

---

## File Structure

```
/root/vxlan-web-controller/
├── backend/
│   ├── server.py              # Main HTTP server
│   ├── ovs_manager.py         # OVS discovery and management
│   ├── vxlan_manager.py       # VXLAN tunnel creation
│   ├── network_manager.py     # Virtual network management
│   └── host_provisioner.py    # Auto-provisioning and interface scanning
├── frontend/37734/
│   └── index.html             # Web UI (Dojo-based)
└── SESSION_CONTINUITY.md      # This file
```

---

## Data Storage

- **Networks**: `/tmp/recira-networks.json` (persisted)
- **Hosts/Switches**: In-memory only (lost on server restart)
- **Tunnels**: In-memory only (lost on server restart)

**Note**: When server restarts, you need to re-add hosts through the UI.

---

## Important Implementation Details

### VXLAN IP Selection Logic:

The system now properly handles dual-interface hosts:

1. **During host add/provision**: User selects VXLAN interface via UI
2. **Backend stores**: Both `management_ip` (for SSH) and `vxlan_ip` (for tunnels)
3. **When creating tunnels**: System uses `vxlan_ip` from host records

Example host record:
```json
{
  "id": 2,
  "hostname": "ovs-3",
  "ip": "192.168.88.197",
  "management_ip": "192.168.88.197",
  "vxlan_ip": "10.172.88.234",
  "type": "remote",
  "ovs_version": "2.17.9",
  "bridges": [...]
}
```

### MTU Configuration:

- **Before**: Set MTU 9000 on ALL physical interfaces
- **After**: Only sets MTU on the selected VXLAN interface
- **Why**: Prevents breaking management network connectivity

### Network Persistence:

Networks are saved to `/tmp/recira-networks.json` in this format:
```json
{
  "id": 1,
  "name": "Production Network",
  "vni": 1009,
  "subnet": "10.0.1.0/24",
  "gateway": "10.0.1.1",
  "switches": [3, 4, 5],
  "tunnels": [1, 2, 3],
  "created_at": "2025-11-25T..."
}
```

---

## Troubleshooting

### Server Not Running:
```bash
# Kill any stuck processes
pkill -9 -f "python3.*server.py"

# Start fresh
cd /root/vxlan-web-controller
nohup python3 backend/server.py > /tmp/recira-server.log 2>&1 &

# Check log
tail -f /tmp/recira-server.log
```

### Host Added but No Switches Show:
- **Cause**: Host has no OVS bridges created yet
- **Solution**: Create a bridge on the host:
  ```bash
  ssh root@HOST_IP 'ovs-vsctl add-br br0'
  ```
- Then re-add the host through the UI

### Duplicate Hosts:
- **Cause**: Added same host multiple times
- **Solution**: Restart server (hosts stored in memory)

### Wrong VXLAN IP Used for Tunnels:
- **Cause**: Host added before interface selection was implemented
- **Solution**:
  1. Restart server to clear hosts
  2. Re-add hosts using new interface selection workflow

### Network Created but Not Showing in UI:
- **Check backend**: `curl http://localhost:8080/api/networks`
- **Check tunnels**: `curl http://localhost:8080/api/tunnels`
- **Check logs**: `tail -100 /tmp/recira-server.log`

---

## Testing Commands

### Check Network on OVS Host:
```bash
ssh root@HOST_IP 'ovs-vsctl show'
ssh root@HOST_IP 'ovs-vsctl list-ports br0'
```

### Verify VXLAN Tunnel:
```bash
ssh root@HOST_IP 'ovs-vsctl list interface vxlan1009'
ssh root@HOST_IP 'ovs-appctl ofproto/list-tunnels'
```

### Check MTU:
```bash
ssh root@HOST_IP 'ip link show ens34'  # Replace ens34 with interface name
```

### Test Connectivity:
```bash
# On one host, add an internal port
ssh root@HOST1 'ovs-vsctl add-port br0 vnet0 -- set interface vnet0 type=internal'
ssh root@HOST1 'ip addr add 10.0.1.10/24 dev vnet0'
ssh root@HOST1 'ip link set vnet0 up'

# On another host
ssh root@HOST2 'ovs-vsctl add-port br0 vnet0 -- set interface vnet0 type=internal'
ssh root@HOST2 'ip addr add 10.0.1.20/24 dev vnet0'
ssh root@HOST2 'ip link set vnet0 up'

# Test ping
ssh root@HOST1 'ping 10.0.1.20'
```

---

## Known Issues and Limitations

1. **In-Memory Storage**: Hosts and tunnels are lost on server restart
2. **No Authentication**: Web UI has no login/authentication
3. **No SSL/TLS**: Server runs on HTTP only
4. **No Flow Management**: Cannot view/modify OpenFlow flows
5. **No Statistics**: No bandwidth/packet counters yet

---

## Future Enhancements (Roadmap)

- [ ] Persistent host/tunnel storage (SQLite or JSON files)
- [ ] Authentication and user management
- [ ] SSL/TLS support
- [ ] OpenFlow flow viewer/editor
- [ ] Traffic statistics and monitoring
- [ ] Automatic host discovery (scan subnet)
- [ ] Backup/restore configuration
- [ ] Multi-controller support
- [ ] REST API documentation (Swagger/OpenAPI)

---

## Quick Reference - SSH Credentials

**Current Hosts**:
- All hosts use: `root` / `Xm9909ona`
- Management Network: 192.168.88.0/24
- VXLAN Network: 10.172.88.0/24

---

## Session Status

**Last Updated**: 2025-11-25 06:00 UTC

### Investigation and Fixes Complete ✅

**User Issue**: "I created a network with vni 1009 and ip 10.0.1.0/24 with gateway 10.0.1.1 it completed without an error but it did not show up in the network list"

---

### Issue #1: Frontend Network Creation Failed (FIXED ✅)

**Root Cause**: Frontend JavaScript failed silently - POST request never sent to backend

**Evidence**:
- Server logs showed NO POST request to `/api/networks/create` from user's attempt
- Frontend JavaScript code appeared correct but needed better error handling

**Fix Applied** (`frontend/37734/index.html`):
- Added console logging to `createNetwork()` function for debugging
- Added null check for submit button selector
- Added error logging for fetch failures
- Now logs: "createNetwork() called", selected switches, request data, and response

**Result**: Frontend now has better debugging capability. User can check browser console (F12) to see if createNetwork() is being called and where it fails.

---

### Issue #2: Full-Mesh Tunnel Creation Partial Failure (FIXED ✅)

**Root Cause**: VXLAN port naming conflict - all tunnels with same VNI used same port name

**Problem Details**:
```
When creating full-mesh with VNI 1009:
- Tunnel 1: ovs-3 → ovs-02, creates port "vxlan1009" ✅
- Tunnel 2: ovs-3 → ovs-01, tries to create port "vxlan1009" ❌ (already exists!)
- Tunnel 3: ovs-02 → ovs-01, tries to create port "vxlan1009" ❌ (already exists!)
```

**Fix Applied** (`backend/vxlan_manager.py`):
```python
# OLD: Single port name per VNI
tunnel_name = f"vxlan{vni}"  # e.g., vxlan1009

# NEW: Unique port names including remote IP suffix
dst_ip_suffix = dst_vxlan_ip.split('.')[-1]
src_ip_suffix = src_vxlan_ip.split('.')[-1]
tunnel_name_src = f"vxlan{vni}_{dst_ip_suffix}"  # e.g., vxlan1009_233
tunnel_name_dst = f"vxlan{vni}_{src_ip_suffix}"  # e.g., vxlan1009_234
```

**Result**: Full-mesh now works correctly. Each tunnel gets unique port names based on remote endpoint.

**Test Results** (VNI 3000, 3 switches):
- ✅ All 3 tunnels created successfully
- ✅ Verified on actual OVS hosts:
  - ovs-3: vxlan3000_232, vxlan3000_233
  - ovs-02: vxlan3000_232, vxlan3000_234
  - ovs-01: vxlan3000_233, vxlan3000_234

---

### Summary of Changes

**Files Modified**:
1. `frontend/37734/index.html:618-620`
   - **CRITICAL FIX**: Removed event listener from DOMContentLoaded (timing issue)
   - Form didn't exist when listener tried to attach at page load
   - Error: `Uncaught TypeError: can't access property "addEventListener", document.getElementById(...) is null`

2. `frontend/37734/index.html:966-988`
   - **CRITICAL FIX**: Moved event listener to showCreateNetworkModal()
   - Ensures form exists in DOM when listener attaches (modal is open)
   - Added flag `networkFormListenerAttached` to prevent multiple attachments
   - Added console logging for debugging

3. `backend/vxlan_manager.py:55-102`
   - Changed tunnel naming to include remote IP suffix (vxlan{vni}_{remote_ip_suffix})
   - Updated tunnel_info to store both tunnel_name_src and tunnel_name_dst
   - Fixed delete_tunnel() for backward compatibility

**Version Update**: v0.6.0 → v0.6.1 (bug fixes)

---

### Testing Verification

**Frontend Fix - VERIFIED ✅**:
- User successfully created network via UI
- Form submission working correctly after browser refresh
- Network appeared in UI immediately
- No JavaScript errors

**Backend Fix - VERIFIED ✅**:
- **Test Network**: "ten-eight-network" (VNI 1002)
- **Switches**: ovs-3, ovs-02, ovs-01
- **Tunnels Created**: 3 of 3 ✅
- **Formula**: 3 switches × (3-1) / 2 = 3 tunnels

**Actual VXLAN Ports Created**:
- **ovs-3** (10.172.88.234): vxlan1002_232, vxlan1002_233
- **ovs-02** (10.172.88.233): vxlan1002_232, vxlan1002_234
- **ovs-01** (10.172.88.232): vxlan1002_233, vxlan1002_234

All unique port names - no conflicts! ✅

---

### What's Working Now

- ✅ Interface selection and dual-IP management
- ✅ Host add/provision with VXLAN interface selection
- ✅ Backend API endpoints fully functional
- ✅ VXLAN tunnels use correct 10.172.88.x IPs
- ✅ Network persistence to `/tmp/recira-networks.json`
- ✅ Full-mesh tunnel creation (FIXED!)
- ✅ Frontend error logging (IMPROVED!)

---

### Known Limitations

1. **Host Persistence**:
   - Remote hosts are currently stored in memory only
   - After server restart, hosts need to be re-added via UI
   - Networks and tunnels ARE persisted to `/tmp/recira-networks.json`
   - Future enhancement: Add host persistence to disk

2. **Network State Recovery**:
   - When server restarts, network metadata loads from disk
   - But VXLAN tunnels remain active on OVS hosts
   - Tunnel state in UI may not reflect actual OVS state after restart

---

*End of Session Continuity Document*
