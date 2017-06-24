# ESCAPEv2: Extensible Service ChAin Prototyping Environment using Mininet, Click, NETCONF and POX

## Introduction

On the one hand, ESCAPE (Extensible Service ChAin Prototyping Environment) is a
general prototyping framework which supports the development of several parts of
the service chaining architecture including VNF implementation, traffic steering,
virtual network embedding, etc.  On the other hand, ESCAPE is a proof of concept
prototype implementing a novel SFC (Service Function Chaining) architecture
proposed by EU FP7 UNIFY project: https://www.fp7-unify.eu/.
It is a realization of the UNIFY service programming and orchestration framework
which enables the joint programming and virtualization of cloud and networking
resources.

The main scope of ESCAPE as a multi-domain orchestrator (MdO) is to
discover, detect and manage infrastructure domains using different
technologies.

ESCAPE receives the specific service requests on its REST-like API,
orchestrate the requested Service Function Chains on the full resource
view (which is constructed automatically based on the information
gathered from lower level domains) making use of a dedicated resource
mapping algorithm and propagate the calculated service parts to the
corresponding Domain Orchestrators (DO).

In addition, ESCAPE can be used in the role of a local Domain
Orchestrator when an extended version of Mininet network emulation
platform is used as an infrastructure which is able to run Network
Functions and realize dataplane connectivity.

For detailed information see the online documentation: https://sb.tmit.bme.hu/escape/

## Installation

All the required dependencies for the full set of ESCAPE's features:

```shell
$ sudo apt -y install python2.7 python-dev python-pip zlib1g-dev libxml2-dev libxslt1-dev \
    libssl-dev libffi-dev python-crypto openjdk-7-jdk neo4j=2.2.7 gcc make socat psmisc xterm \
    ssh iperf iproute telnet python-setuptools cgroup-bin ethtool help2man pyflakes pylint pep8 \
    openvswitch-switch automake ssh libssh2-1-dev libgcrypt11-dev libncurses5-dev libglib2.0-dev \
    libgtk2.0-dev graphviz texlive-latex-extra

$ sudo pip -H install numpy jinja2 py2neo networkx requests ncclient cryptography==1.3.1 tornado \
    sphinx networkx_viewer
```

The `install_dep.sh` script is responsible for managing the dependencies. It sets
the required sym-links, updates the related submodules and installs only the 
necessary packages regarding the given install parameters.

For automatically setting up the submodules and its submodules recursively, 
the `project-setup.sh` script has been added to the project.

```text
$ ./project-setup.sh -h
Setup submodules according to given project for ESCAPEe.
If project name is not given the script tries to detect it
from the git's local configurations.

Usage: ./project-setup.sh [-h] [-p project]
Parameters:
	 -h, --help      show this help message and exit
	 -p, --project   setup project name based on: .gitmodules.<name>

Example: ./project-setup.sh -p 5gex
```

If you don't want to use the complex install script or the included project setup script either
then just create a sym-link to the relevant gitmodules file with the name `.gitmodules` 
and update the submodule manually.

```shell
$ ln -vfs .gitmodules.<PROJECT> .gitmodules
$ git submodules update --init
```

Because the core ESCAPE relies on POX and written in Python there is no need
for explicit compiling or installation. The only requirement need to be
pre-installed is a Python interpreter.

The recommended Python version, in which the development and mostly the testing
are performed, is the standard CPython **2.7.13**.

The best choice of platform on wich ESCAPE is recommended to install and the
`install-dep.sh` is tested is **Ubuntu 16.04.2 LTS**.

However ESCAPE is developed on Xubuntu 16.04, some issues are experienced
related to SAP-xterm initiation in case the platform was an Ubuntu 16.04 server
image and ESCAPE was started through an SSH channel.
Considering this limitation we recommend to use the older 14.04 LTS version in
case ESCAPE is intended to run as a local Domain Orchestrator on a VM without any graphical interface.

#### The preferred way:

1. Download one of pre-build Ubuntu LTS VM image, create one in your preferred VM
    manager (or just use the default Docker image of Ubuntu).

2. Create the `.ssh` folder in the home directory and copy your private RSA key
    into the VM with the name `id_rsa`. If you use a VM image then the following
    commands can be used in the VM to copy your RSA key from your host:
    
    ```shell
    $ cd
    $ mkdir .ssh
    $ scp <your_user>@<host_ip>:~/.ssh/<your_ssh_key> ~/.ssh/id_rsa
    $ sudo chmod 700 .ssh && sudo chmod 600 .ssh/id_rsa
    ```
3. Clone the shared *escape* repository (the default folder name will be: `escape`).

    ```shell
    $ git clone <git repo URL> escape
    ```

