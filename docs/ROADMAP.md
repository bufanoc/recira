# Recira - Development Roadmap

**Vision:** Build a complete, production-ready SDN platform for managing VXLAN overlay networks across multiple Linux hosts.

*Reviving Nicira's vision for open networking*

**Approach:** Progressive development - each phase builds logically on the previous, avoiding "cart before horse" scenarios.

---

## Completed Versions

### v0.1 - Foundation ✅ (Nov 24, 2025)
**Extracted DVSC web UI and created minimal backend**

- Extracted 27MB DVSC web UI (1,905 JS files)
- Basic Python HTTP server
- Mock API endpoints
- Git repository initialized

### v0.2 - Real Data ✅ (Nov 24, 2025)
**Connected to actual OVS switches**

- `ovs_manager.py` - OVS discovery module
- Localhost switch discovery
- Remote host discovery via SSH
- Real-time switch status
- Switch listing API

### v0.3 - VXLAN Tunnels ✅ (Nov 24, 2025)
**Created VXLAN tunnel capability**

- `vxlan_manager.py` - Tunnel management
- Point-to-point VXLAN tunnel creation
- Bidirectional tunnel setup
- VNI auto-assignment
- Tunnel listing API
- Tested with 0% packet loss

### v0.4 - Interactive Management ✅ (Nov 24, 2025)
**Added web UI tunnel management**

- Interactive "Create Tunnel" modal
- Tunnel deletion via UI
- Enhanced tunnel table display
- Form validation
- Real-time UI updates
- DELETE /api/tunnels/delete endpoint

---

## Planned Development (4 Weeks)

### Week 1: Network Foundation

#### v0.5 - Network Abstraction Layer (Days 1-2)
**Goal:** Define virtual networks, not just tunnels

**Why This Order:** Must have network concept before DHCP or port management

**Features:**
- Create "Networks" with name, VNI, subnet, gateway
  - Example: "Production Network" = VNI 200, 10.200.0.0/16, GW 10.200.0.1
- Networks automatically create full-mesh tunnels between selected switches
- Network CRUD operations
- Configuration persistence (JSON storage)
- Network health monitoring

**Backend Changes:**
```
backend/
  ├── network_manager.py         # NEW - Network abstraction
  ├── server.py                  # Add /api/networks endpoints
  └── storage/
      └── networks.json          # NEW - Network configs
```

**API Endpoints:**
- `POST /api/networks` - Create network
- `GET /api/networks` - List networks
- `GET /api/networks/{id}` - Get network details
- `PUT /api/networks/{id}` - Update network
- `DELETE /api/networks/{id}` - Delete network (and all tunnels)

**Frontend Changes:**
- "Create Network" modal (name, VNI, subnet, gateway, switch selection)
- Networks table with status
- Network details view showing all tunnels

**Testing:**
- Create network with 3 switches
- Verify full-mesh tunnels created automatically
- Delete network, verify cleanup

---

#### v0.6 - Host Management & Auto-Provisioning (Days 3-5)
**Goal:** Add and provision hosts from web UI

**Why This Order:** Needed before DHCP (DHCP server must run on a host)

**Features:**
- "Add Host" UI button with modal form
- Auto-detect OS (Ubuntu/Debian/CentOS/RHEL/Fedora)
- Auto-install OVS based on detected OS
- Configure network interfaces (MTU 9000)
- Host health monitoring (ping, SSH reachability)
- Host provisioning status tracking
- Remove/deprovision hosts

**Backend Changes:**
```
backend/
  ├── host_provisioner.py        # NEW - OS detection & OVS installation
  ├── server.py                  # Add /api/hosts/provision endpoint
  └── templates/
      ├── ubuntu_ovs_install.sh  # NEW - Ubuntu install script
      ├── centos_ovs_install.sh  # NEW - CentOS install script
      └── network_config.j2      # NEW - Network config template
```

**API Endpoints:**
- `POST /api/hosts/provision` - Auto-provision OVS on host
- `GET /api/hosts/{id}/status` - Get provision status
- `GET /api/hosts/{id}/health` - Health check
- `DELETE /api/hosts/{id}` - Remove host

**Host Provisioning Steps:**
1. SSH to host with provided credentials
2. Detect OS: `cat /etc/os-release`
3. Install OVS based on OS:
   - Ubuntu/Debian: `apt-get install openvswitch-switch`
   - CentOS/RHEL: `yum install openvswitch`
4. Configure MTU on target interfaces
5. Start OVS service
6. Discover bridges
7. Mark host as "ready"

**Frontend Changes:**
- Enhanced "Add Host" modal:
  - IP address
  - Credentials (username/password or SSH key)
  - Auto-provision toggle
  - Target network interface for VXLAN
