#!/bin/bash
#
# Recira Installation Script
# Intelligent, idempotent installer for the Recira VXLAN Web Controller
#
# Usage:
#   ./install.sh              # Interactive install
#   ./install.sh --uninstall  # Remove Recira
#   ./install.sh --status     # Check installation status
#   ./install.sh --upgrade    # Upgrade existing installation
#   ./install.sh --help       # Show help
#
# Version: 0.7.7
# GitHub: https://github.com/bufanoc/recira
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/recira"
DATA_DIR="/var/lib/recira"
SERVICE_NAME="recira"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
DEFAULT_PORT=8080

# Script directory (where install.sh is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#######################################
# Logging functions
#######################################
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

#######################################
# Check if running as root
#######################################
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

#######################################
# Detect OS type
#######################################
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_TYPE=$ID
        OS_VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS_TYPE="centos"
        OS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+' | head -1)
    else
        OS_TYPE="unknown"
        OS_VERSION="unknown"
    fi

    log_info "Detected OS: ${OS_TYPE} ${OS_VERSION}"
}

#######################################
# Check if a command exists
#######################################
command_exists() {
    command -v "$1" &> /dev/null
}

#######################################
# Check Python version
#######################################
check_python() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 6 ]; then
            log_success "Python $PYTHON_VERSION found (>= 3.6 required)"
            return 0
        else
            log_warn "Python $PYTHON_VERSION found but >= 3.6 required"
            return 1
        fi
    else
        log_warn "Python 3 not found"
        return 1
    fi
}

#######################################
# Install system dependencies
#######################################
install_dependencies() {
    log_info "Installing system dependencies..."

    case $OS_TYPE in
        ubuntu|debian)
            # Update package list (only if older than 1 hour for idempotency)
            if [ ! -f /var/cache/apt/pkgcache.bin ] || \
               [ $(find /var/cache/apt/pkgcache.bin -mmin +60 2>/dev/null | wc -l) -gt 0 ]; then
                apt-get update -qq
            fi

            # Install packages if not present
            PACKAGES="python3 sshpass"
            for pkg in $PACKAGES; do
                if dpkg -l | grep -q "^ii  $pkg "; then
                    log_success "$pkg already installed"
                else
                    log_info "Installing $pkg..."
                    apt-get install -y -qq $pkg
                    log_success "$pkg installed"
                fi
            done
            ;;

        centos|rhel|rocky|almalinux|fedora)
            # Install EPEL for sshpass on CentOS/RHEL
            if [[ "$OS_TYPE" == "centos" || "$OS_TYPE" == "rhel" || "$OS_TYPE" == "rocky" || "$OS_TYPE" == "almalinux" ]]; then
                if ! rpm -q epel-release &>/dev/null; then
                    log_info "Installing EPEL repository..."
                    yum install -y -q epel-release
                fi
            fi

            PACKAGES="python3 sshpass"
            for pkg in $PACKAGES; do
                if rpm -q $pkg &>/dev/null; then
                    log_success "$pkg already installed"
                else
                    log_info "Installing $pkg..."
                    yum install -y -q $pkg
                    log_success "$pkg installed"
                fi
            done
            ;;

        *)
            log_warn "Unknown OS type: $OS_TYPE"
            log_warn "Please manually install: python3, sshpass"
            ;;
    esac
}

#######################################
# Create data directory
#######################################
create_data_dir() {
    if [ -d "$DATA_DIR" ]; then
        log_success "Data directory exists: $DATA_DIR"
    else
        log_info "Creating data directory: $DATA_DIR"
        mkdir -p "$DATA_DIR"
        chmod 750 "$DATA_DIR"
        log_success "Data directory created"
    fi
}

