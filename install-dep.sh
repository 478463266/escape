#!/usr/bin/env bash
# Copyright 2016 Janos Czentye <czentye@tmit.bme.hu>
# Install Python and system-wide packages, required programs and configurations
# for ESCAPEv2 on pre-installed Mininet VM
# Tested on: Ubuntu 14.04.4 LTS and 16.04 LTS

### Initial setup

# Constants for colorful logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

set -euo pipefail

# Fail on error
trap "on_error 'Got signal: SIGHUP'" SIGHUP
trap "on_error 'Got signal: SIGINT'" SIGINT
trap "on_error 'Got signal: SIGTERM'" SIGTERM
trap on_error ERR

function on_error() {
    echo -e "\n${RED}Error during installation! ${1-}${NC}"
    exit 1
}

function info() {
    echo -e "${GREEN}${1-INFO}${NC}"
}

function warn() {
    echo -e "\n${YELLOW}WARNING: ${1-WARNING}${NC}"
    read -rsp $'Press ENTER to continue...\n'
}

function env_setup {
    # Set environment
    set +u
    # If LC_ALL is not set up
    if [[ ! "$LC_ALL" ]]; then
        if [[ "$LANG" ]]; then
            # Set LC_ALL as LANG
            info "=== Set environment ==="
            sudo locale-gen $LANG
            export LC_ALL=$LANG
            locale
        fi
    fi
    set -u
}

### Constants

# Project - unify | 5gex | ericsson | sb
PROJECT="sb"

# Component versions
JAVA_VERSION=7
NEO4J_VERSION=2.2.7
CRYPTOGRAPHY_VERSION=1.3.1

# Other constants
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

BINDIR=/usr/bin
MNEXEC=mnexec
MNUSER=mininet
MNPASSWD=mininet

# Distributor constants
if [ -f /etc/lsb-release ]; then
    DISTRIB_ID=$(lsb_release -si)
    DISTRIB_VER=$(lsb_release -sr)
    info "Detected platform is $DISTRIB_ID, version: $DISTRIB_VER!"
else
    warn "Detected platform is NOT Ubuntu! This may lead to skip some installation steps!"
fi

### Menu point functions

function install_core {
    env_setup
    info "================================="
    info "==  Install core dependencies  =="
    info "================================="
    echo "ESCAPEv2 version: 2.0.0"

#    # Create symlink to the appropriate .gitmodules file
#    info "=== Checkout submodules ==="
#    if [ -f ".gitmodules.$PROJECT" ]; then
#        ln -vfs ".gitmodules.$PROJECT" .gitmodules
#    else
#        on_error "Missing submodule file of project: $PROJECT for ESCAPE repo!"
#    fi
#    git submodule update --init --remote
#
#    info "=== Create symlinks for submodules ==="
#    cd "$DIR/dummy-orchestrator"
#    if [ -f ".gitmodules.$PROJECT" ]; then
#        ln -vfs ".gitmodules.$PROJECT" .gitmodules
#    else
#        on_error "Missing submodule file of project: $PROJECT for dummy-orchestrator!"
#    fi
#    cd "$DIR/mapping"
#    if [ -f ".gitmodules.$PROJECT" ]; then
#        ln -vfs ".gitmodules.$PROJECT" .gitmodules
#    else
#        on_error "Missing submodule file of project: $PROJECT for mapping!"
#    fi
#    cd "$DIR"
#    git submodule update --init --remote --recursive --merge

    info "=== Setup project ==="
    # Git return error during submodule change -> disable error catching
    set +e
    if [ -f "project-setup.sh" ]; then
        . ./project-setup.sh "$PROJECT"
    else
        on_error "Project setup script is missing!"
    fi
    set -e

    # Remove ESCAPEv2 config file from index in git to untrack changes
    # git update-index --assume-unchanged escape.config

    info "=== Add neo4j repository ==="
    sudo sh -c "wget -O - http://debian.neo4j.org/neotechnology.gpg.key | apt-key add -"
    sudo sh -c "echo 'deb http://debian.neo4j.org/repo stable/' | tee /etc/apt/sources.list.d/neo4j.list"

    sudo apt-get install -y software-properties-common

    if [[ ! $(sudo apt-cache search openjdk-${JAVA_VERSION}-jdk) ]]; then
        info "=== Add OpenJDK repository and install Java $JAVA_VERSION ==="
        sudo add-apt-repository -y ppa:openjdk-r/ppa
    fi

    if [ "$DISTRIB_ID" = "Ubuntu" -a "$DISTRIB_VER" = "14.04" ]; then
        info "=== Add 3rd party PPA repo for most recent Python2.7 ==="
        sudo add-apt-repository -y ppa:fkrull/deadsnakes-python2.7
    fi

    info "=== Install ESCAPEv2 core dependencies ==="
    sudo apt-get update
    # Install Java 8 explicitly
    sudo apt-get install -y openjdk-${JAVA_VERSION}-jdk
    # Install Python 2.7.11 explicitly
    sudo apt-get install -y python2.7
    # Install dependencies
    sudo apt-get install -y python-dev python-pip zlib1g-dev libxml2-dev libxslt1-dev \
                            libssl-dev libffi-dev python-crypto neo4j=${NEO4J_VERSION}

    # Force cryptography package installation prior to avoid issues in 1.3.2
    info "=== Install ESCAPEv2 Python dependencies ==="
    sudo -H pip install --upgrade setuptools
    sudo -H pip install cryptography==${CRYPTOGRAPHY_VERSION}
    sudo -H pip install numpy jinja2 py2neo networkx requests ncclient
    # Update setuptools explicitly to workaround a bug related to 3.x.x version

    info "=== Install ESCAPEv2 Python dependencies ==="
    sudo -H pip install flask rainbow_logging_handler

    info "=== Configure neo4j graph database ==="
    # Disable authentication in /etc/neo4j/neo4j.conf <-- neo4j >= 3.0
    if [ -f /etc/neo4j/neo4j.conf ]; then
        # neo4j >= 3.0
        sudo sed -i /dbms\.security\.auth_enabled=false/s/^#//g /etc/neo4j/neo4j.conf
        sudo service neo4j restart
    elif [ -f /etc/neo4j/neo4j-server.properties ]; then
        # neo4j <= 2.3.4
        sudo sed -i s/dbms\.security\.auth_enabled=true/dbms\.security\.auth_enabled=false/ /etc/neo4j/neo4j-server.properties
        sudo service neo4j-service restart
    else
        on_error "=== neo4j server configuration file was not found! ==="
    fi
    # Freeze neo4j version
    echo "Mark current version of neo4j: $NEO4J_VERSION as held back..."
    sudo apt-mark hold neo4j
    info "=== Install dependencies for testing ==="
    sudo apt-get install -y openvswitch-switch
}

