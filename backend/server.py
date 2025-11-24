#!/usr/bin/env python3
"""
VXLAN Web Controller - Minimal Backend Server
Repurposed from DVSC for generic OVS/VXLAN management

This is v0.1 - Just serves the UI and provides mock API
"""

import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime

PORT = 8080
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend/37734')

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
        """Handle API requests with mock data"""

        # Mock API responses - we'll implement these properly later
        if path == '/api/status':
            response = {
                "status": "running",
                "version": "0.1.0",
                "uptime": "5 minutes",
                "controller": "VXLAN Web Controller"
            }

        elif path == '/api/switches':
            # Mock switch data
            response = {
                "switches": [
                    {
                        "dpid": 1,
                        "name": "br0",
                        "host": "192.168.1.100",
                        "hostname": "host1",
                        "connected": True,
                        "ports": 2,
                        "flows": 5
                    },
                    {
                        "dpid": 2,
                        "name": "br0",
                        "host": "192.168.1.101",
                        "hostname": "host2",
                        "connected": True,
                        "ports": 2,
                        "flows": 5
                    }
                ]
            }

        elif path == '/api/topology':
            # Mock topology data
            response = {
                "nodes": [
                    {"id": 1, "type": "switch", "name": "br0@host1", "dpid": 1},
                    {"id": 2, "type": "switch", "name": "br0@host2", "dpid": 2}
                ],
                "links": [
                    {"source": 1, "target": 2, "type": "vxlan", "vni": 100}
                ]
            }

        elif path == '/api/tunnels':
            # Mock VXLAN tunnel data
            response = {
                "tunnels": [
                    {
                        "id": 1,
                        "src_switch": 1,
                        "dst_switch": 2,
                        "vni": 100,
                        "status": "up",
                        "tx_packets": 1250,
                        "rx_packets": 1180
                    }
                ]
            }

        elif path == '/api/hosts':
            # Mock host data
            response = {
                "hosts": [
                    {
                        "id": 1,
                        "hostname": "host1",
                        "ip": "192.168.1.100",
                        "status": "online",
                        "ovs_version": "2.17.9",
                        "bridges": ["br0", "br-int"]
                    },
                    {
                        "id": 2,
                        "hostname": "host2",
                        "ip": "192.168.1.101",
                        "status": "online",
                        "ovs_version": "2.17.9",
                        "bridges": ["br0"]
                    }
                ]
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
    print("\n" + "="*60)
    print("🚀 VXLAN Web Controller v0.1")
    print("="*60)
    print(f"\n📁 Frontend directory: {FRONTEND_DIR}")
    print(f"🌐 Server starting on port {PORT}...")
    print(f"\n✨ Open your browser to: http://localhost:{PORT}")
    print(f"   (or http://192.168.88.164:{PORT} from other machines)")
    print("\n" + "="*60)
    print("API Endpoints (mock data for now):")
    print("  GET  /api/status    - Controller status")
    print("  GET  /api/switches  - Connected switches")
    print("  GET  /api/topology  - Network topology")
    print("  GET  /api/tunnels   - VXLAN tunnels")
    print("  GET  /api/hosts     - OVS hosts")
    print("="*60 + "\n")

    with socketserver.TCPServer(("", PORT), VXLANRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped by user")
            httpd.shutdown()


if __name__ == "__main__":
    main()
