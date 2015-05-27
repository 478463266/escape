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
Contains classes relevant to the main adaptation function of the Controller
Adaptation Sublayer
"""
import importlib
import weakref

from escape import CONFIG
from escape.adapt import ADAPTATION_LAYER_NAME
from escape.infr import LAYER_NAME as infr_name
from escape.orchest.virtualization_mgmt import AbstractVirtualizer
from escape.adapt.domain_adapters import AbstractDomainAdapter
from escape.adapt import log as log
from escape.util.nffg import NFFG


class ControllerAdapter(object):
  """
  Higher-level class for :any:`NFFG` adaptation
  between multiple domains
  """
  # Default adapters
  _domains = {}

  def __init__ (self, layer_API, lazy_load=True, with_infr=False, remote=True):
    """
    Initialize Controller adapter

    For domain adapters the ControllerAdapter checks the CONFIG first
    If there is no adapter defined explicitly then initialize the default
    Adapter class stored in `_defaults`

    .. warning::
      Adapter classes must be subclass of AbstractDomainAdapter

    .. note::
      Arbitrary domain adapters is searched in
      :mod:`escape.adapt.domain_adapters`

    :param layer_API: layer API instance
    :type layer_API: :any:`ControllerAdaptationAPI`
    :param lazy_load: load adapters only at first reference (default: True)
    :type lazy_load: bool
    :param with_infr: using emulated infrastructure (default: False)
    :type with_infr: bool
    :param remote: use NETCONF RPCs or direct access (default: False)
    :type remote: bool
    """
    log.debug("Init ControllerAdapter")
    super(ControllerAdapter, self).__init__()
    # Set a weak reference to avoid circular dependencies
    self._layer_API = weakref.proxy(layer_API)
    self._lazy_load = lazy_load
    self._with_infr = with_infr
    if not lazy_load:
      # Initiate adapters from CONFIG
      self.__init_defaults()
    elif with_infr:
      # Initiate default internal adapter if needed.
      try:
        if CONFIG[infr_name]["LOADED"]:
          # Set adapters for InternalDomainManager
          # Set OpensFlow route handler
          controller = self.__load_adapter("POX")
          # Set emulated network initiator/handler/manager
          network = self.__load_adapter("MININET")
          # Set NETCONF handling capability if needed
          remote = self.__load_adapter('VNFStarter', **
          CONFIG[ADAPTATION_LAYER_NAME]['VNFStarter'][
            'agent']) if remote else None
          # Set internal domain manager
          self._domains['INTERNAL'] = self.__load_adapter("INTERNAL",
                                                          controller=controller,
                                                          network=network,
                                                          remote=remote)
      except KeyError as e:
        log.error(
          "Got KeyError during initialization of InternalDomainManager: %s", e)
    else:
      # Other adapters will be created right after the first reference to them
      # POX seems to be the only reasonable choice as a default adapter
      self.__load_adapter("POX")
    # Set virtualizer-related components
    self.domainResManager = DomainResourceManager()

  def __getattr__ (self, item):
    """
    Expose doamin managers with it's names as an attribute of this class

    :param item: name of the manager defined in it's class
    :type item: str
    :return: given domain manager
    :rtype: AbstractDomainAdapter
    """
    try:
      if not item.startswith('__'):
        return self._domains[item]
    except KeyError:
      if self._lazy_load:
        self._domains[item] = self.__load_adapter(item)
        return self._domains[item]
      else:
        raise AttributeError("No adapter is defined with the name: %s" % item)

  def __load_adapter (self, name, from_config=True, **kwargs):
    """
    Load given adapter.

    :param name: adapter's name
    :type name: str
    :param kwargs: adapter's initial parameters
    :type kwargs: dict
    :return: initiated adapter
    :rtype: :any:`AbstractDomainAdapter`
    """
    try:
      if from_config:
        adapter_class = getattr(
          importlib.import_module("escape.adapt.domain_adapters"),
          CONFIG[ADAPTATION_LAYER_NAME][name]['class'])
      else:
        adapter_class = getattr(
          importlib.import_module("escape.adapt.domain_adapters"), name)
      adapter = adapter_class(**kwargs)
      # Set up listeners for e.g. DomainChangedEvents
      adapter.addListeners(self)
      # Set up listeners for DeployNFFGEvent
      adapter.addListeners(self._layer_API)
      return adapter
    except KeyError as e:
      log.error(
        "Configuration of '%s' is missing. Skip initialization!" % e.args[0])
    except AttributeError:
      log.error("%s is not found. Skip adapter initialization!" %
                CONFIG[ADAPTATION_LAYER_NAME][name]['class'])

  def __init_defaults (self):
    """
    Init default adapters
    """
    # very dummy initialization
    # TODO - improve
    for name in ('POX', 'INTERNAL'):
      self._domains[name] = self.__load_adapter(name)

  def install_nffg (self, mapped_nffg):
    """
    Start NF-FG installation

    Process given :any:`NFFG`, slice information based on domains an invoke
    domain adapters to install domain specific parts

    :param mapped_nffg: mapped NF-FG instance which need to be installed
    :type mapped_nffg: NFFG
    :return: None or internal domain NFFG part
    """
    log.debug("Invoke %s to install NF-FG" % self.__class__.__name__)
    # TODO - implement
    # TODO - no NFFG split just very dummy cycle
    if self._with_infr:
      log.debug("Delegate mapped NFFG to Internal domain manager...")
      self.internal_manager.install_nffg(mapped_nffg)
    else:
      for name, adapter in self._domains.iteritems():
        log.debug("Delegate mapped NFFG to %s domain adapter..." % name)
        adapter.install_routes(mapped_nffg)
    log.debug("NF-FG installation is finished by %s" % self.__class__.__name__)

  def _handle_DomainChangedEvent (self, event):
    """
    Handle DomainChangedEvents, process changes and store relevant information
    in DomainResourceManager
    """
    pass

  def _slice_into_domains (self, nffg):
    """
    Slice given :any:`NFFG` into separate parts

    :param nffg: mapped NFFG object
    :type nffg: NFFG
    :return: sliced parts
    :rtype: dict
    """
    pass


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
    log.debug("Init DomainVirtualizer")
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
    log.debug("Init DomainResourceManager")
    self._dov = DomainVirtualizer(self)

  @property
  def dov (self):
    """
    Getter for :class:`DomainVirtualizer`

    :return: Domain Virtualizer
    :rtype: ESCAPEVirtualizer
    """
    return self._dov

  def update_resource_usage (self, data):
    """
    Update global resource database with resource usage relevant to installed
    components, routes, VNFs, etc.

    :param data: usage data
    :type data: dict
    :return: None
    """
    pass
