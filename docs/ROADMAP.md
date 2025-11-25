# Recira - Development Roadmap

**Vision:** Build a complete, production-ready SDN platform for managing VXLAN overlay networks across multiple hosts.

*Reviving Nicira's vision for open networking*

**Approach:** Progressive development - each phase builds logically on the previous, avoiding "cart before horse" scenarios.

---

## Completed Versions

### v0.1 - Foundation (Nov 24, 2025)
**Extracted DVSC web UI and created minimal backend**

- Extracted 27MB DVSC web UI (1,905 JS files)
- Basic Python HTTP server
- Mock API endpoints
- Git repository initialized

### v0.2 - Real Data (Nov 24, 2025)
**Connected to actual OVS switches**

- `ovs_manager.py` - OVS discovery module
- Localhost switch discovery
- Remote host discovery via SSH
- Real-time switch status
- Switch listing API

### v0.3 - VXLAN Tunnels (Nov 24, 2025)
**Created VXLAN tunnel capability**

- `vxlan_manager.py` - Tunnel management
- Point-to-point VXLAN tunnel creation
- Bidirectional tunnel setup
- VNI auto-assignment
- Tunnel listing API
- Tested with 0% packet loss

### v0.4 - Interactive Management (Nov 24, 2025)
**Added web UI tunnel management**

- Interactive "Create Tunnel" modal
- Tunnel deletion via UI
- Enhanced tunnel table display
- Form validation
- Real-time UI updates
- DELETE /api/tunnels/delete endpoint

### v0.5 - Network Abstraction Layer (Nov 24, 2025)
**Define virtual networks with full-mesh topology**

- `network_manager.py` - Network management module
- Create "Networks" with name, VNI, subnet, gateway
- Networks automatically create full-mesh tunnels
- Network CRUD operations
- Configuration persistence (JSON storage)
- VNI auto-allocation

### v0.6 - Host Auto-Provisioning (Nov 24, 2025)
**Add and provision hosts from web UI**

- `host_provisioner.py` - OS detection & OVS installation
- "Add Host" and "Provision Host" UI modals
- Auto-detect OS (Ubuntu/Debian/CentOS/RHEL)
- Auto-install OVS based on detected OS
- Dual-interface support (management + VXLAN networks)
- Interface selection for VXLAN endpoint IP
- MTU 9000 configuration for VXLAN optimization
- Host health monitoring API

### v0.7.0 - DHCP Integration (Nov 25, 2025)
**Automatic IP assignment in overlay networks**

- `dhcp_manager.py` - dnsmasq management module
- Enable/disable DHCP per network via web UI
- Select which host runs DHCP server
- Configure DHCP scope (range, lease time, DNS)
- Auto-configure dnsmasq on selected host
- View active DHCP leases
- DHCP reservations (MAC -> IP)
- OVS internal port for gateway

### v0.7.1 - Host Persistence (Nov 25, 2025)
**Hosts survive server restarts**

- Hosts saved to `/tmp/recira-hosts.json`
- Auto-reconnect to saved hosts on startup
- Credentials stored with hosts (cleartext - lab use only)
- DHCP uses stored credentials automatically
- API responses filter out passwords
- Security warning added to README

### v0.7.2 - Visual Topology + Tunnel Discovery (Nov 25, 2025)
**Stunning D3.js network visualization** (Originally planned for v0.9!)

- D3.js force-directed graph visualization
- Real-time topology showing hosts, switches, tunnels
- Animated gradient lines for VXLAN tunnels
- Color-coded by VNI with vibrant palette
- Interactive: drag nodes, zoom, pan
- Hover tooltips with details
- Live statistics display
- Tunnel discovery on startup (survives restarts)

### v0.7.3 - Host Management + Bug Fixes (Nov 25, 2025)
**Host lifecycle management and critical fixes**

- Host Detach: Remove from active management, preserve data for re-attach
- Host Forget: Permanently delete all host data
- Host Re-attach: Reconnect previously detached hosts
- New Managed Hosts table with full details and actions
- Detached Hosts section for pending re-attachment
- Fixed VXLAN tunnel deletion (was using switch_id as host_id)
- Fixed DHCP gateway port VNI tagging

---

## Current Version: v0.7.3

**Status**: Fully Functional
**Server**: http://192.168.88.164:8080
**GitHub**: https://github.com/bufanoc/recira

---

## Planned Development

### v0.8 - Port Management
**Goal:** Connect endpoints to overlay networks

