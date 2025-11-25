#!/usr/bin/env python3
"""
VXLAN Web Controller - Backend Server with Real OVS Discovery
Repurposed from DVSC for generic OVS/VXLAN management

Version: 0.7.2 - Tunnel Discovery + Host Persistence + DHCP Integration
"""

import http.server
import socketserver
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from ovs_manager import ovs_manager
import vxlan_manager as vxlan_mgr
import network_manager as net_mgr
import host_provisioner as host_prov
import dhcp_manager as dhcp_mgr

PORT = 8080
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend/37734')

# Server start time for uptime calculation
SERVER_START_TIME = datetime.now()

# Initialize managers
vxlan_manager = None
network_manager = None
dhcp_manager = None

class VXLANRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for VXLAN Web Controller"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # API endpoints
        if path.startswith('/api/'):
            self.handle_api_request(path, parsed_path.query)
        # Redirect root to main UI
        elif path == '/':
            self.send_response(302)
            self.send_header('Location', '/index.html')
            self.end_headers()
        # Serve static files
        else:
            super().do_GET()

    def do_POST(self):
        """Handle POST requests for API"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path.startswith('/api/'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
            except:
                data = {}
            self.handle_api_request(path, data=data)
        else:
            self.send_error(404, "Not Found")

    def handle_api_request(self, path, query=None, data=None):
        """Handle API requests with real OVS data"""

        if path == '/api/status':
            # Real status with actual uptime
            uptime = datetime.now() - SERVER_START_TIME
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds

            response = {
                "status": "running",
                "version": "0.7.2",
                "uptime": uptime_str,
                "controller": "Recira - Virtual Network Platform",
                "hosts": len(ovs_manager.get_all_hosts()),
                "switches": len(ovs_manager.get_all_switches()),
                "networks": len(network_manager.get_all_networks()) if network_manager else 0,
                "dhcp_enabled": len(dhcp_manager.get_all_dhcp_configs()) if dhcp_manager else 0
            }

        elif path == '/api/switches':
            # Real switch data from OVS
            switches = ovs_manager.get_all_switches()

            # Add mock 'flows' field for now (will implement flow counting later)
            for switch in switches:
                switch['flows'] = 0  # Placeholder
                switch['host'] = switch['host_ip']  # Add for compatibility

            response = {"switches": switches}

        elif path == '/api/hosts':
            # Real host data
            hosts = ovs_manager.get_all_hosts()

            # Format bridge names for display (make copies to avoid modifying original)
            formatted_hosts = []
            for host in hosts:
                host_copy = {
                    'id': host['id'],
                    'hostname': host['hostname'],
                    'ip': host['ip'],
                    'type': host.get('type', 'unknown'),
                    'status': host.get('status', 'unknown'),
                    'ovs_version': host.get('ovs_version', 'unknown'),
                    'bridges': [br['name'] for br in host.get('bridges', [])]
                }
                formatted_hosts.append(host_copy)

            response = {"hosts": formatted_hosts}

        elif path == '/api/hosts/detached':
            # Get detached hosts that can be re-attached
            detached = ovs_manager.get_detached_hosts()
            response = {"detached_hosts": detached}

        elif path == '/api/topology':
            # Build topology from real switches (no links yet)
            switches = ovs_manager.get_all_switches()
            nodes = []

            for switch in switches:
                nodes.append({
                    "id": switch['id'],
                    "type": "switch",
                    "name": f"{switch['name']}@{switch['hostname']}",
                    "dpid": switch['dpid']
                })

            response = {
                "nodes": nodes,
                "links": []  # Will implement VXLAN link discovery in v0.3
            }

        elif path == '/api/tunnels':
            # Get all VXLAN tunnels
            if vxlan_manager:
                tunnels = vxlan_manager.get_all_tunnels()
                response = {"tunnels": tunnels}
            else:
                response = {"tunnels": []}

        elif path == '/api/networks':
            # Get all virtual networks with DHCP status
            if network_manager:
                networks = network_manager.get_all_networks()
                # Add DHCP status to each network
                if dhcp_manager:
                    for net in networks:
                        dhcp_config = dhcp_manager.get_dhcp_config(net['id'])
                        if dhcp_config:
                            net['dhcp_enabled'] = True
                            net['dhcp_host'] = dhcp_config.get('host_ip')
                            net['dhcp_range'] = f"{dhcp_config.get('dhcp_start')} - {dhcp_config.get('dhcp_end')}"
                        else:
                            net['dhcp_enabled'] = False
                response = {"networks": networks}
            else:
                response = {"networks": []}

        elif path == '/api/networks/create' and data:
            # Create a virtual network
            name = data.get('name')
            switches = data.get('switches', [])  # List of switch IDs
            vni = data.get('vni')  # Optional
            subnet = data.get('subnet', '')
            gateway = data.get('gateway', '')

            if not name:
                response = {"error": "Missing required field: name"}
            elif not switches or len(switches) < 2:
                response = {"error": "Network requires at least 2 switches"}
            elif not network_manager:
                response = {"error": "Network manager not initialized"}
            else:
                network = network_manager.create_network(
                    name=name,
                    switches=switches,
                    vni=int(vni) if vni else None,
                    subnet=subnet,
                    gateway=gateway
                )

                if network:
                    response = {
                        "success": True,
                        "message": f"Network '{name}' created successfully",
                        "network": network.to_dict()
                    }
                else:
                    response = {
                        "success": False,
                        "error": "Failed to create network"
                    }

        elif path == '/api/networks/delete' and data:
            # Delete a virtual network
            network_id = data.get('network_id')

            if not network_id:
                response = {"error": "Missing required field: network_id"}
            elif not network_manager:
                response = {"error": "Network manager not initialized"}
            else:
                # Also disable DHCP if enabled
                if dhcp_manager and dhcp_manager.get_dhcp_config(int(network_id)):
                    dhcp_manager.disable_dhcp(int(network_id))

                success = network_manager.delete_network(int(network_id))

                if success:
                    response = {
                        "success": True,
                        "message": "Network deleted successfully"
                    }
                else:
                    response = {
                        "success": False,
                        "error": "Failed to delete network (network not found?)"
                    }

        # ============ DHCP API Endpoints (v0.7) ============

        elif path == '/api/dhcp/enable' and data:
            # Enable DHCP for a network
            network_id = data.get('network_id')
            host_ip = data.get('host_ip')
            dhcp_start = data.get('dhcp_start')
            dhcp_end = data.get('dhcp_end')
            username = data.get('username')
            password = data.get('password')
            dns_servers = data.get('dns_servers')
            lease_time = data.get('lease_time', '24h')

            if not network_id or not host_ip or not dhcp_start or not dhcp_end:
                response = {"error": "Missing required fields: network_id, host_ip, dhcp_start, dhcp_end"}
            elif not dhcp_manager:
                response = {"error": "DHCP manager not initialized"}
            else:
                result = dhcp_manager.enable_dhcp(
                    network_id=int(network_id),
                    host_ip=host_ip,
                    dhcp_start=dhcp_start,
                    dhcp_end=dhcp_end,
                    username=username,
                    password=password,
                    dns_servers=dns_servers,
                    lease_time=lease_time
                )
                response = result

        elif path == '/api/dhcp/disable' and data:
            # Disable DHCP for a network
            network_id = data.get('network_id')
            username = data.get('username')
            password = data.get('password')

            if not network_id:
                response = {"error": "Missing required field: network_id"}
            elif not dhcp_manager:
                response = {"error": "DHCP manager not initialized"}
            else:
                result = dhcp_manager.disable_dhcp(
                    network_id=int(network_id),
                    username=username,
                    password=password
                )
                response = result

        elif path == '/api/dhcp/config' and query:
            # Get DHCP configuration for a network (GET request)
            params = parse_qs(query) if isinstance(query, str) else query
            network_id = params.get('network_id', [None])[0] if isinstance(query, str) else query.get('network_id')

            if not network_id:
                response = {"error": "Missing required parameter: network_id"}
            elif not dhcp_manager:
                response = {"error": "DHCP manager not initialized"}
            else:
                config = dhcp_manager.get_dhcp_config(int(network_id))
                if config:
                    response = {"success": True, "dhcp_config": config}
                else:
                    response = {"success": False, "message": "DHCP not enabled for this network"}

        elif path == '/api/dhcp/leases' and query:
            # Get DHCP leases for a network (GET request)
            params = parse_qs(query) if isinstance(query, str) else query
            network_id = params.get('network_id', [None])[0] if isinstance(query, str) else query.get('network_id')
            username = params.get('username', [None])[0] if isinstance(query, str) else query.get('username')
            password = params.get('password', [None])[0] if isinstance(query, str) else query.get('password')

            if not network_id:
                response = {"error": "Missing required parameter: network_id"}
            elif not dhcp_manager:
                response = {"error": "DHCP manager not initialized"}
            else:
                result = dhcp_manager.get_dhcp_leases(
                    network_id=int(network_id),
                    username=username,
                    password=password
                )
                response = result

        elif path == '/api/dhcp/reservation' and data:
            # Add DHCP reservation (POST request)
            network_id = data.get('network_id')
            mac = data.get('mac')
            ip = data.get('ip')
            hostname = data.get('hostname', '')
            username = data.get('username')
            password = data.get('password')

            if not network_id or not mac or not ip:
                response = {"error": "Missing required fields: network_id, mac, ip"}
            elif not dhcp_manager:
                response = {"error": "DHCP manager not initialized"}
            else:
                result = dhcp_manager.add_reservation(
                    network_id=int(network_id),
                    mac=mac,
                    ip=ip,
                    hostname=hostname,
                    username=username,
                    password=password
                )
                response = result

        elif path == '/api/dhcp/reservation/delete' and data:
            # Delete DHCP reservation (POST request)
            network_id = data.get('network_id')
            mac = data.get('mac')
            username = data.get('username')
            password = data.get('password')

            if not network_id or not mac:
                response = {"error": "Missing required fields: network_id, mac"}
            elif not dhcp_manager:
                response = {"error": "DHCP manager not initialized"}
            else:
                result = dhcp_manager.delete_reservation(
                    network_id=int(network_id),
                    mac=mac,
                    username=username,
                    password=password
                )
                response = result

        # ============ End DHCP API Endpoints ============

        elif path == '/api/hosts/add' and data:
            # Add a remote host
            ip = data.get('ip')
            username = data.get('username', 'root')
            password = data.get('password')
            vxlan_ip = data.get('vxlan_ip')  # Optional VXLAN IP

            if not ip or not password:
                response = {"error": "Missing required fields: ip, password"}
            else:
                host_info = ovs_manager.discover_remote_host(
                    ip=ip,
                    username=username,
                    password=password,
                    vxlan_ip=vxlan_ip
                )

                if host_info:
                    # Filter out password from response
                    safe_host_info = {k: v for k, v in host_info.items() if k != 'ssh_password'}
                    response = {
                        "success": True,
                        "message": f"Successfully added {host_info['hostname']}",
                        "host": safe_host_info
                    }
                else:
                    response = {
                        "success": False,
                        "error": f"Failed to connect to {ip}"
                    }

        elif path == '/api/hosts/provision' and data:
            # Auto-provision a host with OVS installation
            ip = data.get('ip')
            username = data.get('username', 'root')
            password = data.get('password')
            vxlan_interface = data.get('vxlan_interface')
            vxlan_ip = data.get('vxlan_ip')
            configure_mtu = data.get('configure_mtu', True)
            optimize = data.get('optimize', True)

            if not ip or not password:
                response = {"error": "Missing required fields: ip, password"}
            else:
                # Run provisioning (this may take several minutes)
                provision_result = host_prov.provision_new_host(
                    ip=ip,
                    username=username,
                    password=password,
                    vxlan_interface=vxlan_interface,
                    configure_mtu=configure_mtu,
                    optimize=optimize
                )

                if provision_result['success']:
                    # After provisioning, discover the host to add it to OVS manager
                    host_info = ovs_manager.discover_remote_host(
                        ip=ip,
                        username=username,
                        password=password,
                        vxlan_ip=vxlan_ip
                    )

                    # Filter out password from response
                    safe_host_info = {k: v for k, v in host_info.items() if k != 'ssh_password'} if host_info else None
                    response = {
                        "success": True,
                        "message": f"Host {ip} provisioned successfully",
                        "provision_details": provision_result,
                        "host": safe_host_info
                    }
                else:
                    response = {
                        "success": False,
                        "error": "Provisioning failed",
                        "details": provision_result
                    }

        elif path == '/api/hosts/health' and query:
            # Get health status of a specific host
            params = parse_qs(query) if isinstance(query, str) else query
            ip = params.get('ip', [None])[0] if isinstance(query, str) else query.get('ip')
            username = params.get('username', ['root'])[0] if isinstance(query, str) else query.get('username', 'root')
            password = params.get('password', [None])[0] if isinstance(query, str) else query.get('password')

            if not ip:
                response = {"error": "Missing required parameter: ip"}
            else:
                health_status = host_prov.get_host_status(
                    ip=ip,
                    username=username,
                    password=password
                )
                response = {"health": health_status}

        elif path == '/api/hosts/scan-interfaces' and query:
            # Scan network interfaces on a host
            params = parse_qs(query) if isinstance(query, str) else query
            ip = params.get('ip', [None])[0] if isinstance(query, str) else query.get('ip')
            username = params.get('username', ['root'])[0] if isinstance(query, str) else query.get('username', 'root')
            password = params.get('password', [None])[0] if isinstance(query, str) else query.get('password')

            if not ip:
                response = {"error": "Missing required parameter: ip"}
            else:
                scan_result = host_prov.scan_host_interfaces(
                    ip=ip,
                    username=username,
                    password=password
                )
                response = scan_result

        elif path == '/api/hosts/remove' and data:
            # Remove a host (detach or forget)
            host_id = data.get('host_id')
            keep_data = data.get('keep_data', False)  # True = detach, False = forget

            if not host_id:
                response = {"error": "Missing required field: host_id"}
            else:
                result = ovs_manager.remove_host(int(host_id), keep_data=keep_data)
                response = result

        elif path == '/api/hosts/reattach' and data:
            # Re-attach a previously detached host
            host_id = data.get('host_id')

            if not host_id:
                response = {"error": "Missing required field: host_id"}
            else:
                result = ovs_manager.reattach_host(int(host_id))
                response = result

        elif path == '/api/tunnels/create' and data:
            # Create a VXLAN tunnel
            src_switch_id = data.get('src_switch_id')
            dst_switch_id = data.get('dst_switch_id')
            vni = data.get('vni')  # Optional

            if not src_switch_id or not dst_switch_id:
                response = {"error": "Missing required fields: src_switch_id, dst_switch_id"}
            elif not vxlan_manager:
                response = {"error": "VXLAN manager not initialized"}
            else:
                tunnel_info = vxlan_manager.create_tunnel(
                    src_switch_id=int(src_switch_id),
                    dst_switch_id=int(dst_switch_id),
                    vni=int(vni) if vni else None
                )

                if tunnel_info:
                    response = {
                        "success": True,
                        "message": f"Tunnel created successfully",
                        "tunnel": tunnel_info
                    }
                else:
                    response = {
                        "success": False,
                        "error": "Failed to create tunnel"
                    }

        elif path == '/api/tunnels/delete' and data:
            # Delete a VXLAN tunnel
            tunnel_id = data.get('tunnel_id')

            if not tunnel_id:
                response = {"error": "Missing required field: tunnel_id"}
            elif not vxlan_manager:
                response = {"error": "VXLAN manager not initialized"}
            else:
                success = vxlan_manager.delete_tunnel(int(tunnel_id))

                if success:
                    response = {
                        "success": True,
                        "message": "Tunnel deleted successfully"
                    }
                else:
                    response = {
                        "success": False,
                        "error": "Failed to delete tunnel (tunnel not found?)"
                    }

        else:
            response = {"error": "Unknown API endpoint", "path": path}

        # Send JSON response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))

    def log_message(self, format, *args):
        """Custom log format"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {self.address_string()} - {format % args}")


