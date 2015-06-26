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
Unifying package for ESCAPEv2 functions

`CONFIG` contains the ESCAPEv2 dependent configuration such as the concrete
RequestHandler and strategy classes, the initial Adapter classes, etc.
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
__status__ = "Prototype"

# Default configuration object which contains static and running
# configuration for Layer APIs, DomainManagers, Adapters and other components
cfg = {'service': {  # Service Adaptation Sublayer
                     'STRATEGY': {'module': 'escape.service.sas_mapping',
                                  'class': 'DefaultServiceMappingStrategy',
                                  'THREADED': True}},
       'orchestration': {  # Resource Orchestration Sublayer
                           'STRATEGY': {'module': 'escape.orchest.ros_mapping',
                                        'class': 'ESCAPEMappingStrategy',
                                        'THREADED': True}},
       'adaptation': {  # Controller Adaptation Sublayer
                        'DEFAULTS': ('OPENSTACK',),
                        'INTERNAL': {'module': 'escape.adapt.domain_adapters',
                                     'class': "InternalDomainManager",
                                     'listener-id': "InternalOFController"},
                        'POX': {'module': 'escape.adapt.domain_adapters',
                                'class': "POXDomainAdapter"},
                        'MININET': {'module': 'escape.adapt.domain_adapters',
                                    'class': "MininetDomainAdapter"},
                        "VNFStarter": {'module': 'escape.adapt.domain_adapters',
                                       "class": "VNFStarterAdapter",
                                       "agent": {"server": "192.168.12.128",
                                                 "port": 830,
                                                 "username": "mininet",
                                                 "password": "mininet"}},
                        'OPENSTACK': {'module': 'escape.adapt.domain_adapters',
                                      'class': "OpenStackDomainAdapter"},
                        'DOCKER': {'module': 'escape.adapt.domain_adapters',
                                   'class': "DockerDomainAdapter"}},
       'infrastructure': {  # Infrastructure Layer
                            'NETWORK-OPTS': None,  # Additional opts for Mininet
                            'FALLBACK-TOPO': {'module': "escape.infr.topology",
                                              'class': "BackupTopology"}}}

from escape.util.misc import ESCAPEConfig
# Define global configuration and try to load additions from file
CONFIG = ESCAPEConfig(cfg).load_config()
