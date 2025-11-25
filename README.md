# VXLAN Web Controller

**Open Source SDN Platform for VXLAN Overlay Networks**

Build and manage virtual overlay networks across multiple Linux hosts with a professional web interface. Repurposed from Citrix DVSC to work with any Open vSwitch deployment.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6+-green.svg)](https://python.org)
[![OVS](https://img.shields.io/badge/Open%20vSwitch-2.17+-orange.svg)](https://openvswitch.org)

## Features (v0.4)

- **OVS Discovery** - Auto-discover switches on local and remote Linux hosts
- **VXLAN Tunnels** - Create point-to-point VXLAN tunnels between switches
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
git clone https://github.com/yourusername/vxlan-web-controller.git
cd vxlan-web-controller
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
vxlan-web-controller/
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

### v0.4 - Interactive Management (CURRENT)
- [x] Web UI dashboard with real-time data
- [x] OVS switch discovery (localhost + SSH remotes)
- [x] VXLAN tunnel creation via UI
- [x] Tunnel deletion
- [x] Interactive modal forms
- [x] Real-time tunnel status

### Next: v0.5 - Network Abstraction
See [ROADMAP.md](docs/ROADMAP.md) for full development plan.

## API Documentation

### GET /api/status
Returns controller status and statistics.

**Response:**
```json
{
  "status": "running",
  "version": "0.4.0",
  "uptime": "2:15:30",
  "hosts": 3,
  "switches": 4
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

## License

Apache License 2.0

Original DVSC UI components: Copyright (C) Citrix Systems/Nicira
Repurposed controller: Copyright (C) 2025 VXLAN Web Controller Contributors

## Acknowledgments

- **Citrix/Nicira** - Original DVSC web UI
- **Open vSwitch** - The amazing virtual switch
- **Dojo Toolkit** - Professional UI framework
- **Claude Code** - 99.999% of the coding assistance

---

**Built by:** Carmine + Claude Code
**Started:** 2025-11-24
**Status:** v0.4 - Interactive Management Complete!
**Website:** (Coming soon)
**GitHub:** https://github.com/yourusername/vxlan-web-controller