**Features:**
- List all ports on all switches
- View port statistics (RX/TX bytes, packets, errors)
- Assign ports to networks (tag with VNI)
- Trunk mode (multiple VNIs on one port)
- Port access mode (single VNI, untagged)
- Port status monitoring
- Link state detection

**API Endpoints:**
- `GET /api/ports` - List all ports across all switches
- `GET /api/switches/{id}/ports` - Ports on specific switch
- `PUT /api/ports/{id}/tag` - Assign port to network
- `PUT /api/ports/{id}/trunk` - Configure trunk mode
- `GET /api/ports/{id}/stats` - Port statistics

---

### v1.0 - OpenFlow Management
**Goal:** Flow rule management

**Features:**
- View flows on switches (`ovs-ofctl dump-flows`)
- Flow statistics (packet/byte counts)
- Add simple flows via UI
- Delete flows
- Flow templates (common patterns)
- Flow priority management

---

### v1.1 - Statistics & Monitoring
**Goal:** Observability and alerting

**Features:**
- Traffic graphs (real-time and historical)
- Tunnel health checks (periodic VXLAN ping)
- Switch connectivity monitoring
- DHCP server status monitoring
- Event log (tunnel created/deleted, host added)
- Alerts/notifications
- Performance metrics dashboard
- Export statistics (CSV/JSON)

---

### v1.2 - KVM Integration
**Goal:** Manage VMs and connect to networks

**Features:**
- Detect KVM/libvirt on hosts
- List VMs on each host (running/stopped)
- VM details (vCPUs, RAM, disks, network interfaces)
- Attach VM interfaces to OVS bridges
- Assign VMs to networks (auto-tag with VNI)
- VM power management (start/stop/reboot)
- VM console access (VNC link)

---

### v1.3 - Windows Host Support (Future)
**Goal:** Support Windows Server hosts with OVS

**Challenges:**
- Windows OVS is older (2.10.0 vs 2.17.9 on Linux)
- Requires WinRM or OpenSSH for remote management
- OVS runs as Hyper-V extension on Windows
- Different command paths and service management

**Approach:**
- Require manual OVS pre-installation on Windows
- Detect Windows hosts via SSH (PowerShell detection)
- Use Windows-compatible OVS commands
- Test VXLAN interoperability with Linux hosts

**Supported Windows Versions (via Cloudbase OVS):**
- Windows Server 2016
- Windows Server 2019
- Windows Server 2022/2025 (untested, may work)

---

### v1.4+ - Production Hardening (Ongoing)

**Authentication & Security:**
- JWT token-based authentication
- Login page with session management
- Password hashing (bcrypt)
- HTTPS/TLS support
- Encrypted credential storage (vault integration)

**RBAC (Role-Based Access Control):**
- User roles: Admin, Operator, Viewer
- Permission management

**Configuration Management:**
- Backup/restore entire configuration
- Export/import JSON
- Configuration versioning
- Rollback capability

**API Documentation:**
- Swagger/OpenAPI spec
- Interactive API docs at /api/docs

**Testing & Quality:**
- Unit tests (pytest)
- Integration tests
- CI/CD pipeline (GitHub Actions)

**Operational Features:**
- Systemd service unit
- Log rotation
- Graceful shutdown
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
- [x] All planned features implemented
- [x] Manual testing passed
- [x] README updated
- [x] Git commit with release tag
- [x] Working demo available

---

## Quick Summary

| Version | Feature | Status |
|---------|---------|--------|
| v0.1 | Foundation | Complete |
| v0.2 | Real Data | Complete |
| v0.3 | VXLAN Tunnels | Complete |
| v0.4 | Interactive UI | Complete |
| v0.5 | Network Abstraction | Complete |
| v0.6 | Host Provisioning | Complete |
| v0.7.0 | DHCP Integration | Complete |
| v0.7.1 | Host Persistence | Complete |
| v0.7.2 | Visual Topology | Complete |
| v0.7.3 | Host Management | Complete |
| v0.8 | Port Management | **Next** |
| v1.0 | OpenFlow | Planned |
| v1.1 | Monitoring | Planned |
| v1.2 | KVM Integration | Planned |
| v1.3 | Windows Support | Future |
| v1.4+ | Production Hardening | Future |

---

**Last Updated:** 2025-11-25
**Current Version:** v0.7.3
**Next Milestone:** v0.8 (Port Management)
