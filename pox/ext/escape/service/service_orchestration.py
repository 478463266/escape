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


class ServiceOrchestrator(object):
  """
  Main class for the actual Service Graph processing
  """

  def __init__ (self):
    pass


class SGManager(object):
  """
  Store, handle and organize Service Graphs

  Currently it just stores SGs in one central place
  """
  service_graphs = dict()

  def __init__ (self):
    super(SGManager, self).__init__()

  def save (self, sg):
    """
    Save SG in a dict
    :return computed id of givven SG
    """
    graph_id = len(self.service_graphs)
    self.service_graphs[graph_id] = sg
    return graph_id

  def get (self, graph_id):
    """
    Return service graph with given id
    """
    return self.service_graphs[graph_id]


class VirtualResourceManager(object):
  """
  Support Service Graph mapping, follows the used virtual resources according to
  the Service Graph(s) in effect
  """

  def __init__ (self):
    pass


class NFIBManager(object):
  """
  Manage the handling of Network Function Information Base
  """

  def __init__ (self):
    pass