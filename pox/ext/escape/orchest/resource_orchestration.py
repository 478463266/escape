# Copyright 2015 Janos Czentye
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
from escape.orchest.nffg_mapping import ResourceOrchestrationMapper
from escape.orchest.virtualization_management import VirtualizerManager
from escape.orchest import log as log


class ResourceOrchestrator(object):
  """
  Main class for the handling of the Orchestration-level mapping functions
  """

  def __init__ (self):
    super(ResourceOrchestrator, self).__init__()
    log.debug("Init %s" % self.__class__.__name__)
    self.nffg_manager = NFFGManager()
    self.virtualizer_manager = VirtualizerManager()
    self.nffg_mapper = ResourceOrchestrationMapper()

  def instantiate_nffg (self, nffg):
    """
    Start NF-FG instantiation
    """
    log.debug("Invoke %s to initiate NF-FG" % self.__class__.__name__)
    # Store newly created NF-FG
    self.nffg_manager.save(nffg)
    # Get Domain Virtualizer to aquire global domain view
    global_resource = self.virtualizer_manager.get_domain_view()
    # Run Nf-FG mapping algorithm
    mapped_nffg = self.nffg_mapper.orchestrate(nffg, global_resource)
    log.debug("NF-FG initiation is finished by %s" % self.__class__.__name__)
    return mapped_nffg


class NFFGManager(object):
  """
  Store, handle and organize Network Function Forwarding Graphs
  """
  nffgs = dict()

  def __init__ (self):
    super(NFFGManager, self).__init__()
    log.debug("Init %s" % self.__class__.__name__)

  def save (self, nffg):
    """
    Save NF-FG in a dict

    :param nffg: Network Function Forwarding Graph
    :return: computed id of given NF-FG
    """
    nffg.id = len(self.nffgs)
    self.nffgs[nffg.id] = nffg
    log.debug(
      "NF-FG is saved by %s with id: %s" % (self.__class__.__name__, nffg.id))
    return nffg.id

  def get (self, nffg_id):
    """
    Return NF-FG with given id
    """
    return self.nffgs.get(nffg_id, default=None)