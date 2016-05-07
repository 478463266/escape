#!/usr/bin/env bash
# Copyright 2016 Janos Czentye <czentye@tmit.bme.hu>
# Install Python and system-wide packages, required programs and configurations
# for ESCAPEv2 on pre-installed Mininet VM
# Tested on: mininet-2.1.0p2-140718-ubuntu-14.04-server-amd64 and Ubuntu 16.04

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Fail on error
trap on_error ERR

function on_error {
    echo -e "${RED}Error during installation!${NC}"
    exit 1
}

function info() {
    echo -e "${GREEN}$1${NC}"
}

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function install_core {
    info "================================="
    info "==  Install core dependencies  =="
    info "================================="
    echo "ESCAPEv2 version: 2.0.0"
    info "=== Checkout submodules ==="
    git submodule update --init --recursive --merge
    # Remove ESCAPEv2 config file from index in git to untrack changes
    git update-index --assume-unchanged escape.config

    info "=== Add neo4j repository ==="
    sudo sh -c "wget -O - http://debian.neo4j.org/neotechnology.gpg.key | apt-key add -"
    sudo sh -c "echo 'deb http://debian.neo4j.org/repo stable/' > /etc/apt/sources.list.d/neo4j.list"

    info "=== Install ESCAPEv2 core dependencies ==="
    sudo apt-get update
    # Install dependencies
    sudo apt-get -y install python-dev python-pip zlib1g-dev libxml2-dev libxslt1-dev libssl-dev libffi-dev python-crypto neo4j=2.2.7

    # Force cryptography package installation prior to avoid issues in 1.3.2
    sudo -H pip install cryptography==1.3.1
    sudo -H pip install numpy jinja2 py2neo networkx requests ncclient cryptography==1.3.1

    info "=== Configure neo4j graph database ==="
    # Disable authentication in /etc/neo4j/neo4j-server.properties
    sudo sed -i s/dbms\.security\.auth_enabled=true/dbms\.security\.auth_enabled=false/ /etc/neo4j/neo4j-server.properties
    sudo service neo4j-service restart
    # Stick to version  2.2.7
    sudo apt-mark hold neo4j

#    info "=== Compile hwloc2nffg ==="
#    sudo apt-get -y install g++ cmake make libboost-program-options-dev libhwloc-dev libjsoncpp-dev
#    cd "$DIR/hwloc2nffg/build"
#    cmake ../
#    make
}

function install_mn_dep {
    BINDIR=/usr/bin
    MNEXEC=mnexec
    MNUSER=mininet
    MNPASSWD=mininet
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
    if id -u ${MNUSER} >/dev/null 2>&1
    then
        info "=== User: $MNUSER already exist. Skip user addition... ==="
    else
        info "=== Create user: mininet passwd: mininet for communication over NETCONF ==="
        sudo adduser --system --shell /bin/bash --no-create-home ${MNUSER}
        sudo addgroup ${MNUSER} sudo
        echo "$MNUSER:$MNPASSWD" | sudo chpasswd
    fi
    info "\nIf this installation was not performed on a VM, limit the SSH connections only to localhost due to security issues!\n"
}

function install_infra {
    info "==================================================================="
    info "==  Install dependencies for Mininet-based Infrastructure Layer  =="
    info "==================================================================="
    sudo apt-get install -y gcc make automake ssh libssh2-1-dev libgcrypt11-dev libncurses5-dev libglib2.0-dev libgtk2.0-dev

    info "=== Install OpenYuma for NETCONF capability ==="
    cd "$DIR/OpenYuma"
    # -i flag -> got error during first run of make but it seems OK, so ignore...
    make -i
    sudo make install

    if grep -Fxq "# --- ESCAPEv2 ---" "/etc/ssh/sshd_config"
    then
        info "=== Remove previous ESCAPEv2-related sshd config ==="
        sudo sed -in '/.*ESCAPEv2.*/,/.*ESCAPEv2 END.*/d' "/etc/ssh/sshd_config"
    fi

    info "=== Set sshd configuration ==="
    cat <<EOF | sudo tee -a /etc/ssh/sshd_config
# --- ESCAPEv2 ---
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
# --- ESCAPEv2 END ---
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
    make
    sudo make install

    info "=== Install click for VNFs ==="
    cd ${DIR}
    git clone --depth 1 https://github.com/kohler/click.git
    cd click
    ./configure --disable-linuxmodule
    CPU=$(grep -c '^processor' /proc/cpuinfo)
    make -j${CPU}
    sudo make install

    info "=== Install clicky for graphical VNF management ==="
    # sudo apt-get install libgtk2.0-dev
    cd apps/clicky
    autoreconf -i
    ./configure
    make -j${CPU}
    sudo make install
    cd ${DIR}
    rm -rf click

    info "=== Install clickhelper.py ==="
    # install clickhelper.py to be available from netconfd
    sudo ln -vs "$DIR/mininet/mininet/clickhelper.py" /usr/local/bin/clickhelper.py

    if [ ! -f /usr/bin/mnexec ]
    then
        info "=== Pre-installed Mininet not detected! Try to install mn dependencies... ==="
        install_mn_dep
    fi
}

# Install development dependencies as tornado for scripts in ./tools,
# for doc generations, etc.
function install_dev {
    info "=========================================================="
    info "==  Installing additional dependencies for development  =="
    info "=========================================================="
    # tornado for domain emulating scripts under ./tools
    # sphinx for doc generation
    # graphviz for UML class diagram generation
    # texlive-latex-extra for doc generation in PDF format
    sudo apt-get install graphviz texlive-latex-extra
    sudo -H pip install tornado sphinx
}

# Install GUI dependencies
function install_gui {
    info "==========================================================="
    info "==  Installing additional dependencies for internal GUI  =="
    info "==========================================================="
    sudo apt-get install -y python-tk
    sudo -H pip install networkx_viewer
}

# Install all main component
function all {
    install_core
    install_gui
    install_infra
    info "============"
    info "==  Done  =="
    info "============"
    exit 0
}

# Print help
function print_usage {
    echo -e "Usage: $0 [-a] [-c] [-d] [-g] [-h] [-i]"
    echo -e "Install script for ESCAPEv2\n"
    echo -e "options:"
    echo -e "\t-a:   (default) install (A)ll ESCAPEv2 components (identical with -cgi)"
    echo -e "\t-c:   install (C)ore dependencies for Global Orchestration"
    echo -e "\t-d:   install additional dependencies for (D)evelopment and test tools"
    echo -e "\t-g:   install dependencies for our rudimentary (G)UI"
    echo -e "\t-h:   print this (H)elp message"
    echo -e "\t-i:   install components of (I)nfrastructure Layer for Local Orchestration"
    exit 2
}

if [ $# -eq 0 ]
then
    # No param was given
    all
else
    while getopts 'acdghi' OPTION
    do
        case ${OPTION} in
        a)  all;;
        c)  install_core;;
        d)  install_dev;;
        g)  install_gui;;
        h)  print_usage;;
        i)  install_infra;;
        \?)  print_usage;;
        esac
    done
    #shift $(($OPTIND - 1))
fi

info "============"
info "==  Done  =="
info "============"