#######################################
# Install Recira files
#######################################
install_files() {
    log_info "Installing Recira to $INSTALL_DIR..."

    # Check if source files exist
    if [ ! -d "$SCRIPT_DIR/backend" ] || [ ! -d "$SCRIPT_DIR/frontend" ]; then
        log_error "Source files not found in $SCRIPT_DIR"
        log_error "Make sure you're running install.sh from the cloned repository"
        exit 1
    fi

    # Create install directory
    mkdir -p "$INSTALL_DIR"

    # Copy files (rsync for efficiency, fall back to cp)
    if command_exists rsync; then
        rsync -a --delete "$SCRIPT_DIR/backend" "$INSTALL_DIR/"
        rsync -a --delete "$SCRIPT_DIR/frontend" "$INSTALL_DIR/"
        [ -f "$SCRIPT_DIR/README.md" ] && rsync -a "$SCRIPT_DIR/README.md" "$INSTALL_DIR/"
        [ -d "$SCRIPT_DIR/docs" ] && rsync -a "$SCRIPT_DIR/docs" "$INSTALL_DIR/"
    else
        rm -rf "$INSTALL_DIR/backend" "$INSTALL_DIR/frontend"
        cp -r "$SCRIPT_DIR/backend" "$INSTALL_DIR/"
        cp -r "$SCRIPT_DIR/frontend" "$INSTALL_DIR/"
        [ -f "$SCRIPT_DIR/README.md" ] && cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/"
        [ -d "$SCRIPT_DIR/docs" ] && cp -r "$SCRIPT_DIR/docs" "$INSTALL_DIR/"
    fi

    log_success "Files installed to $INSTALL_DIR"
}

#######################################
# Create systemd service
#######################################
create_service() {
    log_info "Creating systemd service..."

    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Recira VXLAN Web Controller
Documentation=https://github.com/bufanoc/recira
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/backend/server.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening (optional - comment out if issues)
# ProtectSystem=strict
# ReadWritePaths=$DATA_DIR
# PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload

    log_success "Systemd service created: $SERVICE_NAME"
}

#######################################
# Enable and start service
#######################################
start_service() {
    log_info "Starting Recira service..."

    # Enable service
    if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
        log_success "Service already enabled"
    else
        systemctl enable "$SERVICE_NAME"
        log_success "Service enabled for auto-start"
    fi

    # Start or restart service
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        log_info "Restarting service..."
        systemctl restart "$SERVICE_NAME"
    else
        systemctl start "$SERVICE_NAME"
    fi

    # Wait a moment and check status
    sleep 2
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        log_success "Recira service is running"
    else
        log_error "Service failed to start. Check: journalctl -u $SERVICE_NAME"
        exit 1
    fi
}

#######################################
# Show installation summary
#######################################
show_summary() {
    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')

    echo ""
    echo "=============================================="
    echo -e "${GREEN}Recira Installation Complete!${NC}"
    echo "=============================================="
    echo ""
    echo "  Installation Directory: $INSTALL_DIR"
    echo "  Data Directory:         $DATA_DIR"
    echo "  Service Name:           $SERVICE_NAME"
    echo ""
    echo "  Web UI: http://$SERVER_IP:$DEFAULT_PORT"
    echo "          http://localhost:$DEFAULT_PORT"
    echo ""
    echo "  Commands:"
    echo "    sudo systemctl status $SERVICE_NAME   # Check status"
    echo "    sudo systemctl restart $SERVICE_NAME  # Restart"
    echo "    sudo systemctl stop $SERVICE_NAME     # Stop"
    echo "    sudo journalctl -u $SERVICE_NAME -f   # View logs"
    echo ""
    echo "  GitHub: https://github.com/bufanoc/recira"
    echo ""
    echo "=============================================="
    echo -e "${YELLOW}WARNING: This is for LAB USE ONLY${NC}"
    echo "Credentials are stored in cleartext."
    echo "=============================================="
}

#######################################
# Uninstall Recira
#######################################
uninstall() {
    log_info "Uninstalling Recira..."

    # Stop and disable service
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        log_info "Stopping service..."
        systemctl stop "$SERVICE_NAME"
    fi

    if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
        log_info "Disabling service..."
        systemctl disable "$SERVICE_NAME"
    fi

    # Remove service file
    if [ -f "$SERVICE_FILE" ]; then
        log_info "Removing service file..."
        rm -f "$SERVICE_FILE"
        systemctl daemon-reload
    fi

    # Remove install directory
    if [ -d "$INSTALL_DIR" ]; then
        log_info "Removing installation directory..."
        rm -rf "$INSTALL_DIR"
    fi

    # Ask about data directory
    if [ -d "$DATA_DIR" ]; then
        echo ""
        read -p "Remove data directory $DATA_DIR? (contains hosts/networks config) [y/N]: " response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "$DATA_DIR"
            log_success "Data directory removed"
        else
            log_info "Data directory preserved"
        fi
    fi

    log_success "Recira uninstalled"
}

