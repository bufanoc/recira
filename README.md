# VXLAN Web Controller

**Generic OpenFlow/VXLAN SDN Controller with Professional Web UI**

Repurposed from Citrix DVSC to work with any Linux host running Open vSwitch.

## 🎯 What This Does

- Manage Open vSwitch bridges on any Linux host
- Create VXLAN tunnels between hosts
- Visualize network topology
- Monitor flows and statistics
- All through a beautiful web interface!

## 🚀 Quick Start

### Prerequisites

- Python 3.6+ (you have 3.10 ✅)
- Linux hosts with Open vSwitch installed
- SSH access to hosts

### Run the Controller (v0.1 - Mock Data)

```bash
cd /root/vxlan-web-controller
python3 backend/server.py
```

Then open your browser to: **http://192.168.88.164:8080**

## 📋 Current Status

**v0.1 - Foundation** (DONE! ✅)
- [x] Web UI extracted from DVSC (27MB, 1,905 JS files)
- [x] Minimal Python backend serving UI
- [x] Mock API endpoints (fake data for testing UI)
- [x] Server running and accessible

**v0.2 - Real Data** (Next!)
- [ ] Connect to actual OVS hosts via SSH
- [ ] Discover switches and bridges
- [ ] Real-time switch status
- [ ] Flow table viewing

**v0.3 - VXLAN Management** (After that!)
- [ ] Create VXLAN tunnels from UI
- [ ] Delete tunnels
- [ ] Monitor tunnel status
- [ ] Packet statistics

## 🏗️ Architecture

```
┌──────────────────────┐
│   Web Browser        │  ← You see the beautiful UI here
│  (Dojo Toolkit UI)   │
└──────────┬───────────┘
           │ HTTP/JSON
┌──────────▼───────────┐
│  Python Backend      │  ← Simple HTTP server (for now)
│  (backend/server.py) │
└──────────┬───────────┘
           │ (Future: SSH, OVSDB, OpenFlow)
┌──────────▼───────────┐
│  OVS on Linux Hosts  │  ← Your actual switches
└──────────────────────┘
```

## 📂 Project Structure

```
vxlan-web-controller/
├── backend/
│   └── server.py          ← Python web server (mock APIs)
├── frontend/              ← DVSC web UI (27MB)
│   └── 37734/
│       ├── dojo/          ← Dojo Toolkit framework
│       └── nox/ext/apps/
│           └── vmanui/    ← Main UI application
├── docs/                  ← Documentation (future)
├── tests/                 ← Tests (future)
└── README.md              ← This file
```

## 🧪 Testing the UI

1. **Start the server:**
   ```bash
   python3 backend/server.py
   ```

2. **Open browser to:** http://192.168.88.164:8080

3. **What you'll see:**
   - Dashboard with mock switches
   - Network topology with fake data
   - It won't actually DO anything yet - just shows the UI works!

4. **Test API endpoints:**
   ```bash
   curl http://localhost:8080/api/status
   curl http://localhost:8080/api/switches
   curl http://localhost:8080/api/topology
   ```

## 📝 Next Steps (We'll Do Together!)

### Week 1: Real Switch Discovery
- Write `ovs_manager.py` to SSH into Linux hosts
- Discover OVS bridges automatically
- Show real switches in UI

### Week 2: VXLAN Tunnel Creation
- Write `vxlan_manager.py` to create tunnels
- Add "Create Tunnel" button to UI
- Test ping between hosts over VXLAN

### Week 3: Flow Management
- Install flow rules from UI
- View active flows
- Monitor statistics

## 🤝 How We Work

**Me (Claude):**
- Write 100% of the code
- Provide every command you need
- Debug every error

**You:**
- Run commands I give you
- Report: "It worked!" or "Error: ..."
- Test features and tell me what you see

## 🎓 Learning Resources

- **Open vSwitch**: https://www.openvswitch.org/
- **VXLAN**: https://en.wikipedia.org/wiki/Virtual_Extensible_LAN
- **Dojo Toolkit**: https://dojotoolkit.org/

## 📜 License

Original DVSC code: Citrix/Nicira
Repurposed version: (We should decide - probably Apache 2.0 or MIT)

## 🐛 Troubleshooting

**UI doesn't load:**
- Check: `python3 backend/server.py` is running
- Check: Port 8080 not blocked by firewall
- Try: `curl http://localhost:8080` - should return HTML

**Can't access from another machine:**
- Server binds to 0.0.0.0 (all interfaces)
- Check firewall: `sudo ufw allow 8080`

**API returns errors:**
- Currently all APIs return mock data - this is expected!
- Real APIs will come in v0.2

---

**Built by:** You + Claude Code
**Started:** 2025-11-24
**Status:** v0.1 - Foundation Complete! 🎉
