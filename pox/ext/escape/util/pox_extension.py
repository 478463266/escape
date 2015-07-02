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
Override and extend internal POX components to achieve ESCAPE-desired behaviour
"""
import nffglib
from pox.core import core
from pox.openflow import OpenFlowConnectionArbiter, OpenFlowNexus, ConnectionIn


class OpenFlowBridge(OpenFlowNexus):
  """
  Own class for listening OpenFlow event originated by one of the contained
  :class:`Connection` and sending OpenFlow messages according to DPID.

  Purpose of the class mostly fits the Bride design pattern.
  """
  pass


class ExtendedOFConnectionArbiter(OpenFlowConnectionArbiter):
  """
  Extended connection arbiter class for dispatching incoming OpenFlow
  :class:`Connection` between registered OF event originators (
  :class:`OpenFlowNexus`) according to the connection's listening address.
  """
  # core name to register the class as a OpenFlowConnectionArbiter
  _core_name = "OpenFlowConnectionArbiter"

  def __init__ (self, default=False):
    """
    Init

    :param default: inherited param
    :type default: :class:`OpenFlowNexus`
    """
    super(ExtendedOFConnectionArbiter, self).__init__(default)
    try:
      # Set original OpenFlow nexus as a last resort
      self._fallback = core.openflow
    except:
      # for safety reason
      core.getLogger().warning(
        "No default OpenFlow nexus is registered. Registering now...")
      core.core.register("openflow", OpenFlowNexus())
      self._fallback = core.openflow
      # registered nexus objects - key: (address, port)
    self._listeners = {}

  def add_connection_listener (self, address, nexus):
    """
    Helper function to register connection listeners a.k.a.
    :class:`OpenFlowNexus`.

    :param address: listened socket name in form of (address, port)
    :type address: tuple
    :param nexus: registered object
    :type nexus: :class:`OpenFlowBridge`
    :return: registered listener
    :rtype: :class:`OpenFlowBridge`
    """
    self._listeners[address] = nexus

  @classmethod
  def activate (cls):
    """
    Register this component into ``pox.core`` and replace already registered
    Arbiter.

    :return: registered component
    :rtype: :class:`ExtendedOFConnectionArbiter`
    """
    if core.hasComponent(cls._core_name):
      # If the registered arbiter is our extended one skip registration
      if isinstance(core.components[cls._core_name], cls):
        return
      del core.components[cls._core_name]
    return core.core.registerNew(cls)

  def getNexus (self, connection):
    """
    Return registered connection listener or default ``core.openflow``.

    Fires ConnectionIn event.

    :param connection: incoming connection object
    :type connection: :class:`Connection`
    :return: OpenFlow event originator object
    :rtype: :class:`OpenFlowNexus`
    """
    event = ConnectionIn(connection)
    if self._default:
      # Set default value is exist
      event.nexus = self._default
    else:
      # No default
      con_address = connection.sock.getsockname()
      if con_address in self._listeners:
        # If there is registered listener
        event.nexus = self._listeners[con_address]
      else:
        # Fall back to core.openflow
        event.nexus = self._fallback
    self.raiseEventNoErrors(event)
    return event.nexus


class ESCAPEInteractiveHelper(object):
  """
  Extended Interactive class which add ESCAPE specific debug functions to
  POX's py module.
  """

  def __repr__ (self):
    """
    return with defined helper functions.
    """
    return "\n".join([f for f in dir(self) if not f.startswith('_')])

  @staticmethod
  def init ():
    """
    Register an ESCPAEInteractiveHelper into POX's core.
    """
    core.components['helper'] = ESCAPEInteractiveHelper()

  def ping (self):
    """
    Call the ping() function of the OpenStackRESTAdapter.
    """
    ret = core.adaptation.controller_adapter.domains.components[
      'OPENSTACK'].rest_adapter.ping()
    print "Return: ", ret

  def get_config (self):
    """
    Call the get_config() function of the OpenStackRESTAdapter.
    """
    ret = core.adaptation.controller_adapter.domains.components[
      'OPENSTACK'].rest_adapter.get_config()
    print "Return: ", ret
    print core.adaptation.controller_adapter.domains.components[
      'OPENSTACK'].rest_adapter._response.text

  def edit_config (self):
    """
    Call the edit_config() function of OpenStackRESTAdapter with the default
    config.
    """
    config = """<?xml version="1.0" ?>
    <virtualizer>
      <id>UUID-ETH-001</id>
      <name>ETH OpenStack-OpenDaylight domain</name>
      <nodes>
        <node>
          <id>UUID-01</id>
          <name>single Bis-Bis node representing the whole domain</name>
          <type>BisBis</type>
          <ports>
            <port>
              <id>0</id>
              <name>OVS-north external port</name>
              <port_type>port-abstract</port_type>
              <capability/>
            </port>
            <port>
              <id>1</id>
              <name>OVS-south external port</name>
              <port_type>port-abstract</port_type>
              <capability/>
            </port>
          </ports>
          <resources>
            <cpu>10 VCPU</cpu>
            <mem>32 GB</mem>
            <storage>5 TB</storage>
          </resources>
          <capabilities>
            <supported_NFs>
              <node>
                <id>nf_a</id>
                <name>tcp header compressor</name>
                <type>0</type>
                <ports>
                  <port>
                    <id>0</id>
                    <name>in</name>
                    <port_type>port-abstract</port_type>
                    <capability>...</capability>
                  </port>
                  <port>
                    <id>1</id>
                    <name>out</name>
                    <port_type>port-abstract</port_type>
                    <capability>...</capability>
                  </port>
                </ports>
              </node>
            </supported_NFs>
          </capabilities>
        </node>
      </nodes>
    </virtualizer>"""
    virtualizer = nffglib.Virtualizer.parse(text=config)
    ret = core.adaptation.controller_adapter.domains.components[
      'OPENSTACK'].rest_adapter.edit_config(virtualizer.xml())
    print "Return: ", ret
    print core.adaptation.controller_adapter.domains.components[
      'OPENSTACK'].rest_adapter._response.text


# Pre-register our helper class
ESCAPEInteractiveHelper.init()