- Hosts table with status:
  - Provisioning (yellow)
  - Ready (green)
  - Error (red)
  - Offline (gray)
- Provision log viewer (real-time tail)

**Testing:**
- Add fresh Ubuntu host, verify OVS installed
- Add fresh CentOS host, verify OVS installed
- Test with host that already has OVS (should skip installation)
- Remove host, verify cleanup

---

### Week 2: Overlay Services

#### v0.7 - DHCP Server Integration (Days 1-3)
**Goal:** Automatic IP assignment in overlay networks

**Why This Order:** Requires networks (v0.5) and provisioned hosts (v0.6)

**Features:**
- Enable DHCP per network
- Select which host runs DHCP server
- Configure DHCP scope (range, lease time, DNS)
- Auto-configure dnsmasq on selected host
- View active DHCP leases
- DNS forwarding for overlay network
- DHCP reservations (MAC → IP)

**Backend Changes:**
```
backend/
  ├── dhcp_manager.py            # NEW - dnsmasq management
  ├── server.py                  # Add DHCP endpoints
  └── templates/
      └── dnsmasq.conf.j2        # NEW - dnsmasq config template
```

**API Endpoints:**
- `POST /api/networks/{id}/dhcp/enable` - Enable DHCP on network
- `PUT /api/networks/{id}/dhcp/config` - Update DHCP config
- `GET /api/networks/{id}/dhcp/leases` - View leases
- `POST /api/networks/{id}/dhcp/reservation` - Create MAC reservation
- `DELETE /api/networks/{id}/dhcp` - Disable DHCP

**DHCP Setup Process:**
1. Select host to run DHCP server
2. Create OVS internal port on that host's bridge
3. Assign network gateway IP to internal port
4. Install dnsmasq if not present
5. Generate dnsmasq config:
   - Listen on internal port
   - DHCP range within subnet
   - DNS upstream servers
6. Start dnsmasq service
7. Monitor for lease activity

**Example Config Generated:**
```
# /etc/dnsmasq.d/vxlan-network-100.conf
interface=vxlan100-gw
dhcp-range=10.100.0.10,10.100.0.250,255.255.255.0,24h
dhcp-option=option:router,10.100.0.1
dhcp-option=option:dns-server,8.8.8.8,8.8.4.4
dhcp-leasefile=/var/lib/misc/dnsmasq-vxlan100.leases
```

**Frontend Changes:**
- "Enable DHCP" toggle in network details
- DHCP configuration form:
  - Server host selection
  - Start IP
  - End IP
  - Lease time
  - DNS servers
- Active leases table (MAC, IP, hostname, expiry)
- "Add Reservation" button

**Testing:**
- Create network VNI 100, subnet 10.100.0.0/24
- Enable DHCP, select VM1 as server
- Connect test VM to network
- Verify test VM gets IP via DHCP
- Check leases table in UI

---

#### v0.8 - Port Management (Days 4-5)
**Goal:** Connect endpoints to overlay networks

**Why This Order:** Needs networks + DHCP to be functional

**Features:**
- List all ports on all switches
- View port statistics (RX/TX bytes, packets, errors)
- Assign ports to networks (tag with VNI)
- Trunk mode (multiple VNIs on one port)
- Port access mode (single VNI, untagged)
- Port status monitoring
- Link state detection

**Backend Changes:**
```
backend/
  ├── ovs_manager.py             # ENHANCE - Add port operations
  ├── server.py                  # Add port endpoints
  └── port_monitor.py            # NEW - Background port monitoring
```

**API Endpoints:**
- `GET /api/ports` - List all ports across all switches
- `GET /api/switches/{id}/ports` - Ports on specific switch
- `PUT /api/ports/{id}/tag` - Assign port to network
- `PUT /api/ports/{id}/trunk` - Configure trunk mode
- `GET /api/ports/{id}/stats` - Port statistics

**Port Operations:**
```bash
# Tag port eth1 with VNI 100 (access mode)
ovs-vsctl set port eth1 tag=100

# Trunk port eth2 with VNIs 100,200,300
ovs-vsctl set port eth2 trunks=100,200,300

# Get port stats
ovs-ofctl dump-ports br0 eth1
```

**Frontend Changes:**
- New "Ports" page
- Ports table:
  - Switch name
  - Port name
  - Network (VNI)
  - Mode (access/trunk)
  - Status (up/down)
  - RX/TX statistics
- "Configure Port" modal:
  - Select network
  - Access vs. trunk mode
  - VLAN IDs for trunk

**Testing:**
- Connect VM interface to br0
- Assign to network VNI 100
- Verify VM gets DHCP IP
- Test connectivity to other VMs on same network
- Test trunk mode with multiple networks