4. Install the necessary dependencies with the `install_dep.sh` script (system
    and Python packages, optionally the OpenYuma with VNFStarter module, etc.):

    ```shell
    $ cd escape
    $ ./install_dep.sh
    ```

   In a high level the script above takes care of the following things:
    
   * Setup sym-links and submodules for given project name
   * Install the necessary system and Python packages
   * Compile and install the `OpenYuma` tools with our `VNF_starter` module
   * Compile and install `Click` modular router and `The Click GUI`.
   * Install `neo4j` graph database for NFIB
      
   See help menu for further parameters:
    
   ```shell
   $ ./install-dep.sh -h
   Usage: ./install-dep.sh [-a] [-c] [-d] [-g] [-h] [-i] [-p project]
   Install script for ESCAPEv2

   options:
        -a:   (default) install (A)ll ESCAPEv2 components (identical with -cgi)
        -c:   install (C)ore dependencies for Global Orchestration
        -d:   install additional dependencies for (D)evelopment and test tools
        -g:   install dependencies for our rudimentary (G)UI
        -h:   print this (H)elp message
        -i:   install components of (I)nfrastructure Layer for Local Orchestration
        -p:   explicitly setup project name based on: .gitmodules.<name>
    ```
    
5. Run ESCAPE with one of the commands listed in a later section. To see the
    available arguments of the top stating script check the help menu:
    
    ```shell
    $ ./escape.py --help
    ```
    
    To verify ESCAPE in **MdO** role a dry-run can be performed without any command line flag.
    If ESCAPE is up and running, the following line will be logged to the console:
    
    ```
       > [core                   ] ESCAPEv2 is up.
    ```
    
    This final log entry means that each component was installed and configured successfully.
    
    To verify ESCAPE in **DO** role with the embedding engine and all of it's components,
    the following command can be run in order to test the reachability between the initiated
    service access points (SAP) represented by the(``xterm``) windows with the ``ping`` command:
    
    ```shell
    $ ./escape.py -df -s examples/escape-mn-req.nffg
 
    # on SAP1 xterm
    $ ping sap2
    # on SAP2 xterm
    $ ping sap1
    ```
    This command starts the full stack ESCAPE with the default topology (`examples/escape-mn-topo.nffg`)
    and initiate a service request consists of a *HeaderCompressor* and a *HeaderDecompressor* VNF
    for one direction and a simple *Forwarder* VNF for the backward direction between SAP1 and SAP2.
    The two initiated SAP should reach each other after the service request has been processed.

## ESCAPE as a Docker container

ESCAPE can be run in a Docker container. To create the basic image, issue the following command 
in the project root:

```shell
$ sudo docker build --rm --no-cache -t mdo/ro .
```

This command creates a minimal image based on the official Python image with the name: _mdo/ro_, 
installs the required Python dependencies listed in `requirement.txt` and sets the entry point.

To create and start a persistent container based on the _mdo/ro_ image, use the following commands:

```shell
$ sudo docker create --name escape -p 8008:8008 -p 8888:8888 -it mdo/ro
$ sudo docker start -i escape
```

To create a one-time container, use the following command:

```shell
$ sudo docker run --rm -p 8008:8008 -p 8888:8888 -ti mdo/ro
```

Other helper scripts for the dockerization can be found under the ``docker`` folder.

## Tests

ESCAPE has several testcases formed as Unit tests. These tests can be found under
the `test` folder.

Dependent packages for the test can be installed with the `install_requirements.sh` script.
To run the test see the main test runner script:

```
$ ./test/run_tests.py -h
usage: run_tests.py [-h] [-f] [-o] [-t t] [-s] [-v]
                    [testcases [testcases ...]]

ESCAPE Test runner

positional arguments:
  testcases          list test case names you want to run. Example:
                     ./run_tests.py case05 case03 --show-output

optional arguments:
  -h, --help         show this help message and exit
  -f, --failfast     Stop on first failure
  -o, --show-output  Show ESCAPE output
  -t t, --timeout t  define explicit timeout in sec (default: 30s)
  -s, --standalone   run standalone mode: no timeout, no quitting
  -v, --verbose      Run in verbose mode and show output
```

## Documentation

The documentation can be generated from source code with `generate-docs.sh` script
or directly with the `Makefile` in `escape/doc` directory.
The generated doc can be found in `escape/doc/build/`.

```shell
$ ./escape/doc/generate-doc.sh
```

Requirements:
    
* sphinx (`sudo -H pip install sphinx`)
* texlive-latex-extra (`sudo apt install -y texlive-latex-extra`)

Online version: https://sb.tmit.bme.hu/escape/

## License

Licensed under the Apache License, Version 2.0; see LICENSE file.

    Copyright (C) 2017 by
    János Czentye <janos.czentye@tmit.bme.hu>
    Balázs Németh <balazs.nemeth@tmit.bme.hu>
    Balázs Sonkoly <balazs.sonkoly@tmit.bme.hu>
