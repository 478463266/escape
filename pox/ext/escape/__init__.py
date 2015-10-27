# Copyright 2015 Janos Czentye <czentye@tmit.bme.hu>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Unifying package for ESCAPEv2 functions.

'cfg' defines the default configuration settings such as the concrete
RequestHandler and strategy classes, the initial Adapter classes, etc.

`CONFIG` contains the ESCAPEv2 dependent configuration as an
:any:`ESCAPEConfig`.
"""
__project__ = "ESCAPEv2"
__authors__ = "Janos Czentye, Balazs Sonkoly, Levente Csikor"
__copyright__ = "Copyright 2015, under Apache License Version 2.0"
__credits__ = "Janos Czentye, Balazs Sonkoly, Levente Csikor, Attila Csoma, " \
              "Felician Nemeth, Andras Gulyas, Wouter Tavernier, and Sahel " \
              "Sahhaf"
__license__ = "Apache License, Version 2.0"
__version__ = "2.0.0"
__maintainer__ = "Janos Czentye"
__email__ = "czentye@tmit.bme.hu"
__status__ = "prototype"

from escape.util.config import ESCAPEConfig
CONFIG = None

# Default configuration object which contains static and running
# configuration for Layer APIs, DomainManagers, Adapters and other components
cfg = {"service": {  # Service Adaptation Sublayer
                     "MAPPER": {"module": "escape.service.sas_mapping",
                                "class": "ServiceGraphMapper",
                                "mapping-enabled": False},
                     "STRATEGY": {"module": "escape.service.sas_mapping",
                                  "class": "DefaultServiceMappingStrategy",
                                  "THREADED": False},
                     "PROCESSOR": {"module": "escape.util.mapping",
                                   "class": "ProcessorSkipper",
                                   "enabled": False},
                     "REST-API": {"module": "escape.service.sas_API",
                                  "class": "ServiceRequestHandler",
                                  "address": "0.0.0.0", "port": 8008,
                                  "prefix": "escape"}},
       "orchestration": {  # Resource Orchestration Sublayer
                           "MAPPER": {"module": "escape.orchest.ros_mapping",
                                      "class": "ResourceOrchestrationMapper",
                                      "mapping-enabled": True},
                           "STRATEGY": {"module": "escape.orchest.ros_mapping",
                                        "class": "ESCAPEMappingStrategy",
                                        "THREADED": False},
                           "PROCESSOR": {"module": "escape.util.mapping",
                                         "class": "ProcessorSkipper",
                                         "enabled": True},
                           "Sl-Or": {"module": "escape.orchest.ros_API",
                                     "class": "ROSAgentRequestHandler",
                                     "prefix": "escape",
                                     "address": "0.0.0.0",
                                     "port": 8888,
                                     "virtualizer_type": "GLOBAL"},
                           "Cf-Or": {"module": "escape.orchest.ros_API",
                                     "class": "CfOrRequestHandler",
                                     "prefix": "cfor",
                                     "address": "0.0.0.0",
                                     "port": 8889,
                                     "virtualizer_type": "GLOBAL"}},
       "adaptation": {  # Controller Adaptation Sublayer
                        # Default managers need to start at init
                        # "DEFAULTS": ["REMOTE-ESCAPE","SDN","OPENSTACK","UN"],
                        "DEFAULTS": [],
                        # Specific Domain Adapters for DomainManagers
                        "INTERNAL-POX": {"module": "escape.adapt.adapters",
                                         "class": "InternalPOXAdapter",
                                         "address": "127.0.0.1", "port": 6653,
                                         "keepalive": False},
                        "SDN-POX": {"module": "escape.adapt.adapters",
                                    "class": "SDNDomainPOXAdapter",
                                    "address": "0.0.0.0", "port": 6633,
                                    "keepalive": False},
                        "MININET": {"module": "escape.adapt.adapters",
                                    "class": "InternalMininetAdapter"},
                        "SDN-TOPO": {"module": "escape.adapt.adapters",
                                     "class": "SDNDomainTopoAdapter",
                                     "path": "sdn-topo.nffg"  # relative to ext/
                                     },
                        "VNFStarter": {"module": "escape.adapt.adapters",
                                       "class": "VNFStarterAdapter",
                                       "username": "mininet",
                                       "password": "mininet",
                                       "server": "127.0.0.1", "port": 830},
                        "ESCAPE-REST": {"module": "escape.adapt.adapters",
                                        "class": "RemoteESCAPEv2RESTAdapter",
                                        "url": "http://localhost:8083"},
                        "OpenStack-REST": {"module": "escape.adapt.adapters",
                                           "class": "OpenStackRESTAdapter",
                                           "url": "http://localhost:8081"},
                        "UN-REST": {"module": "escape.adapt.adapters",
                                    "class": "UniversalNodeRESTAdapter",
                                    "url": "http://localhost:8082"},
                        # Specific Domain Managers
                        "INTERNAL": {"module": "escape.adapt.managers",
                                     "class": "InternalDomainManager",
                                     "poll": False},
                        "REMOTE-ESCAPE": {"module": "escape.adapt.managers",
                                          "class": "RemoteESCAPEDomainManager",
                                          "poll": False},
                        "OPENSTACK": {"module": "escape.adapt.managers",
                                      "class": "OpenStackDomainManager",
                                      "poll": False},
                        "UN": {"module": "escape.adapt.managers",
                               "class": "UniversalNodeDomainManager",
                               "poll": False},
                        "DOCKER": {"module": "escape.adapt.managers",
                                   "class": "DockerDomainManager",
                                   "poll": False},
                        "SDN": {"module": "escape.adapt.managers",
                                "class": "SDNDomainManager", "poll": False},
                        # Shutdown strategy config
                        "RESET-DOMAINS-AFTER-SHUTDOWN": True},
       "infrastructure": {  # Infrastructure Layer
                            "NETWORK-OPTS": None,  # Additional opts for Mininet
                            "TOPO": "escape-mn-topo.nffg",  # relative to ext/
                            "FALLBACK-TOPO": {"module": "escape.infr.topology",
                                              "class":
                                                "FallbackDynamicTopology"},
                            "SAP-xterms": True,
                            "SHUTDOWN-CLEAN": True},
       # "additional-config-file": "escape.config"
       }  # relative to ext/


def add_dependencies ():
  """
  Add dependency directories to PYTHONPATH.
  Dependencies are directories besides the escape.py initial script except pox.

  :return: None
  """
  import os
  import sys
  from pox.core import core

  # Project root dir relative to unify.py top module which is/must be under
  # pox/ext
  root = os.path.abspath(os.path.dirname(__file__) + "../../../..")
  for sub_folder in os.listdir(root):
    abs_sub_folder = os.path.join(root, sub_folder)
    if not os.path.isdir(abs_sub_folder):
      continue
    if not(sub_folder.startswith('.') or sub_folder.upper().startswith(
         'PYTHON')) and sub_folder not in (
         "pox", "OpenYuma", "Unify_ncagent", "tools", "gui", "include", "share",
         "lib", "bin"):
      if abs_sub_folder not in sys.path:
        core.getLogger().debug("Add dependency: %s" % abs_sub_folder)
        sys.path.insert(0, abs_sub_folder)
      else:
        core.getLogger().debug("Dependency: %s already added." % abs_sub_folder)

def launch():
  # Detect and add dependency directories
  add_dependencies()

  # Define global configuration and try to load additions from file
  global CONFIG
  CONFIG = ESCAPEConfig(cfg).load_config()