---

### Week 3: Visualization & Management

#### v0.9 - Visual Topology (Days 1-3)
**Goal:** Interactive network diagram

**Why This Order:** Foundation is solid, now improve UX

**Features:**
- D3.js force-directed graph visualization
- Node types:
  - Hosts (servers with OVS)
  - Switches (OVS bridges)
  - Networks (overlay networks)
  - VMs (endpoints)
- Link types:
  - Physical connections
  - VXLAN tunnels (with VNI label)
  - Network membership
- Interactive features:
  - Drag nodes to reposition
  - Click node for details panel
  - Zoom/pan
  - Filter by network
  - Highlight path between nodes
- Real-time updates (tunnels up/down)
- Export topology as PNG/SVG

**Frontend Changes:**
```
frontend/37734/
  ├── topology.html              # NEW - Topology page
  ├── js/
  │   ├── d3.v7.min.js          # NEW - D3.js library
  │   └── topology-graph.js      # NEW - Graph rendering logic
  └── css/
      └── topology.css           # NEW - Topology styles
```

**Backend Changes:**
- `GET /api/topology/graph` - Returns D3-compatible node/edge data

**Graph Data Format:**
```json
{
  "nodes": [
    {"id": "host-1", "type": "host", "label": "carmine", "x": 100, "y": 100},
    {"id": "switch-1", "type": "switch", "label": "br0", "parent": "host-1"},
    {"id": "network-100", "type": "network", "label": "Prod (VNI 100)"}
  ],
  "links": [
    {"source": "switch-1", "target": "switch-2", "type": "vxlan", "vni": 100},
    {"source": "port-1", "target": "network-100", "type": "member"}
  ]
}
```

**Testing:**
- Create 3-host, 2-network topology
- Verify all nodes render correctly
- Test drag-and-drop
- Create tunnel, verify link appears in real-time
- Test filtering by network

---

#### v1.0 - OpenFlow Management (Days 4-5)
**Goal:** Flow rule management

**Why This Order:** Advanced feature after core networking works

**Features:**
- View flows on switches (`ovs-ofctl dump-flows`)
- Flow statistics (packet/byte counts)
- Add simple flows via UI
- Delete flows
- Flow templates (common patterns)
- Flow priority management
- Flow aging/timeouts

**Backend Changes:**
```
backend/
  ├── flow_manager.py            # NEW - OpenFlow operations
  ├── server.py                  # Add flow endpoints
  └── templates/
      └── flow_templates.json    # NEW - Common flow patterns
```

**API Endpoints:**
- `GET /api/switches/{id}/flows` - List flows
- `POST /api/switches/{id}/flows` - Add flow
- `DELETE /api/switches/{id}/flows/{id}` - Delete flow
- `GET /api/flows/templates` - Get flow templates

**Flow Templates:**
- Forward all traffic port A → port B
- Drop traffic from MAC address
- Mirror traffic to monitoring port
- Rate limit traffic
- VLAN translation

**Frontend Changes:**
- "Flows" tab on switch details
- Flows table with match/action/stats
- "Add Flow" modal:
  - Template selection
  - Match fields (in_port, dl_src, dl_dst, dl_vlan)
  - Actions (output, drop, modify_vlan)
  - Priority
- Flow statistics graphs

**Testing:**
- Add flow: "Forward port 1 → port 2"
- Generate traffic, verify flow stats increment
- Delete flow, verify traffic stops
- Test flow priority (higher priority wins)

---

### Week 4: Operations & Extensions

#### v1.1 - Statistics & Monitoring (Days 1-2)
**Goal:** Observability and alerting

**Features:**
- Traffic graphs (real-time and historical)
- Tunnel health checks (periodic VXLAN ping)
- Switch connectivity monitoring
- DHCP server status monitoring
- Event log (tunnel created/deleted, host added, flow installed)
- Alerts/notifications
- Performance metrics dashboard
- Export statistics (CSV/JSON)

**Backend Changes:**
```
backend/
  ├── monitoring.py              # NEW - Background monitoring
  ├── stats_collector.py         # NEW - Time-series data collection
  ├── alerting.py                # NEW - Alert engine
  └── storage/
      ├── stats.db               # NEW - SQLite for time-series
      └── events.log             # NEW - Event log
```

**Monitoring Features:**
- Every 30 seconds:
  - Poll switch statistics
  - Check tunnel reachability (ping through VXLAN)
  - Verify DHCP server responding
  - Check host SSH connectivity
- Store time-series data (last 7 days)
- Detect anomalies:
  - Tunnel packet loss > 1%
  - DHCP server down
  - Host unreachable
- Generate events for UI

