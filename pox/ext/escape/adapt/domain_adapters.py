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
other different domains

:class:`AbstractDomainAdapter` contains general logic for actual Adapters

:class:`MininetDomainAdapter` implements Mininet related functionality

:class:`POXDomainAdapter` implements POX related functionality

:class:`OpenStackDomainAdapter` implements OpenStack related functionality

:class:`VNFStarterManager` is a wrapper class for vnf_starter NETCONF module
"""
from escape.adapt import log as log
from escape.util.netconf import AbstractNETCONFAdapter
from pox.lib.revent import Event, EventMixin


class DomainChangedEvent(Event):
  """
  Event class for signaling some kind of change(s) in specific domain
  """

  def __init__ (self, domain, cause, data=None):
    """
    Init event object

    :param domain: domain name
    :type domain: str
    :param cause: type of the domain change
    :type cause: str
    :param data: data connected to the change (optional)
    :type data: object
    :return: None
    """
    super(DomainChangedEvent, self).__init__()


class AbstractDomainAdapter(EventMixin):
  """
  Abstract class for different domain adapters

  Follows the Adapter design pattern (Adaptor base class)
  """
  # Events raised by this class
  _eventMixin_events = {DomainChangedEvent}

  def __init__ (self):
    """
    Init
    """
    super(AbstractDomainAdapter, self).__init__()

  def install (self, nffg):
    """
    Intall domain specific part of a mapped NFFG

    :param nffg: domain specific slice of mapped NFFG
    :type nffg: NFFG
    :return: None
    """
    raise NotImplementedError("Derived class have to override this function")

  def notify_change (self):
    """
    Notify other components (ControllerAdapter) about changes in specific domain
    """
    raise NotImplementedError("Derived class have to override this function")


class MininetDomainAdapter(AbstractDomainAdapter):
  """
  Adapter class to handle communication with Mininet

  .. warning::
    Not implemented yet!
  """

  def __init__ (self):
    """
    Init
    """
    super(MininetDomainAdapter, self).__init__()
    log.debug("Init %s" % self.__class__.__name__)

  def install (self, nffg):
    log.info("Install Mininet domain part...")
    # TODO - implement
    pass

  def notify_change (self):
    # TODO - implement
    pass


class POXDomainAdapter(AbstractDomainAdapter):
  """
  Adapter class to handle communication with POX OpenFlow controller

  .. warning::
    Not implemented yet!
  """

  def __init__ (self):
    """
    Init
    """
    super(POXDomainAdapter, self).__init__()
    log.debug("Init %s" % self.__class__.__name__)

  def install (self, nffg):
    log.info("Install POX domain part...")
    # TODO - implement
    pass

  def notify_change (self):
    # TODO - implement
    pass


class OpenStackDomainAdapter(AbstractDomainAdapter):
  """
  Adapter class to handle communication with OpenStack

  .. warning::
    Not implemented yet!
  """

  def __init__ (self):
    """
    Init
    """
    super(OpenStackDomainAdapter, self).__init__()
    log.debug("Init %s" % self.__class__.__name__)

  def install (self, nffg):
    log.info("Install OpenStack domain part...")
    # TODO - implement
    pass

  def notify_change (self):
    # TODO - implement
    pass


class VNFStarterManager(AbstractNETCONFAdapter):
  """
  This class is devoted to provide NETCONF specific functions for vnf_starter
  module. Documentation is transferred from vnf_starter.yang

  .. seealso::
      vnf_starter.yang

  This class is devoted to start and stop CLICK-based VNFs that will be
  connected to a mininet switch.
  """
  # RPC namespace
  RPC_NAMESPACE = u'http://csikor.tmit.bme.hu/netconf/unify/vnf_starter'

  def __init__ (self, **kwargs):
    super(VNFStarterManager, self).__init__(**kwargs)
    log.debug("Init %s" % self.__class__.__name__)

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
    is UP_AND_RUNNING"

    :param vnf_id: VNF ID
    :type vnf_id: str
    :return: reply data
    :raises: RPCError, OperationError, TransportError
    """
    params = {"vnf_id": vnf_id}
    log.debug("Call getVNFInfo...")
    return self.call_RPC('getVNFInfo', **params)