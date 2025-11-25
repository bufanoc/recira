# Recira Installation Guide

**Version:** 0.6.1
**Last Updated:** 2025-11-25

This guide provides step-by-step instructions for installing and configuring Recira.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Install (One-Line)](#quick-install-one-line)
3. [Manual Installation](#manual-installation)
4. [Post-Installation Setup](#post-installation-setup)
5. [Multi-Host Setup](#multi-host-setup)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Controller Host (Where Recira Runs)

**Operating System:**
- Ubuntu 20.04+ / Debian 11+
- CentOS 7+ / RHEL 7+
- Any Linux with Python 3.6+

**Software:**
- Python 3.6 or higher
- Git
- SSH client
- `sshpass` (for remote host management)

**Network:**
- Port 8080 available (HTTP server)
- SSH access to managed hosts (port 22)

**Resources:**
- Minimum: 512MB RAM, 1 CPU core
- Recommended: 1GB RAM, 2 CPU cores

### Managed OVS Hosts

**Operating System:**
- Ubuntu 20.04+ / Debian 11+
- CentOS 7+ / RHEL 7+

**Software:**
- Open vSwitch 2.x (auto-installed by Recira)
- SSH server with root access

**Network Requirements:**
- **Management Network**: For SSH access (e.g., 192.168.88.0/24)
- **VXLAN Network** (recommended): Dedicated network for VXLAN tunnels with MTU 9000 (e.g., 10.172.88.0/24)
  - *Note*: Dual-interface setup recommended for production
- UDP port 4789 open for VXLAN traffic

**Resources (per host):**
- Minimum: 2GB RAM, 2 CPU cores
- Recommended: 4GB+ RAM, 4+ CPU cores

---

## Quick Install (One-Line)

**Coming in v0.7!**

```bash
# Future one-line installer (not yet available)
curl -sSL https://raw.githubusercontent.com/bufanoc/recira/master/install.sh | bash
```

For now, use the [Manual Installation](#manual-installation) method below.

---

## Manual Installation

### Step 1: Install Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-pip sshpass
```

**CentOS/RHEL:**
```bash
sudo yum install -y git python3 python3-pip sshpass epel-release
```

### Step 2: Clone Repository

```bash
git clone https://github.com/bufanoc/recira.git
cd recira
```

### Step 3: Verify Installation

```bash
# Check Python version (must be 3.6+)
python3 --version

# Verify repository structure
ls -la backend/ frontend/
```

### Step 4: Start Recira Server

```bash
# Start server (foreground)
python3 backend/server.py

# Or run in background
nohup python3 backend/server.py > /tmp/recira.log 2>&1 &
```

### Step 5: Access Web Interface

Open your browser to:
- **Local**: http://localhost:8080
- **Remote**: http://<SERVER_IP>:8080

You should see the Recira dashboard with localhost already discovered.

---

## Post-Installation Setup

### Option 1: Add Hosts with Existing OVS

If your hosts already have Open vSwitch installed:

1. Click **"Add Host"** button in the UI
2. Enter host details:
   - **IP Address**: Management network IP
   - **Username**: root (or sudo user)
   - **Password**: SSH password
3. Click **"Add Host"**

The host will be discovered and its OVS bridges will appear in the UI.

### Option 2: Auto-Provision New Hosts

To automatically install OVS on a fresh Linux host:

1. Click **"Provision Host"** button in the UI
2. Enter host details:
   - **IP Address**: Management network IP
   - **Username**: root
   - **Password**: SSH password
   - **VXLAN IP** (optional): IP for VXLAN tunnel endpoints
3. Enable options:
   - ✅ **Configure MTU 9000** (recommended for performance)
   - ✅ **Apply Optimizations** (recommended)
4. Click **"Provision Host"**

This will:
- Detect OS (Ubuntu/Debian/CentOS)
- Install Open vSwitch
- Create default bridge (br0)
- Configure MTU 9000 on VXLAN interface
- Apply OVS performance optimizations

**Note**: Provisioning takes 5-10 minutes depending on internet speed.

---

## Multi-Host Setup

### Recommended Network Architecture

For production deployments, use a dual-interface setup:

```
┌─────────────────────────────────────────────────────┐
│  Controller Host (192.168.88.164)                   │
│  - Runs Recira server                               │
│  - Web UI on port 8080                              │
└─────────────────────────────────────────────────────┘
                      │
                      │ SSH Management
                      │
       ┌──────────────┴──────────────┬────────────────┐
       │                             │                 │
┌──────▼─────────┐           ┌──────▼─────────┐  ┌───▼───────────┐
│  OVS Host 1    │           │  OVS Host 2    │  │  OVS Host 3   │
│                │           │                │  │               │
│ Management:    │           │ Management:    │  │ Management:   │
│ 192.168.88.194 │           │ 192.168.88.195 │  │ 192.168.88.197│
│                │           │                │  │               │
│ VXLAN:         │◄─────────►│ VXLAN:         │◄►│ VXLAN:        │
│ 10.172.88.232  │  MTU 9000 │ 10.172.88.233  │  │ 10.172.88.234 │
│ (ens34)        │           │ (ens34)        │  │ (ens34)       │
└────────────────┘           └────────────────┘  └───────────────┘
```

### Network Setup Steps

1. **Configure VXLAN Network** (on each OVS host):
```bash
# Example for ens34 interface
ip addr add 10.172.88.X/24 dev ens34
ip link set ens34 mtu 9000
ip link set ens34 up
```

2. **Make Configuration Persistent**:
```bash
# Ubuntu/Debian: /etc/netplan/01-netcfg.yaml
network:
  version: 2
  ethernets:
    ens34:
      addresses:
        - 10.172.88.232/24
      mtu: 9000

# Apply
netplan apply
```

3. **Add Hosts to Recira**:
   - Use "Provision Host" button
   - Specify VXLAN IP when prompted (e.g., 10.172.88.232)
   - Recira will use management IP for SSH, VXLAN IP for tunnels

---

## Verification

### Check Controller Status

```bash
# Via API
curl http://localhost:8080/api/status

# Expected output:
{
  "status": "running",
  "version": "0.6.1",
  "hosts": 3,
  "switches": 3,
  "networks": 0
}
```

### Create Test Network

1. Click **"Create Network"** in the UI
2. Fill in details:
   - **Name**: Test Network
   - **Switches**: Select all available switches
   - **Subnet**: 10.0.1.0/24
   - **Gateway**: 10.0.1.1
3. Click **"Create Network"**

Expected result:
- Network appears in "Networks" section
- **Tunnels Created**: 3 (for 3 switches)
- Full-mesh topology: N×(N-1)/2 tunnels

### Verify VXLAN Tunnels

```bash
# On each OVS host
ssh root@<HOST_IP> 'ovs-vsctl show'

# Expected: VXLAN interfaces like vxlan1000_232, vxlan1000_233
```

### Test Connectivity

```bash
# Check tunnel reachability
ssh root@<HOST_IP> 'ovs-vsctl list Interface | grep -A 10 vxlan'

# Verify tunnel status (should show local/remote IPs)
```

---

## Troubleshooting

### Server Won't Start

**Error: Port 8080 already in use**
```bash
# Find and kill process
lsof -ti:8080 | xargs kill -9

# Restart server
python3 backend/server.py
```

### Can't SSH to Remote Hosts

**Check sshpass installation:**
```bash
# Ubuntu/Debian
sudo apt-get install sshpass

# CentOS/RHEL
sudo yum install sshpass
```

**Test SSH access manually:**
```bash
ssh root@<HOST_IP>
# Should connect without errors
```

**Firewall blocking SSH:**
```bash
# On remote host, allow SSH
sudo ufw allow 22
```

### OVS Provisioning Fails

**Check OS support:**
- Supported: Ubuntu 20.04+, Debian 11+, CentOS 7+
- Unsupported: May require manual OVS installation

**Check internet connectivity:**
```bash
# On remote host
curl -I google.com
# Should return HTTP 200
```

**View detailed logs:**
```bash
# Check provision API response in browser DevTools
# Or check server console output
```

### VXLAN Tunnels Not Working

**Check MTU on VXLAN interface:**
```bash
ip link show ens34  # Should show mtu 9000
```

**Verify UDP port 4789 is open:**
```bash
# On OVS host
sudo netstat -ulnp | grep 4789
```

**Check VXLAN endpoint IPs are reachable:**
```bash
ping 10.172.88.232  # Should work from other VXLAN hosts
```

**Verify tunnel configuration:**
```bash
ssh root@<HOST_IP> 'ovs-vsctl list Interface' | grep -A 5 vxlan
# Check remote_ip and key (VNI) settings
```

### Networks Not Showing in UI

**Hard refresh browser:**
```
Ctrl+F5 (Windows/Linux)
Cmd+Shift+R (Mac)
```

**Check browser console for errors:**
```
F12 → Console tab
# Look for JavaScript errors
```

**Verify API is working:**
```bash
curl http://localhost:8080/api/networks
# Should return JSON with networks array
```

### Hosts Disappear After Server Restart

**Known Limitation (v0.6.1):**
- Remote hosts are stored in memory only
- After server restart, re-add hosts via UI
- Networks and tunnels ARE persisted
- **Fix coming in v0.7**: Host persistence to disk

---

## Next Steps

After successful installation:

1. **Create your first network**: Follow the "Create Test Network" steps above
2. **Explore the API**: See [README.md](README.md#api-documentation)
3. **Add more hosts**: Scale to multi-host overlay networks
4. **Read the roadmap**: See [docs/ROADMAP.md](docs/ROADMAP.md)

---

## Getting Help

- **Documentation**: See [README.md](README.md)
- **Issues**: https://github.com/bufanoc/recira/issues
- **Session Continuity**: See [SESSION_CONTINUITY.md](SESSION_CONTINUITY.md) for development history

---

**Happy SDN Networking!** 🚀
