# Recira

**Open Source SDN Platform for VXLAN Overlay Networks**

*Reviving Nicira's vision for open networking*

Build and manage virtual overlay networks across multiple Linux hosts with a professional web interface. Recira repurposes the Citrix DVSC web UI to work with any Open vSwitch deployment.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6+-green.svg)](https://python.org)
[![OVS](https://img.shields.io/badge/Open%20vSwitch-2.17+-orange.svg)](https://openvswitch.org)

## Features (v0.7.0)

- **DHCP Integration (NEW!)** - Automatic IP assignment in overlay networks using dnsmasq
- **DHCP Leases Viewer** - View active DHCP leases from web UI
- **DHCP Reservations** - Map MAC addresses to static IPs
- **Host Auto-Provisioning** - Automatic OVS installation on Ubuntu/Debian/CentOS
- **Dual-Interface Support** - Separate management and VXLAN data plane networks
- **Interface Selection** - Choose VXLAN endpoint IP during host provisioning
- **OS Detection** - Auto-detect Linux distribution and version
- **MTU Optimization** - Configure 9000 MTU for VXLAN performance
- **Health Monitoring** - Real-time host health and OVS status checks
- **Virtual Networks** - Define named networks with auto-provisioned full-mesh tunnels
- **Full-Mesh Topology** - Automatic N×(N-1)/2 tunnel creation
- **OVS Discovery** - Auto-discover switches on local and remote Linux hosts
- **VXLAN Tunnels** - Automatic full-mesh or manual point-to-point tunnels
- **Network Abstraction** - Subnet/gateway config with VNI auto-allocation
- **Configuration Persistence** - Network and DHCP configs saved to JSON
- **Interactive UI** - Professional web interface (repurposed from Citrix DVSC)
- **Real-time Monitoring** - Live switch status, port counts, tunnel state
- **Multi-host Support** - Manage OVS across multiple hosts via SSH

## Quick Start

### Prerequisites

- Python 3.6+
- Linux hosts with Open vSwitch 2.x
- SSH access to managed hosts
- `sshpass` for remote host management

### Installation

```bash
git clone https://github.com/bufanoc/recira.git
cd recira
python3 backend/server.py
```

Open browser to: **http://localhost:8080**

### Add Remote Hosts

```bash
# Via API
curl -X POST http://localhost:8080/api/hosts/add \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.100", "username": "root", "password": "yourpassword"}'

# Or use the web UI "Add Host" button (coming in v0.6)
```

### Create VXLAN Tunnel

Via web UI:
1. Click "Create Tunnel" button
2. Select source and destination switches
3. Optionally specify VNI (or auto-assign)
4. Click "Create Tunnel"

Via API:
```bash
curl -X POST http://localhost:8080/api/tunnels/create \
  -H "Content-Type: application/json" \
  -d '{"src_switch_id": 1, "dst_switch_id": 2, "vni": 100}'
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                          │
│            (Professional Dojo Toolkit UI)               │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────┐
│              Python Backend Server                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ OVS Manager  │  │VXLAN Manager │  │ Host Manager │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         └──────────────────┴──────────────────┘          │
└────────────────────┬────────────────────────────────────┘
                     │ SSH / ovs-vsctl
┌────────────────────▼────────────────────────────────────┐
│              Open vSwitch (Multiple Hosts)              │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐      │
│  │  Host 1    │   │  Host 2    │   │  Host 3    │      │
│  │ ┌────────┐ │   │ ┌────────┐ │   │ ┌────────┐ │      │
│  │ │  br0   │◄┼───┼►│  br0   │◄┼───┼►│  br0   │ │      │
│  │ └────────┘ │   │ └────────┘ │   │ └────────┘ │      │
│  │  (VXLAN)   │   │  (VXLAN)   │   │  (VXLAN)   │      │
│  └────────────┘   └────────────┘   └────────────┘      │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
recira/
├── backend/
│   ├── server.py              # Main HTTP server & API router
│   ├── ovs_manager.py         # OVS discovery & management
│   ├── vxlan_manager.py       # VXLAN tunnel operations
│   ├── host_provisioner.py    # Host auto-provisioning (v0.6)
│   ├── network_manager.py     # Virtual network abstraction (v0.5)
│   └── dhcp_manager.py        # Overlay DHCP services (v0.7)
├── frontend/37734/            # Web UI (from DVSC)
│   ├── index.html             # Custom dashboard
│   ├── dojo/                  # Dojo Toolkit framework
│   └── nox/ext/apps/vmanui/   # Original DVSC UI components
├── docs/
│   └── ROADMAP.md             # Development roadmap
├── .gitignore
└── README.md                  # This file
```

## Current Status

### v0.7.0 - DHCP Integration (CURRENT - 2025-11-25)
- [x] **DHCP Manager**: New backend module for dnsmasq management
- [x] **Enable/Disable**: Per-network DHCP enable/disable from web UI
- [x] **Host Selection**: Choose which host runs DHCP server
- [x] **DHCP Config**: IP range, lease time, DNS servers
- [x] **Leases Viewer**: View active DHCP leases in web UI
- [x] **Reservations**: MAC to IP static mappings via API
- [x] **Auto-Install**: dnsmasq installed automatically if missing
- [x] **Gateway Port**: OVS internal port created for DHCP server

### v0.6.1 - Bug Fixes (COMPLETE)
- [x] Fixed network creation form event listener timing issue
- [x] Fixed VXLAN port naming conflicts in full-mesh topology
- [x] Unique tunnel names: `vxlan{vni}_{remote_ip_suffix}`

### v0.6 - Host Auto-Provisioning (COMPLETE)
- [x] OS detection (Ubuntu/Debian/CentOS/RHEL)
- [x] Automatic OVS installation based on OS
- [x] MTU 9000 configuration for VXLAN optimization
- [x] OVS performance optimizations
- [x] Host health monitoring API
- [x] Auto-provisioning API endpoint
- [x] Dual-interface support with VXLAN IP selection

### v0.5 - Network Abstraction Layer (COMPLETE)
- [x] Network creation with name, VNI, subnet, gateway
- [x] Automatic full-mesh tunnel provisioning
- [x] Configuration persistence (JSON)
- [x] Network management API (create/read/delete)
- [x] VNI auto-allocation (prevents conflicts)
- [x] Per-network switch membership tracking

### v0.4 - Interactive Management (COMPLETE)
- [x] Web UI dashboard with real-time data
- [x] OVS switch discovery (localhost + SSH remotes)
- [x] VXLAN tunnel creation via UI
- [x] Tunnel deletion
- [x] Interactive modal forms
- [x] Real-time tunnel status

### Next: v0.8 - Port Management
See [ROADMAP.md](docs/ROADMAP.md) for full development plan.

## API Documentation

### GET /api/status
Returns controller status and statistics.

**Response:**
```json
{
  "status": "running",
  "version": "0.6.0",
  "uptime": "2:15:30",
  "controller": "Recira - Virtual Network Platform",
  "hosts": 3,
  "switches": 4,
  "networks": 2
}
```

### POST /api/hosts/provision
Auto-provision a host with OVS installation and configuration.

**Request:**
```json
{
  "ip": "192.168.1.100",
  "username": "root",
  "password": "yourpassword",
  "configure_mtu": true,
  "optimize": true
}
```

Notes:
- Automatically detects OS (Ubuntu/Debian/CentOS/RHEL)
- Installs OVS based on detected OS
- Configures MTU to 9000 for VXLAN optimization
- Applies OVS performance optimizations
- This operation may take 5-10 minutes

**Response:**
```json
{
  "success": true,
  "message": "Host 192.168.1.100 provisioned successfully",
  "provision_details": {
    "os_type": "ubuntu",
    "os_version": "22.04",
    "ovs_installed": true,
    "ovs_version": "2.17.9",
    "mtu_configured": true,
    "optimizations_applied": true
  },
  "host": {
    "id": 2,
    "hostname": "ovs-host-02",
    "ip": "192.168.1.100",
    "ovs_version": "2.17.9"
  }
}
```

### GET /api/hosts/health
Get health status of a specific host.

**Query Parameters:**
- `ip` (required): Host IP address
- `username` (optional): SSH username (default: root)
- `password` (optional): SSH password

**Example:**
```
GET /api/hosts/health?ip=192.168.1.100&username=root&password=secret
```

**Response:**
```json
{
  "health": {
    "timestamp": "2025-11-24T22:30:00",
    "ip": "192.168.1.100",
    "reachable": true,
    "ovs_installed": true,
    "ovs_running": true,
    "ovs_version": "2.17.9",
    "os_type": "ubuntu",
    "os_version": "22.04",
    "uptime": "up 3 days",
    "load_average": "0.15, 0.10, 0.05"
  }
}
```

### GET /api/networks
List all virtual networks.

**Response:**
```json
{
  "networks": [
    {
      "id": 1,
      "name": "Production",
      "vni": 1000,
      "subnet": "10.0.1.0/24",
      "gateway": "10.0.1.1",
      "switches": [1, 2, 3],
      "switch_names": ["s1", "s2", "s3"],
      "tunnel_count": 3,
      "created_at": "2025-11-24T22:03:25.203823"
    }
  ]
}
```

### POST /api/networks/create
Create virtual network with automatic full-mesh tunnels.

**Request:**
```json
{
  "name": "Production",
  "switches": [1, 2, 3],
  "subnet": "10.0.1.0/24",
  "gateway": "10.0.1.1",
  "vni": 1000
}
```

Notes:
- `name`: Required - Human-readable network name
- `switches`: Required - List of switch IDs (minimum 2)
- `subnet`: Optional - Network subnet in CIDR notation
- `gateway`: Optional - Gateway IP address
- `vni`: Optional - Auto-allocated if not specified

**Response:**
```json
{
  "success": true,
  "message": "Network 'Production' created successfully",
  "network": {
    "id": 1,
    "name": "Production",
    "vni": 1000,
    "subnet": "10.0.1.0/24",
    "gateway": "10.0.1.1",
    "switches": [1, 2, 3],
    "tunnels": [1, 2, 3]
  }
}
```

### POST /api/networks/delete
Delete virtual network and all associated tunnels.

**Request:**
```json
{
  "network_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Network deleted successfully"
}
```

### GET /api/switches
List all discovered OVS switches.

**Response:**
```json
{
  "switches": [
    {
      "id": 1,
      "name": "br0",
      "dpid": 50791130291780,
      "hostname": "ovs-01",
      "host_ip": "192.168.88.194",
      "ports": 3,
      "connected": false
    }
  ]
}
```

### POST /api/tunnels/create
Create VXLAN tunnel between two switches.

**Request:**
```json
{
  "src_switch_id": 1,
  "dst_switch_id": 2,
  "vni": 100
}
```

**Response:**
```json
{
  "success": true,
  "message": "Tunnel created successfully",
  "tunnel": {
    "id": 1,
    "vni": 100,
    "src_switch_name": "br0",
    "dst_switch_name": "br0",
    "status": "up"
  }
}
```

### POST /api/tunnels/delete
Delete existing VXLAN tunnel.

**Request:**
```json
{
  "tunnel_id": 1
}
```

See full API documentation at: http://localhost:8080/api/ (coming in v1.3)

## Development Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed plan.

**High-level Milestones:**
- **v0.5** - Network Abstraction Layer
- **v0.6** - Host Auto-Provisioning
- **v0.7** - DHCP Integration
- **v0.8** - Port Management
- **v0.9** - Visual Topology
- **v1.0** - OpenFlow Management
- **v1.1** - Statistics & Monitoring
- **v1.2** - KVM Integration
- **v1.3+** - Production Hardening

## Contributing

This is currently a personal project built with Claude Code assistance. Contributions welcome!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Testing

### Manual Testing
```bash
# Start server
python3 backend/server.py

# Test API
curl http://localhost:8080/api/status

# Add remote host
python3 backend/add_remote_host.py

# Create tunnel
curl -X POST http://localhost:8080/api/tunnels/create \
  -H "Content-Type: application/json" \
  -d '{"src_switch_id": 3, "dst_switch_id": 4, "vni": 100}'
```

### Unit Tests (Coming in v1.3)
```bash
python3 -m pytest tests/
```

## Troubleshooting

**Port 8080 already in use:**
```bash
lsof -ti:8080 | xargs kill -9
python3 backend/server.py
```

**Can't SSH to remote hosts:**
- Ensure `sshpass` is installed: `apt-get install sshpass`
- Verify SSH credentials
- Check firewall rules on remote hosts

**VXLAN tunnels not working:**
- Verify MTU settings (recommend 9000 for underlay network)
- Check VXLAN endpoint IPs are reachable
- Ensure VNI matches on both ends

## Attribution

Recira repurposes the web UI components from **Citrix DVSC** (Distributed Virtual Switch Controller), originally developed by **Nicira Networks** (acquired by VMware, now part of Broadcom).

### Original Work
- **DVSC Web UI**: Copyright (C) Citrix Systems, Inc. / Nicira Networks
- **Original Authors**: Nicira engineering team
- **Technology**: Dojo Toolkit 1.8, NOX Controller framework

### This Project
- **Backend Controller**: Copyright (C) 2025 Recira Contributors (Original work)
- **Repurposed UI**: Used for educational and open-source purposes
- **License**: Apache 2.0

The web UI components (`frontend/37734/`) are extracted from an end-of-life product and repurposed for modern open-source SDN management. This project honors Nicira's pioneering work in software-defined networking.

**Note**: If you represent Citrix, Broadcom, or VMware and have concerns about this use, please open an issue to discuss.

## License

Apache License 2.0

**Recira Backend & Modifications**: Copyright (C) 2025 Recira Contributors
**Original DVSC UI Components**: Copyright (C) Citrix Systems, Inc.

## Acknowledgments

- **Citrix/Nicira** - Original DVSC web UI
- **Open vSwitch** - The amazing virtual switch
- **Dojo Toolkit** - Professional UI framework
- **Claude Code** - 99.999% of the coding assistance

---

**Built by:** Carmine Bufano (bufanoc) + Claude Code
**Started:** 2025-11-24
**Status:** v0.7.0 - DHCP Integration Complete!
**Last Updated:** 2025-11-25
**Website:** (Coming soon)
**GitHub:** https://github.com/bufanoc/recira
