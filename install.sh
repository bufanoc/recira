#!/bin/bash
################################################################################
# Recira Installation Script
# Version: 0.6.1
#
# This script will be enhanced in future versions to provide one-line installation
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/bufanoc/recira/master/install.sh | bash
#
################################################################################

set -e

echo "============================================================"
echo "Recira - Open Source SDN Platform for VXLAN Overlay Networks"
echo "============================================================"
echo ""
echo "⚠️  This installer is a placeholder for v0.6.1"
echo ""
echo "For now, please use manual installation:"
echo ""
echo "1. Clone the repository:"
echo "   git clone https://github.com/bufanoc/recira.git"
echo ""
echo "2. Install prerequisites:"
echo "   # Ubuntu/Debian:"
echo "   sudo apt-get update"
echo "   sudo apt-get install -y git python3 python3-pip sshpass"
echo ""
echo "   # CentOS/RHEL:"
echo "   sudo yum install -y git python3 python3-pip sshpass"
echo ""
echo "3. Start the server:"
echo "   cd recira"
echo "   python3 backend/server.py"
echo ""
echo "4. Open browser to: http://localhost:8080"
echo ""
echo "For detailed instructions, see: INSTALL.md"
echo "============================================================"
echo ""

# TODO: Implement automated installation in v0.7+
# Features to add:
# - Detect OS automatically
# - Install prerequisites
# - Clone repository
# - Setup systemd service
# - Configure firewall
# - Optional: Install OVS on controller host
# - Print access URL and next steps

exit 0