#######################################
# Show status
#######################################
show_status() {
    echo ""
    echo "Recira Installation Status"
    echo "=========================="

    # Check install directory
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "Installation: ${GREEN}Installed${NC} ($INSTALL_DIR)"
    else
        echo -e "Installation: ${RED}Not installed${NC}"
    fi

    # Check data directory
    if [ -d "$DATA_DIR" ]; then
        echo -e "Data Directory: ${GREEN}Exists${NC} ($DATA_DIR)"
        # Count files
        HOST_COUNT=$([ -f "$DATA_DIR/hosts.json" ] && grep -c '"id"' "$DATA_DIR/hosts.json" 2>/dev/null || echo "0")
        NET_COUNT=$([ -f "$DATA_DIR/networks.json" ] && grep -c '"id"' "$DATA_DIR/networks.json" 2>/dev/null || echo "0")
        echo "  - Hosts: ~$HOST_COUNT"
        echo "  - Networks: ~$NET_COUNT"
    else
        echo -e "Data Directory: ${YELLOW}Not created${NC}"
    fi

    # Check service
    if [ -f "$SERVICE_FILE" ]; then
        if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
            echo -e "Service: ${GREEN}Running${NC}"
        else
            echo -e "Service: ${YELLOW}Stopped${NC}"
        fi

        if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
            echo -e "Auto-start: ${GREEN}Enabled${NC}"
        else
            echo -e "Auto-start: ${YELLOW}Disabled${NC}"
        fi
    else
        echo -e "Service: ${RED}Not configured${NC}"
    fi

    # Check dependencies
    echo ""
    echo "Dependencies:"
    if command_exists python3; then
        echo -e "  Python 3: ${GREEN}$(python3 --version)${NC}"
    else
        echo -e "  Python 3: ${RED}Not installed${NC}"
    fi

    if command_exists sshpass; then
        echo -e "  sshpass: ${GREEN}Installed${NC}"
    else
        echo -e "  sshpass: ${RED}Not installed${NC}"
    fi

    echo ""
}

#######################################
# Show help
#######################################
show_help() {
    echo "Recira Installation Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  (none)        Interactive installation"
    echo "  --uninstall   Remove Recira from system"
    echo "  --status      Show installation status"
    echo "  --upgrade     Upgrade existing installation"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo ./install.sh           # Install Recira"
    echo "  sudo ./install.sh --status  # Check status"
    echo "  sudo ./install.sh --upgrade # Upgrade to latest"
    echo ""
}

#######################################
# Upgrade existing installation
#######################################
upgrade() {
    log_info "Upgrading Recira..."

    # Check if installed
    if [ ! -d "$INSTALL_DIR" ]; then
        log_error "Recira is not installed. Run ./install.sh first."
        exit 1
    fi

    # Stop service if running
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        log_info "Stopping service for upgrade..."
        systemctl stop "$SERVICE_NAME"
    fi

    # Backup data directory (just in case)
    if [ -d "$DATA_DIR" ]; then
        BACKUP_DIR="/tmp/recira-backup-$(date +%Y%m%d%H%M%S)"
        log_info "Backing up data to $BACKUP_DIR..."
        cp -r "$DATA_DIR" "$BACKUP_DIR"
    fi

    # Install new files
    install_files

    # Restart service
    start_service

    log_success "Upgrade complete!"
}

#######################################
# Main installation
#######################################
install() {
    echo ""
    echo "=============================================="
    echo "  Recira - VXLAN Web Controller Installer"
    echo "  Version 0.7.7"
    echo "=============================================="
    echo ""

    check_root
    detect_os

    # Check if already installed
    if [ -d "$INSTALL_DIR" ]; then
        log_warn "Recira is already installed at $INSTALL_DIR"
        read -p "Do you want to reinstall/upgrade? [y/N]: " response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled"
            exit 0
        fi
    fi

    install_dependencies
    check_python
    create_data_dir
    install_files
    create_service
    start_service
    show_summary
}

#######################################
# Main entry point
#######################################
case "${1:-}" in
    --uninstall)
        check_root
        uninstall
        ;;
    --status)
        show_status
        ;;
    --upgrade)
        check_root
        upgrade
        ;;
    --help|-h)
        show_help
        ;;
    "")
        install
        ;;
    *)
        log_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