def main():
    """Start the web server"""
    global vxlan_manager, network_manager, dhcp_manager

    print("\n" + "="*60)
    print("🚀 Recira - Virtual Network Platform v0.7.1")
    print("="*60)
    print(f"\n📁 Frontend directory: {FRONTEND_DIR}")

    # Discover localhost OVS
    print("\n🔍 Discovering OVS bridges on localhost...")
    host_info = ovs_manager.discover_localhost()

    if host_info:
        print(f"   ✅ Found host: {host_info['hostname']} ({host_info['ip']})")
        print(f"   ✅ OVS version: {host_info['ovs_version']}")
        print(f"   ✅ Bridges: {len(host_info['bridges'])}")
        for bridge in host_info['bridges']:
            print(f"      - {bridge['name']} (DPID: {bridge['dpid']}, {bridge['ports']} ports)")
    else:
        print("   ⚠️  Warning: Could not discover OVS on localhost")
        print("   ⚠️  Server will start but show no switches")

    # Initialize VXLAN manager
    print("\n🔗 Initializing VXLAN tunnel manager...")
    vxlan_manager = vxlan_mgr.initialize(ovs_manager)
    vxlan_manager.discover_tunnels()
    print("   ✅ VXLAN manager ready")

    # Initialize Network manager
    print("\n🌐 Initializing virtual network manager...")
    network_manager = net_mgr.initialize(ovs_manager, vxlan_manager)
    print("   ✅ Network manager ready")

    # Initialize DHCP manager
    print("\n🖧 Initializing DHCP manager...")
    dhcp_manager = dhcp_mgr.initialize(ovs_manager, network_manager)
    print("   ✅ DHCP manager ready")

    print(f"\n🌐 Server starting on port {PORT}...")
    print(f"\n✨ Open your browser to: http://localhost:{PORT}")
    print(f"   (or http://192.168.88.164:{PORT} from other machines)")
    print("\n" + "="*60)
    print("API Endpoints (v0.7.3 - Host Management!):")
    print("  GET  /api/status              - Controller status")
    print("  GET  /api/switches            - Connected switches")
    print("  GET  /api/hosts               - OVS hosts")
    print("  GET  /api/hosts/detached      - Detached hosts (can re-attach)")
    print("  POST /api/hosts/add           - Add remote host")
    print("  POST /api/hosts/provision     - Auto-provision host with OVS")
    print("  POST /api/hosts/remove        - Remove host (detach or forget)")
    print("  POST /api/hosts/reattach      - Re-attach detached host")
    print("  GET  /api/hosts/health        - Get host health status")
    print("  GET  /api/networks            - Virtual networks (with DHCP status)")
    print("  POST /api/networks/create     - Create network with full-mesh")
    print("  POST /api/networks/delete     - Delete network and tunnels")
    print("  GET  /api/tunnels             - VXLAN tunnels")
    print("  POST /api/tunnels/create      - Create VXLAN tunnel")
    print("  POST /api/tunnels/delete      - Delete VXLAN tunnel")
    print("  GET  /api/topology            - Network topology")
    print("  --- DHCP Endpoints ---")
    print("  POST /api/dhcp/enable         - Enable DHCP for network")
    print("  POST /api/dhcp/disable        - Disable DHCP for network")
    print("  GET  /api/dhcp/config         - Get DHCP configuration")
    print("  GET  /api/dhcp/leases         - View active DHCP leases")
    print("  POST /api/dhcp/reservation    - Add DHCP reservation")
    print("  POST /api/dhcp/reservation/delete - Delete reservation")
    print("="*60 + "\n")

    # Allow port reuse to avoid "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), VXLANRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped by user")
            httpd.shutdown()


if __name__ == "__main__":
    main()
