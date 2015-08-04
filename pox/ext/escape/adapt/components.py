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
Contains Adapter classes which represent the connections between ESCAPEv2 and
other different domains.
"""
from requests.exceptions import ConnectionError, HTTPError, Timeout

from escape.adapt import log as log
from escape.infr.il_API import InfrastructureLayerAPI
from escape.util.domain import *
from escape.util.netconf import AbstractNETCONFAdapter
from escape.util.pox_extension import ExtendedOFConnectionArbiter, \
  OpenFlowBridge


class POXDomainAdapter(AbstractDomainAdapter):
  """
  Adapter class to handle communication with internal POX OpenFlow controller.

  Can be used to define a controller (based on POX) for other external domains.
  """
  name = "POX"

  def __init__ (self, name=None, address="127.0.0.1", port=6653):
    """
    Initialize attributes, register specific connection Arbiter if needed and
    set up listening of OpenFlow events.

    :param name: name used to register component ito ``pox.core``
    :type name: str
    :param address: socket address (default: 127.0.0.1)
    :type address: str
    :param port: socket port (default: 6653)
    :type port: int
    """
    log.debug("Init %s with ID: %s" % (self.__class__.__name__, name))
    super(POXDomainAdapter, self).__init__()
    # Set an OpenFlow nexus as a source of OpenFlow events
    self.openflow = OpenFlowBridge()
    self.controller_address = (address, port)
    # Initiate our specific connection Arbiter
    arbiter = ExtendedOFConnectionArbiter.activate()
    # Register our OpenFlow event source
    arbiter.add_connection_listener(self.controller_address, self.openflow)
    # Launch OpenFlow connection handler if not started before with given name
    # launch() return the registered openflow module which is a coop Task
    from pox.openflow.of_01 import launch

    of = launch(name=name, address=address, port=port)
    # Start listening for OpenFlow connections
    of.start()
    self.task_name = name if name else "of_01"
    of.name = self.task_name
    # register OpenFlow event listeners
    self.openflow.addListeners(self)
    log.debug("Start listening %s domain..." % self.name)

  def filter_connections (self, event):
    """
    Handle which connection should be handled by this Adapter class.

    This adapter accept every OpenFlow connection by default.

    :param event: POX internal ConnectionUp event (event.dpid, event.connection)
    :type event: :class:`pox.openflow.ConnectionUp`
    :return: True os False obviously
    :rtype: bool
    """
    return True

  def _handle_ConnectionUp (self, event):
    """
    Handle incoming OpenFlow connections.
    """
    log.debug("Handle connection by %s" % self.task_name)
    if self.filter_connections(event):
      event = DomainChangedEvent(domain=self.name,
                                 cause=DomainChangedEvent.type.DEVICE_UP,
                                 data={"DPID": event.dpid})
      self.raiseEventNoErrors(event)

  def _handle_ConnectionDown (self, event):
    """
    Handle disconnected device.
    """
    log.debug("Handle disconnection by %s" % self.task_name)
    event = DomainChangedEvent(domain=self.name,
                               cause=DomainChangedEvent.type.DEVICE_DOWN,
                               data={"DPID": event.dpid})
    self.raiseEventNoErrors(event)

  def install_routes (self, routes):
    """
    Install routes related to the managed domain. Translates the generic
    format of the routes into OpenFlow flow rules.

    Routes are computed by the ControllerAdapter's main adaptation algorithm.

    :param routes: list of routes
    :type routes: :any:`NFFG`
    :return: None
    """
    log.info("Install POX domain part: routes...")
    # TODO - implement
    pass


class MininetDomainAdapter(AbstractDomainAdapter, VNFStarterAPI):
  """
  Adapter class to handle communication with Mininet domain.

  Implement VNF managing API using direct access to the
  :class:`mininet.net.Mininet` object.
  """
  # Events raised by this class
  _eventMixin_events = {DomainChangedEvent, DeployEvent}
  name = "MININET"

  def __init__ (self, mininet=None):
    """
    Init.

    :param mininet: set pre-defined network (optional)
    :type mininet: :class:`ESCAPENetworkBridge`
    """
    log.debug("Init %s" % self.__class__.__name__)
    # Call base constructors directly to avoid super() and MRO traps
    AbstractDomainAdapter.__init__(self)
    if not mininet:
      from pox import core

      if core.core.hasComponent(InfrastructureLayerAPI._core_name):
        mininet = core.core.components[
          InfrastructureLayerAPI._core_name].topology
        if mininet is None:
          log.error("Unable to get emulated network reference!")
    self.mininet = mininet  # wrapper class for emulated Mininet network

  def check_domain_is_up (self):
    """
    Checker function for domain polling.
    """
    return self.mininet.started

  def get_topology_description (self):
    """
    Return with the topology description as an :any:`NFFG`.

    :return: the emulated topology description
    :rtype: :any:`NFFG`
    """
    return self.mininet.topo_desc if self.mininet.started else None

  def initiate_VNFs (self, nffg_part):
    log.info("Install Mininet domain part: initiate VNFs...")
    # TODO - implement
    self.raiseEventNoErrors(DeployEvent, nffg_part)

  def stopVNF (self, vnf_id):
    # TODO - implement
    pass

  def getVNFInfo (self, vnf_id=None):
    # TODO - implement
    pass

  def disconnectVNF (self, vnf_id, vnf_port):
    # TODO - implement
    pass

  def startVNF (self, vnf_id):
    # TODO - implement
    pass

  def connectVNF (self, vnf_id, vnf_port, switch_id):
    # TODO - implement
    pass

  def initiateVNF (self, vnf_type=None, vnf_description=None, options=None):
    # TODO - implement
    pass


class VNFStarterAdapter(AbstractNETCONFAdapter, AbstractDomainAdapter,
                        VNFStarterAPI):
  """
  This class is devoted to provide NETCONF specific functions for vnf_starter
  module. Documentation is transferred from `vnf_starter.yang`.

  This class is devoted to start and stop CLICK-based VNFs that will be
  connected to a mininet switch.

  Follows the MixIn design pattern approach to support NETCONF functionality.
  """
  # RPC namespace
  RPC_NAMESPACE = u'http://csikor.tmit.bme.hu/netconf/unify/vnf_starter'
  # Adapter name used in CONFIG and ControllerAdapter class
  name = "VNFStarter"

  def __init__ (self, **kwargs):
    """
    Init.

    :param server: server address
    :type server: str
    :param port: port number
    :type port: int
    :param username: username
    :type username: str
    :param password: password
    :type password: str
    :param timeout: connection timeout (default=30)
    :type timeout: int
    :return:
    """
    # Call base constructors directly to avoid super() and MRO traps
    AbstractNETCONFAdapter.__init__(self, **kwargs)
    AbstractDomainAdapter.__init__(self)
    log.debug("Init VNFStarterAdapter")

  # RPC calls starts here

  def initiateVNF (self, vnf_type=None, vnf_description=None, options=None):
    """
    This RCP will start a VNF.

    0. initiate new VNF (initiate datastructure, generate unique ID)
    1. set its arguments (control port, control ip, and VNF type/command)
    2. returns the connection data, which from the vnf_id is the most important

    :param vnf_type: pre-defined VNF type (see in vnf_starter/available_vnfs)
    :type vnf_type: str
    :param vnf_description: Click description if there are no pre-defined type
    :type vnf_description: str
    :param options: unlimited list of additional options as name-value pairs
    :type options: collections.OrderedDict
    :return: RPC reply data
    :raises: RPCError, OperationError, TransportError
    """
    params = locals()
    del params['self']
    log.debug("Call initiateVNF...")
    return self.call_RPC("initiateVNF", **params)

  def connectVNF (self, vnf_id, vnf_port, switch_id):
    """
    This RPC will practically start and connect the initiated VNF/CLICK to
    the switch.

    0. create virtualEthernet pair(s)
    1. connect either end of it (them) to the given switch(es)

    This RPC is also used for reconnecting a VNF. In this case, however,
    if the input fields are not correctly set an error occurs

    :param vnf_id: VNF ID (mandatory)
    :type vnf_id: str
    :param vnf_port: VNF port (mandatory)
    :type vnf_port: str
    :param switch_id: switch ID (mandatory)
    :type switch_id: str
    :return: Returns the connected port(s) with the corresponding switch(es).
    :raises: RPCError, OperationError, TransportError
    """
    params = locals()
    del params['self']
    log.debug("Call connectVNF...")
    return self.call_RPC("connectVNF", **params)

  def disconnectVNF (self, vnf_id, vnf_port):
    """
    This RPC will disconnect the VNF(s)/CLICK(s) from the switch(es).

    0. ip link set uny_0 down
    1. ip link set uny_1 down
    2. (if more ports) repeat 1. and 2. with the corresponding data

    :param vnf_id: VNF ID (mandatory)
    :type vnf_id: str
    :param vnf_port: VNF port (mandatory)
    :type vnf_port: str
    :return: reply data
    :raises: RPCError, OperationError, TransportError
    """
    params = locals()
    del params['self']
    log.debug("Call disconnectVNF...")
    return self.call_RPC("disconnectVNF", **params)

  def startVNF (self, vnf_id):
    """
    This RPC will actually start the VNF/CLICK instance.

    :param vnf_id: VNF ID (mandatory)
    :type vnf_id: str
    :return: reply data
    :raises: RPCError, OperationError, TransportError
    """
    params = locals()
    del params['self']
    log.debug("Call startVNF...")
    return self.call_RPC("startVNF", **params)

  def stopVNF (self, vnf_id):
    """
    This RPC will gracefully shut down the VNF/CLICK instance.

    0. if disconnect() was not called before, we call it
    1. delete virtual ethernet pairs
    2. stop (kill) click
    3. remove vnf's data from the data structure

    :param vnf_id: VNF ID (mandatory)
    :type vnf_id: str
    :return: reply data
    :raises: RPCError, OperationError, TransportError
    """
    params = locals()
    del params['self']
    log.debug("Call stopVNF...")
    return self.call_RPC("stopVNF", **params)

  def getVNFInfo (self, vnf_id=None):
    """
    This RPC will send back all data of all VNFs that have been initiated by
    this NETCONF Agent. If an input of vnf_id is set, only that VNF's data
    will be sent back. Most of the data this RPC replies is used for DEBUG,
    however 'status' is useful for indicating to upper layers whether a VNF
    is UP_AND_RUNNING.

    :param vnf_id: VNF ID
    :type vnf_id: str
    :return: reply data
    :raises: RPCError, OperationError, TransportError
    """
    params = {"vnf_id": vnf_id}
    log.debug("Call getVNFInfo...")
    return self.call_RPC('getVNFInfo', **params)


class OpenStackRESTAdapter(AbstractRESTAdapter, AbstractDomainAdapter,
                           OpenStackAPI):
  """
  This class is devoted to provide REST specific functions for OpenStack domain.
  """
  # HTTP methods
  GET = "GET"
  POST = "POST"

  def __init__ (self, url):
    """
    Init.

    :param url: OpenStack RESTful API URL
    :type url: str
    """
    log.debug("Init %s" % self.__class__.__name__)
    AbstractRESTAdapter.__init__(self, base_url=url)
    log.debug("OpenStack base URL is set to %s" % url)
    AbstractDomainAdapter.__init__(self)

  @property
  def URL (self):
    return self._base_url

  def ping (self):
    """
    .. seealso::
      :func:`OpenStackAPI.ping() <escape.util.domain.OpenStackAPI.ping>`
    """
    try:
      return self.send_request(self.GET, 'ping')
    except ConnectionError:
      log.warning("OpenStack agent (%s) is not reachable!" % self._base_url)
    except Timeout:
      log.warning("OpenStack agent (%s) not responding!" % self._base_url)
    except HTTPError as e:
      log.warning(
        "OpenStack agent responded with an error during 'ping': %s" % e.message)

  def get_config (self):
    """
    .. seealso::
      :func:`OpenStackAPI.get_config()
      <escape.util.domain.OpenStackAPI.get_config>`
    """
    try:
      data = self.send_request(self.POST, 'get-config')
    except ConnectionError:
      log.warning("OpenStack agent (%s) is not reachable!" % self._base_url)
      return None
    except Timeout:
      log.warning("OpenStack agent (%s) not responding!" % self._base_url)
      return None
    except HTTPError as e:
      log.warning(
        "OpenStack agent responded with an error during 'get-config': %s" %
        e.message)
      return None
    return NFFG.parse(data)

  def edit_config (self, config):
    """
    .. seealso::
      :func:`OpenStackAPI.edit_config()
      <escape.util.domain.OpenStackAPI.edit_config>`
    """
    if isinstance(config, NFFG):
      config = NFFG.dump(config)
    elif not isinstance(config, (str, unicode)):
      raise RuntimeError("Not supported config format for 'edit-config'!")
    try:
      self.send_request(self.POST, 'edit-config', config)
    except ConnectionError:
      log.warning("OpenStack agent (%s) is not reachable: %s" % self._base_url)
      return None
    except HTTPError as e:
      log.warning(
        "OpenStack agent responded with an error during 'get-config': %s" %
        e.message)
      return None
    return self._response.status_code


class InternalDomainManager(AbstractDomainManager):
  """
  Manager class to handle communication with internally emulated network.

  .. note::
    Uses :class:`MininetDomainAdapter` for managing the emulated network and
    :class:`POXDomainAdapter` for controlling the network.
  """
  name = "INTERNAL"

  def __init__ (self, **kwargs):
    """
    Init
    """
    log.debug("Init %s" % self.__class__.__name__)
    super(InternalDomainManager, self).__init__()
    if 'poll' in kwargs:
      self._poll = kwargs['poll']
    else:
      self._poll = False
    self.controller = None  # DomainAdapter for POX - POXDomainAdapter
    self.network = None  # DomainAdapter for Mininet - MininetDomainAdapter
    self.remote = None  # NETCONF communication - VNFStarterAdapter
    self._detected = None
    self.topology = None  # Description of the domain topology as an NFFG

  def finit (self):
    """
    Stop polling and release dependent components.

    :return: None
    """
    self.stop_polling()
    del self.controller
    del self.network
    del self.remote

  def init (self, configurator, **kwargs):
    """
    Initialize Internal domain manager.

    :return: None
    """
    self.controller = configurator.load_component("POX")
    self.network = configurator.load_component("MININET")
    self.remote = configurator.load_component("VNFStarter")
    # Skip to start polling is it's set
    if not self._poll:
      # Try to request/parse/update Mininet topology
      if not self._detect_topology():
        log.warning("%s domain not confirmed during init!" % self.name)
    else:
      log.debug("Start polling %s domain..." % self.name)
      self.start_polling(self.POLL_INTERVAL)

  @property
  def controller_name (self):
    return self.controller.task_name

  def _detect_topology (self):
    """
    Check the undetected topology is up or not.

    :return: detected or not
    :rtype: bool
    """
    if self.network.check_domain_is_up():
      log.info("%s domain confirmed!" % self.name)
      self._detected = True
      log.info("Updating resource information from %s domain..." % self.name)
      topo_nffg = self.network.get_topology_description()
      if topo_nffg:
        log.debug("Set received NFFG(name: %s)..." % topo_nffg.name)
        self.topology = topo_nffg
        # TODO updating DOV
      else:
        log.warning(
          "Resource info is missing! Infrastructure layer is inconsistent "
          "state!")
    return self._detected

  def poll (self):
    """
    Poll the defined Internal domain based on Mininet.

    :return:
    """
    if not self._detected:
      self._detect_topology()
    else:
      self.update_resource_info()

  def update_resource_info (self):
    """
    Update the resource information of this domain with the requested
    configuration.

    :return: None
    """
    topo_nffg = self.network.get_topology_description()
    # TODO - implement actual updating
    # update local topology
    # update DoV

  def install_nffg (self, nffg_part):
    """
    Install an :any:`NFFG` related to the internal domain.

    Split given :any:`NFFG` to a set of NFs need to be initiated and a set of
    routes/connections between the NFs.

    :param nffg_part: NF-FG need to be deployed
    :type nffg_part: :any:`NFFG`
    :return: None
    """
    log.info("Install Internal domain part...")
    # TODO - implement
    self.network.initiate_VNFs(nffg_part=())
    # TODO ...
    self.controller.install_routes(routes=())


class OpenStackDomainManager(AbstractDomainManager):
  """
  Adapter class to handle communication with OpenStack domain.
  """
  name = "OPENSTACK"

  def __init__ (self, **kwargs):
    """
    Init
    """
    log.debug("Init %s" % self.__class__.__name__)
    super(OpenStackDomainManager, self).__init__()
    if 'poll' in kwargs:
      self._poll = kwargs['poll']
    else:
      self._poll = False
    self.rest_adapter = None
    self._detected = None

  def finit (self):
    """
    Stop polling and release dependent components.

    :return: None
    """
    self.stop_polling()
    del self.rest_adapter

  def init (self, configurator, **kwargs):
    """
    Initialize OpenStack domain manager.

    :return: None
    """
    self.rest_adapter = configurator.load_component("OpenStack-REST")
    # Skip to start polling is it's set
    if not self._poll:
      return
    log.debug("Start polling %s domain..." % self.name)
    self.start_polling()

  def poll (self):
    """
    Poll the defined OpenStack domain agent. Handle different connection
    errors and go to slow/rapid poll. When an agent is (re)detected update
    the current resource information.
    """
    try:
      if not self._detected:
        # Trying to request config
        raw_data = self.rest_adapter.send_request(self.rest_adapter.POST,
                                                  'get-config')
        # If no exception -> success
        log.info("%s agent detected!" % self.name)
        self._detected = True
        log.info("Updating resource information from %s domain..." % self.name)
        self.update_resource_info(raw_data)
        self.restart_polling()
      else:
        # Just ping the agent if it's alive. If exception is raised -> problem
        self.rest_adapter.send_request(self.rest_adapter.GET, 'ping')
    except ConnectionError:
      if self._detected is None:
        # detected = None -> First try
        log.warning("%s agent is not detected! Keep trying..." % self.name)
        self._detected = False
      elif self._detected:
        # Detected before -> lost connection = big Problem
        log.warning(
          "Lost connection with %s agent! Go slow poll..." % self.name)
        self._detected = False
        self.restart_polling()
      else:
        # No success but not for the first try -> keep trying silently
        pass
    except Timeout:
      if self._detected is None:
        # detected = None -> First try
        log.warning("%s agent not responding!" % self.name)
        self._detected = False
      elif self._detected:
        # Detected before -> not responding = big Problem
        log.warning(
          "Detected %s agent not responding! Go slow poll..." % self.name)
        self._detected = False
        self.restart_polling()
      else:
        # No success but not for the first try -> keep trying silently
        pass
    except HTTPError:
      raise

  def update_resource_info (self):
    """
    Update the resource information if this domain with the requested
    configuration. The config attribute is the raw date from request. This
    function's responsibility to parse/convert/save the data effectively.

    :param raw_data: polled raw data
    :type raw_data: str
    :return: None
    """
    # TODO - implement actual updating
    pass

  def install_nffg (self, nffg_part):
    log.info("Install OpenStack domain part...")
    # TODO - implement
    pass


class DockerDomainManager(AbstractDomainManager):
  """
  Adapter class to handle communication component in a Docker domain.

  .. warning::
    Not implemented yet!
  """
  name = "DOCKER"

  def __init__ (self):
    """
    Init
    """
    log.debug("Init %s" % self.__class__.__name__)
    super(DockerDomainManager, self).__init__()

  def install_nffg (self, nffg_part):
    log.info("Install Docker domain part...")
    # TODO - implement
    pass
