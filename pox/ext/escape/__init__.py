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

# Default configuration object which contains static and running
# configuration for Layer APIs, DomainManagers, Adapters and other components
cfg = {"service": {  # Service Adaptation Sublayer
                     "MAPPER": {"module": "escape.service.sas_mapping",
                                "class": "ServiceGraphMapper",
                                "mapping-enabled": False},
                     "STRATEGY": {"module": "escape.service.sas_mapping",
                                  "class": "DefaultServiceMappingStrategy",
                                  "THREADED": True},
                     "REST-API": {"module": "escape.service.sas_API",
                                  "class": "ServiceRequestHandler",
                                  "address": "0.0.0.0", "port": 8008,
                                  "prefix": "escape"}},
       "orchestration": {  # Resource Orchestration Sublayer
                           "MAPPER": {"module": "escape.orchest.ros_mapping",
                                      "class": "ResourceOrchestrationMapper",
                                      "mapping-enabled": False},
                           "STRATEGY": {"module": "escape.orchest.ros_mapping",
                                        "class": "ESCAPEMappingStrategy",
                                        "THREADED": True},
                           "AGENT": {"module": "escape.orchest.ros_API",
                                     "class": "ROSAgentRequestHandler",
                                     "address": "0.0.0.0", "port": 8888,
                                     "prefix": "escape"}},
       "adaptation": {  # Controller Adaptation Sublayer
                        # Default managers need to start at init
                        # "DEFAULTS": ("OPENSTACK",), # OpenStack Agent REST API
                        # "DEFAULTS": ["REMOTE-ESCAPE", "SDN", "OPENSTACK", "UN"],
                        "DEFAULTS": ["OPENSTACK", "UN"],
                        # Specific Domain Adapters for DomainManagers
                        "INTERNAL-POX": {"module": "escape.adapt.components",
                                         "class": "InternalPOXAdapter",
                                         "address": "0.0.0.0", "port": "6633"},
                        "MININET": {"module": "escape.adapt.components",
                                    "class": "InternalMininetAdapter"},
                        "VNFStarter": {"module": "escape.adapt.components",
                                       "class": "VNFStarterAdapter",
                                       "username": "mininet",
                                       "password": "mininet",
                                       "server": "127.0.0.1", "port": 830},
                        "ESCAPE-REST": {"module": "escape.adapt.components",
                                        "class": "RemoteESCAPEv2RESTAdapter",
                                        "url": "http://192.168.1.111:8888/escape/"},
                        "OpenStack-REST": {"module": "escape.adapt.components",
                                           "class": "OpenStackRESTAdapter",
                                           "url":
                                             "http://localhost:8081"},
                        "UN-REST": {"module": "escape.adapt.components",
                                    "class": "UnifiedNodeRESTAdapter",
                                    "url": "http://localhost:8082"},
                        # Specific Domain Managers
                        "INTERNAL": {"module": "escape.adapt.components",
                                     "class": "InternalDomainManager",
                                     "poll": False},
                        "REMOTE-ESCAPE": {"module": "escape.adapt.components",
                                          "class": "RemoteESCAPEDomainManager",
                                          "poll": False},
                        "OPENSTACK": {"module": "escape.adapt.components",
                                      "class": "OpenStackDomainManager",
                                      "poll": False},
                        "UN": {"module": "escape.adapt.components",
                               "class": "UnifiedNodeDomainManager",
                               "poll": False},
                        "DOCKER": {"module": "escape.adapt.components",
                                   "class": "DockerDomainManager",
                                   "poll": False},
                        "SDN": {"module": "escape.adapt.components",
                                "class": "SDNDomainManager", "poll": False}},
       "infrastructure": {  # Infrastructure Layer
                            "NETWORK-OPTS": None,  # Additional opts for Mininet
                            "TOPO": "escape-mn-topo.nffg",  # relative to ext/
                            "FALLBACK-TOPO": {"module": "escape.infr.topology",
                                              "class":
                                                "FallbackDynamicTopology"},
                            "SDN-TOPO": "sdn-topo.nffg",  # relative to ext/
                            "SHUTDOWN-CLEAN": True},
       "additional-config-file": "escape.config"}  # relative to ext/


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
    if not sub_folder.startswith('.') and sub_folder not in (
         "pox", "OpenYuma", "Unify_ncagent") and os.path.isdir(abs_sub_folder):
      if abs_sub_folder not in sys.path:
        sys.path.insert(0, abs_sub_folder)
        core.getLogger().debug("Add dependency: %s" % abs_sub_folder)
      else:
        core.getLogger().debug("Dependency: %s already added." % abs_sub_folder)


# Detect and add dependency directories
add_dependencies()

from escape.util.config import ESCAPEConfig
# Define global configuration and try to load additions from file
CONFIG = ESCAPEConfig(cfg).load_config()