function install_mn_dep {
    env_setup
    info "=== Install Mininet dependencies ==="
    # Copied from /mininet/util/install.sh
    sudo apt-get install -y gcc make socat psmisc xterm ssh iperf iproute telnet \
    python-setuptools cgroup-bin ethtool help2man pyflakes pylint pep8
    info "=== Install Open vSwitch ==="
    sudo apt-get install -y openvswitch-switch
    info "=== Compile and install 'mnexec' execution utility  ==="
    cd "$DIR/mininet"
    make mnexec
    sudo install -v ${MNEXEC} ${BINDIR}
    if id -u ${MNUSER} >/dev/null 2>&1; then
        info "=== User: $MNUSER already exist. Skip user addition... ==="
    else
        info "=== Create user: mininet passwd: mininet for communication over NETCONF ==="
        sudo adduser --system --shell /bin/bash --no-create-home ${MNUSER}
        sudo addgroup ${MNUSER} sudo
        echo "$MNUSER:$MNPASSWD" | sudo chpasswd
    fi
    if [ "$DISTRIB_VER" = "14.04" ]; then
        if grep -Fxq "# --- ESCAPE-mininet ---" "/etc/ssh/sshd_config"; then
            info "=== Remove previous ESCAPEv2-related mininet config ==="
            sudo sed -in '/.*ESCAPE-mininet.*/,/.*ESCAPE-mininet END.*/d' "/etc/ssh/sshd_config"
        fi

        info "=== Restrict user: mininet to be able to establish SSH connection only from: localhost ==="
        # Only works with OpenSSH_6.6.1p1 and tested on Ubuntu 14.04
        cat <<EOF | sudo tee -a /etc/ssh/sshd_config
# --- ESCAPE-mininet ---
# Restrict mininet user to be able to login only from localhost
Match Host *,!localhost
  DenyUsers  mininet
# --- ESCAPE-mininet END---
EOF
    # sudo sh -c 'echo "# --- ESCAPE-mininet ---\n# Restrict mininet user to be able to login only from localhost\nMatch Host *,!localhost\n  DenyUsers  mininet\n# --- ESCAPE-mininet END---" | tee -a /etc/ssh/sshd_config'
    else
        warn "\nIf this installation was not performed on an Ubuntu 14.04 VM, limit the SSH connections only to localhost due to security issues!\n"
    fi
}

