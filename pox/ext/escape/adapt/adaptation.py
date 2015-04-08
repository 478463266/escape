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
"""
Contain classes relevant to the main adaptation function of the Controll
Adaptation Sublayer

:class:`ControllerAdapter` implements the centralized functionality of
high-level adaptation and installation of :class:`NFFG <escape.util.nffg.NFFG>`

:class:`DomainVirtualizer` implement the standard virtualization/generalization
logic of the Resource Orchestration Sublayer

:class:`DomainResourceManager` stores and handles the global Virtualizer
"""
import weakref

from escape import CONFIG
from escape.orchest.virtualization_mgmt import AbstractVirtualizer
from escape.adapt.domain_adapters import POXDomainAdapter, \
  MininetDomainAdapter, \
  OpenStackDomainAdapter
from escape.adapt import log as log
from escape.util.nffg import NFFG


class ControllerAdapter(object):
  """
  Higher-level class for :class:`NFFG <escape.util.nffg.NFFG>` adaptation
  between multiple domains
  """

  def __init__ (self):
    """
    Init
    """
    super(ControllerAdapter, self).__init__()
    log.debug("Init %s" % self.__class__.__name__)
    self.domainResManager = DomainResourceManager()
    self.poxAdapter = POXDomainAdapter() if CONFIG['CAS']['POX'] else None
    self.mnAdapter = MininetDomainAdapter() if CONFIG['CAS']['MN'] else None
    self.osAdapter = OpenStackDomainAdapter() if CONFIG['CAS']['OS'] else None

  def install_nffg (self, mapped_nffg):
    """
    Start NF-FG installation

    :param mapped_nffg: mapped NF-FG instance which need to be installed
    :type mapped_nffg: NFFG
    :return: None
    """
    log.debug("Invoke %s to install NF-FG" % self.__class__.__name__)
    # TODO - implement
    log.debug("NF-FG installation is finished by %s" % self.__class__.__name__)


class DomainVirtualizer(AbstractVirtualizer):
  """
  Specific Virtualizer class for global domain virtualization

  Implement the same interface as :class:`AbstractVirtualizer
  <escape.orchest.virtualization_mgmt.AbstractVirtualizer>`
  """

  def __init__ (self, domainResManager):
    """
    Init

    :param domainResManager: domain resource manager
    :type domainResManager: DomainResourceManager
    :return: None
    """
    super(DomainVirtualizer, self).__init__()
    log.debug("Init %s" % self.__class__.__name__)
    # Garbage-collector safe
    self.domainResManager = weakref.proxy(domainResManager)

  def get_resource_info (self):
    """
    Return the global resource info represented this class

    :return: global resource info
    :rtype: NFFG
    """
    # TODO - implement - possibly don't store anything just convert??
    log.debug("Request global resource info...")
    return NFFG()


class DomainResourceManager(object):
  """
  Handle and store global resources
  """

  def __init__ (self):
    """
    Init
    """
    super(DomainResourceManager, self).__init__()
    log.debug("Init %s" % self.__class__.__name__)
    self._dov = DomainVirtualizer(self)

  @property
  def dov (self):
    """
    Getter for :class:`DomainVirtualizer`

    :return: Domain Virtualizer
    :rtype: ESCAPEVirtualizer
    """
    return self._dov