**Frontend Changes:**
- Dashboard widgets:
  - Traffic graph (bytes/sec over time)
  - Active tunnels count
  - Health status (green/yellow/red)
- Events log table (timestamp, type, message)
- Alerts panel (critical issues)
- "Export Stats" button

**Testing:**
- Monitor traffic through tunnel
- Simulate tunnel failure (shut down interface)
- Verify alert generated
- Check event log shows failure and recovery

---

#### v1.2 - KVM Integration (Days 3-5)
**Goal:** Manage VMs and connect to networks

**Why Last:** Most complex, requires all networking to work first

**Features:**
- Detect KVM/libvirt on hosts
- List VMs on each host (running/stopped)
- VM details (vCPUs, RAM, disks, network interfaces)
- Create VM network interfaces
- Attach VM interfaces to OVS bridges
- Assign VMs to networks (auto-tag with VNI)
- VM power management (start/stop/reboot)
- VM console access (VNC link)
- VM creation wizard (basic)

**Backend Changes:**
```
backend/
  ├── vm_manager.py              # NEW - libvirt wrapper
  ├── server.py                  # Add VM endpoints
  └── templates/
      └── vm_interface.xml       # NEW - libvirt interface XML
```

**Prerequisites on Hosts:**
- Install: `apt-get install qemu-kvm libvirt-daemon-system libvirt-clients`
- Enable: `systemctl enable --now libvirtd`

**API Endpoints:**
- `GET /api/hosts/{id}/vms` - List VMs on host
- `GET /api/vms/{id}` - VM details
- `POST /api/vms/{id}/attach-network` - Attach VM to network
- `POST /api/vms/{id}/power` - Start/stop/reboot VM
- `POST /api/vms/create` - Create new VM

**VM Network Attachment:**
1. Get VM's libvirt XML
2. Add new interface:
   ```xml
   <interface type='bridge'>
     <source bridge='br0'/>
     <virtualport type='openvswitch'/>
     <vlan>
       <tag id='100'/>  <!-- VNI -->
     </vlan>
   </interface>
   ```
3. Attach interface to VM
4. VM gets DHCP IP on network

**Frontend Changes:**
- "Virtual Machines" page
- VMs table:
  - Host
  - Name
  - State (running/stopped)
  - vCPUs
  - Memory
  - Networks
- "Attach to Network" modal
- VM details panel with console link

**Testing:**
- Create test VM on ovs-01
- Attach to Production network (VNI 100)
- Verify VM gets DHCP IP (10.100.0.x)
- Ping from VM to other network members
- Stop VM, verify DHCP lease released

---

### v1.3+ - Production Hardening (Ongoing)

**Authentication & Security:**
- JWT token-based authentication
- Login page
- Session management
- Password hashing (bcrypt)
- HTTPS/TLS support
- Certificate management

**RBAC (Role-Based Access Control):**
- User roles: Admin, Operator, Viewer
- Admin: Full access
- Operator: Create networks, attach VMs (no delete)
- Viewer: Read-only

**Configuration Management:**
- Backup entire configuration (networks, hosts, tunnels)
- Restore from backup
- Export/import JSON
- Configuration versioning
- Rollback capability

**API Documentation:**
- Swagger/OpenAPI spec
- Interactive API docs at /api/docs
- Code examples for each endpoint
- Postman collection

**Testing & Quality:**
- Unit tests (pytest)
- Integration tests
- Load testing
- CI/CD pipeline (GitHub Actions)
- Code coverage reports

**Operational Features:**
- Systemd service unit
- Log rotation
- Graceful shutdown
- Health check endpoint
- Metrics export (Prometheus format)

---

## Development Principles

1. **Progressive Enhancement** - Each version builds on previous
2. **Test as You Go** - Verify each feature works before moving on
3. **Documentation First** - Update docs before writing code
4. **API Stability** - Don't break existing endpoints
5. **User Feedback** - Test UI/UX at each milestone

## Success Criteria

Each version is complete when:
- [ ] All planned features implemented
- [ ] Manual testing passed
- [ ] README updated
- [ ] Git commit with release tag
- [ ] Working demo available

## Timeline Summary

- **Week 1** (v0.5-v0.6): Network abstraction + host provisioning
- **Week 2** (v0.7-v0.8): DHCP + port management
- **Week 3** (v0.9-v1.0): Visualization + OpenFlow
- **Week 4** (v1.1-v1.2): Monitoring + KVM
- **Ongoing** (v1.3+): Production hardening

**Total Estimated Time:** 4-5 weeks full-time development

---

**Last Updated:** 2025-11-24
**Current Version:** v0.4
**Next Milestone:** v0.5 (Network Abstraction Layer)