function install_infra {
    env_setup
    info "==================================================================="
    info "==  Install dependencies for Mininet-based Infrastructure Layer  =="
    info "==================================================================="
    sudo apt-get install -y gcc make automake ssh libxml2-dev libssh2-1-dev libgcrypt11-dev libncurses5-dev libglib2.0-dev libgtk2.0-dev

    info "=== Install OpenYuma for NETCONF capability ==="
    cd "$DIR/OpenYuma"
    #make clean
    make -i
    sudo make install

    if grep -Fxq "# --- ESCAPE-sshd ---" "/etc/ssh/sshd_config"; then
        info "=== Remove previous ESCAPEv2-related sshd config ==="
        sudo sed -in '/.*ESCAPE-sshd.*/,/.*ESCAPE-sshd END.*/d' "/etc/ssh/sshd_config"
    fi

    info "=== Set sshd configuration ==="
    cat <<EOF | sudo tee -a /etc/ssh/sshd_config
# --- ESCAPE-sshd ---
# Only 8 Port can be used as a listening port for SSH daemon.
# The default Port 22 has already reserved one port.
# To overcome this limitation the openssh-server needs to be
# modified and recompiled from source.
Port 830
Port 831
Port 832
Port 833
Port 834
Port 835
Port 836
Subsystem netconf /usr/sbin/netconf-subsystem
# --- ESCAPEv2-sshd END ---
EOF

    info "=== Restart sshd ==="
    #sudo /etc/init.d/ssh restart
    sudo service ssh restart

    # sudo apt-get install libglib2.0-dev
    info "=== Installing VNF starter module for netconfd ==="
    cd "$DIR/Unify_ncagent/vnf_starter"
    mkdir -p bin
    mkdir -p lib
    sudo cp vnf_starter.yang /usr/share/yuma/modules/netconfcentral/

    # Docker workaround
    if [ ! -f /usr/include/glib-2.0/glib/glib-autocleanups.h ]; then
        sudo wget -vP /usr/include/glib-2.0/glib/ https://github.com/GNOME/glib/blob/master/glib/glib-autocleanups.h
    fi

    make clean
    make
    sudo make install

    info "=== Install click for VNFs ==="
    cd ${DIR}
    if [ ! -d click ]; then
        git clone --depth 1 https://github.com/kohler/click.git
    fi
    cd click
    ./configure --disable-linuxmodule
    CPU=$(grep -c '^processor' /proc/cpuinfo)
    make clean
    make -j${CPU}
    sudo make install

    # sudo apt-get install libgtk2.0-dev
    info "=== Install clicky for graphical VNF management ==="
    cd apps/clicky
    autoreconf -i
    ./configure
    make clean
    make -j${CPU}
    sudo make install

    # Remove click codes
    # cd ${DIR}
    # rm -rf click

    info "=== Install clickhelper.py ==="
    # install clickhelper.py to be available from netconfd
    sudo ln -vfs "$DIR/mininet/mininet/clickhelper.py" /usr/local/bin/clickhelper.py

    if [ ! -f /usr/bin/mnexec ]; then
        info "=== Pre-installed Mininet not detected! Try to install mn dependencies... ==="
        install_mn_dep
    fi
}

# Install development dependencies as tornado for scripts in ./tools,
# for doc generations, etc.
function install_dev {
    env_setup
    info "=========================================================="
    info "==  Installing additional dependencies for development  =="
    info "=========================================================="
    # tornado for domain emulating scripts under ./tools
    # sphinx for doc generation
    # graphviz for UML class diagram generation
    # texlive-latex-extra for doc generation in PDF format
    sudo apt-get install -y graphviz texlive-latex-extra
    sudo -H pip install tornado sphinx
}

# Install GUI dependencies
function install_gui {
    env_setup
    info "==========================================================="
    info "==  Installing additional dependencies for internal GUI  =="
    info "==========================================================="
    sudo apt-get install -y python-tk
    sudo -H pip install networkx_viewer
}

# Install all main component
function all {
    env_setup
    install_core
    install_gui
    install_infra
}

# Print help
function print_usage {
    echo -e "Usage: $0 [-a] [-c] [-d] [-g] [-h] [-i] [-p project]"
    echo -e "Install script for ESCAPEv2\n"
    echo -e "options:"
    echo -e "\t-a:   (default) install (A)ll ESCAPEv2 components (identical with -cgi)"
    echo -e "\t-c:   install (C)ore dependencies for Global Orchestration"
    echo -e "\t-d:   install additional dependencies for (D)evelopment and test tools"
    echo -e "\t-g:   install dependencies for our rudimentary (G)UI"
    echo -e "\t-h:   print this (H)elp message"
    echo -e "\t-i:   install components of (I)nfrastructure Layer for Local Orchestration"
    echo -e "\t-p:   use specific project module files [unify|sb|5gex|ericsson] default: sb"
    exit 2
}

if [ $# -eq 0 ]; then
    # No param was given, call all with default project
    all
else
    # Parse optional project parameter
    while getopts ':p:' OPTION; do
        case ${OPTION} in
            p)  PROJECT=$OPTARG;;
        esac
    done
    OPTIND=1    # Reset getopts
    info "User project config: $PROJECT"
    while getopts 'acdghip:' OPTION; do
        case ${OPTION} in
            a)  all;;
            c)  install_core;;
            d)  install_dev;;
            g)  install_gui;;
            h)  print_usage;;
            i)  install_infra;;
            p)  if [ $# -eq 2 ]; then all; fi;; # If only -p was set, call all else skip
            \?)  print_usage;;
        esac
    done
    #shift $(($OPTIND - 1))
fi

info "============"
info "==  Done  =="
info "============"
# Force to return with 0 for docker build
exit 0