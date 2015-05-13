# Copyright 2014 Levente Csikor <csikor@tmit.bme.hu>
# Copyright 2015 Janos Czentye <czentye@tmit.bme.hu>
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
Requirements::

  sudo apt-get install python-setuptools python-paramiko python-lxml \
  python-libxml2 python-libxslt1 libxml2 libxslt1-dev

  sudo pip install ncclient

Implement the supporting classes for communication over NETCONF

:class:`AbstractNETCONFAdapter` contains the main function for communication
over NETCONF such as managing SSH channel, handling configuration, assemble
RPC request and parse RPC reply
"""
from lxml import etree
from StringIO import StringIO

from ncclient import manager
from ncclient.operations import RPCError, OperationError
from ncclient.transport import TransportError
from ncclient.xml_ import new_ele, sub_ele


class AbstractNETCONFAdapter(object):
  """
  Abstract class for various Adapters rely on NETCONF protocol (RFC 4741)

  Contains basic functions for managing connection and invoking RPC calls.
  Configuration management can be handled by the external
  :class:`ncclient.manager.Manager` class exposed by the manager property

  Follows the Adapter design pattern
  """
  # NETCONF namespace - u'urn:ietf:params:xml:ns:netconf:base:1.0'
  NETCONF_NAMESPACE = manager.BASE_NS_1_0
  # RPC namespace. Must be set by derived classes through RPC_NAMESPACE
  RPC_NAMESPACE = None

  def __init__ (self, server, port, username, password, timeout=30,
       debug=False):
    """
    Initialize connection parameters

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
    :param debug: print DEBUG infos, RPC messages ect. (default: False)
    :type debug: bool
    :return: None
    """
    super(AbstractNETCONFAdapter, self).__init__()
    self.__server = server
    self.__port = int(port)
    self.__username = username
    self.__password = password
    self.__timeout = int(timeout)
    self.__debug = debug
    # variables for the last RPC reply
    self.__rpc_reply_formatted = dict()
    self.__rpc_reply_as_xml = ""
    # Server side and connection parameters
    self.__connection = None
    self.__config = None

  @property
  def connected (self):
    """
    :return: Return connection state
    :rtype: bool
    """
    return self.__connection is not None and self.__connection.connected

  @property
  def connection_data (self):
    """
    :return: Return connection data in (server, port, username) tuples
    :rtype: tuple
    """
    return self.__server, self.__port, self.__username

  @property
  def manager (self):
    """
    :return: Return the connection manager (wrapper for NETCONF commands)
    :rtype: :class:`ncclient.manager.Manager`
    """
    return self.__connection

  def connect (self):
    """
    This function will connect to the netconf server.

    :return: Also returns the NETCONF connection manager
    :rtype: :class:`ncclient.manager.Manager`
    """
    # __connection is responsible for keeping the connection up.
    self.__connection = manager.connect(host=self.__server, port=self.__port,
                                        username=self.__username,
                                        password=self.__password,
                                        hostkey_verify=False,
                                        timeout=self.__timeout)
    if self.__debug:
      print "Connecting to %s:%s with %s/%s ---> %s" % (
        self.__server, self.__port, self.__username, self.__password,
        'OK' if self.connected else 'PROBLEM')
    return self.__connection

  def disconnect (self):
    """
    This function will close the connection.

    :return: None
    """
    if self.connected:
      self.__connection.close_session()
    if self.__debug:
      print "Connection closed!"

  def get_config (self, source="running", to_file=False):
    """
    This function will download the configuration of the NETCONF agent in an
    XML format. If source is None then the running config will be downloaded.
    Other configurations are netconf specific (:rfc:`6241`) - running,
    candidate, startup

    :param source: NETCONF specific configuration source (defalut: running)
    :type source: str
    :param to_file: save config to file
    :type to_file: bool
    :return: None
    """
    if self.connected:
      self.__config = self.__connection.get_config(source=source).data_xml
      if to_file:
        with open("%s_%s.xml", "w") as f:
          f.write(self.__config)
      else:
        return self.__config
    else:
      raise RuntimeError("Not connected!")

  def get (self, expr="/"):
    """
    This process works as yangcli's GET function. A lot of information can be
    got from the running NETCONF agent. If an xpath-based expression is also
    set, the results can be filtered. The results are not printed out in a
    file, it's only printed to stdout

    :param expr: xpath-based expression
    :type expr: str
    :return: result in XML
    :rtype: str
    """
    return self.__connection.get(filter=('xpath', expr)).data_xml

  def _create_rpc_request (self, rpc_name, **params):
    """
    This function is devoted to create a raw RPC request message in XML format.
    Any further additional rpc-input can be passed towards, if netconf agent
    has this input list, called 'options'. Switches is used for connectVNF
    rpc in order to set the switches where the vnf should be connected.

    :param rpc_name: rpc name
    :type rpc_name: str
    :param options: additional RPC input in the specific <options> tag
    :type options: dict
    :param switches: set the switches where the vnf should be connected
    :type switches: list
    :param params: input params for the RPC using param's name as XML tag name
    :type params: dict
    :return: raw RPC message in XML format (lxml library)
    :rtype: :class:`lxml.etree.ElementTree`
    """
    # create the desired xml element
    xsd_fetch = new_ele(rpc_name)
    # set the namespace of your rpc
    xsd_fetch.set('xmlns', self.RPC_NAMESPACE)
    # set input params
    self.__parse_rpc_params(xsd_fetch, params)
    # we need to remove the confusing netconf namespaces with our own function
    rpc_request = self.__remove_namespace(xsd_fetch, self.NETCONF_NAMESPACE)
    # show how the created rpc message looks like
    if self.__debug:
      print "Generated raw RPC message:\n", etree.tostring(rpc_request,
                                                           pretty_print=True)
    return rpc_request

  def _parse_rpc_response (self, data=None):
    """
    Parse raw XML response and return params in dictionary. If data is given
    it is parsed instead of the lasr response and the result will not be saved.

    :param data: raw data (uses last reply by default)
    :type data: :class:`lxml.etree.ElementTree`
    :return: return parsed params
    :rtype: dict
    """
    # in order to handle properly the rpc-reply as an xml element we need to
    # create a new xml_element from it, since another BRAINFUCK arise around
    # namespaces
    # CREATE A PARSER THAT GIVES A SHIT FOR NAMESPACE
    parser = etree.XMLParser(ns_clean=True)
    if data:
      buffer = StringIO(data)
    else:
      buffer = StringIO(self.__rpc_reply_as_xml)
    # PARSE THE NEW RPC-REPLY XML
    dom = etree.parse(buffer, parser)
    # dom.getroot() = <rpc_reply .... > ... </rpc_reply>
    mainContents = dom.getroot()
    # alright, lets get all the important data with the following recursion
    parsed = self.__parse_xml_response(mainContents, self.RPC_NAMESPACE)
    if not data:
      self.__rpc_reply_formatted = parsed
    return parsed

  def _invoke_rpc (self, request_data):
    """
    This function is devoted to call an RPC, and parses the rpc-reply message
    (if needed) and returns every important parts of it in as a dictionary.
    Any further additional rpc-input can be passed towards, if netconf agent
    has this input list, called 'options'. Switches is used for connectVNF
    rpc in order to set the switches where the vnf should be connected.

    :param request_data: data for RPC request body
    :type request_data: dict
    :return: raw RPC response
    :rtype: :class:`lxml.etree.ElementTree`
    """
    # SENDING THE CREATED RPC XML to the server
    # rpc_reply = without .xml the reply has GetReply type
    # rpc_reply = with .xml we convert it to xml-string
    try:
      # we set our global variable's value to this xml-string therefore,
      # last RPC will always be accessible
      self.__rpc_reply_as_xml = self.__connection.dispatch(request_data).xml
      return self.__rpc_reply_as_xml
    except (RPCError, TransportError, OperationError):
      # need to handle???
      raise

  def __remove_namespace (self, xml_element, namespace=None):
    """
    Own function to remove the ncclient's namespace prefix, because it causes
    "definition not found error" if OWN modules and RPCs are being used

    :param xml_element: XML element
    :type xml_element: :class:`lxml.etree.ElementTree`
    :param namespace: namespace
    :type namespace: :class:`lxml.etree.ElementTree`
    :return: cleaned XML elemenet
    :rtype: :class:`lxml.etree.ElementTree`
    """
    if namespace is not None:
      ns = u'{%s}' % namespace
      for elem in xml_element.getiterator():
        if elem.tag.startswith(ns):
          elem.tag = elem.tag[len(ns):]
    return xml_element

  def __parse_rpc_params (self, rpc_request, params):
    """
    Parse given keyword arguments and generate RPC body in proper XML format.
    The key value is used as the XML tag name. If the value is another
    dictionary the XML structure follows the hierarchy. The param values can
    be only simple types and dictionary for simplicity. Convertation example::

      {
        'vnf_type': 'headerDecompressor',
        'options': {
                    'name': 'ip',
                    'value': 127.0.0.1
                    }
      }

    will be generated into::

      <rpc-call-name>
        <vnf_type>headerDecompressor</vnf_type>
        <options>
          <name>ip</name>
          <value>127.0.0.1</value>
        </options>
      </rpc-call-name>

    :param rpc_request: empty RPC request
    :type rpc_request: :class:`lxml.etree.ElementTree`
    :param params: RPC call argument given in a dictionary
    :type params: dict
    :return: parsed params in XML format (lxml library)
    :rtype: :class:`lxml.etree.ElementTree`
    """

    def parseChild (parent, part):
      for key, value in part.iteritems():
        if isinstance(value, dict):
          node = sub_ele(parent, key)
          # Need to go deeper -> recursion
          parseChild(node, value)
        elif value is not None:
          node = sub_ele(parent, key)
          node.text = str(value)

    assert isinstance(params, dict), "'params' must be a dictionary!"
    parseChild(rpc_request, params)
    return rpc_request

  def __parse_xml_response (self, element, namespace=None):
    """
    This is an inner function, which is devoted to automatically analyze the
    rpc-reply message and iterate through all the xml elements until the last
    child is found, and then create a dictionary. Return a dict with the
    parsed data. If the reply is OK the returned dict contains an `rcp-reply`
    element with value `OK`.

    :param element: XML element
    :type element: :class:`lxml.etree.ElementTree`
    :param namespace: namespace
    :type: str
    :return: parsed XML data
    :rtype: dict
    """
    parsed = {}  # parsed xml subtree as a dict
    if namespace is not None:
      namespace = "{%s}" % namespace
    for i in element.iterchildren():
      if i.getchildren():
        # still has children! Go one level deeper with recursion
        val = self.__parse_xml_response(i, namespace)
        key = i.tag.replace(namespace, "")
      else:
        # if <ok/> is the child, then it has only <rpc-reply> as ancestor
        # so we do not need to iterate through <ok/> element's ancestors
        if i.tag == "{%s}ok" % self.NETCONF_NAMESPACE:
          key = "rpc-reply"
          val = "ok"
        else:
          key = i.tag.replace(namespace, "")
          val = element.findtext(
            "%s%s" % (namespace, i.tag.replace(namespace, "")))
      if key in parsed:
        if isinstance(parsed[key], list):
          parsed[key].append(val)
        else:
          # had only one element, convert to list
          parsed[key] = [parsed[key], val]
      else:
        parsed[key] = val
    return parsed

  def call_RPC (self, rpc_name, no_rpc_error=False, **params):
    """
    Call an RPC given by rpc_name. If `no_rpc_error` is set returns with a
    dict instead of raising :class:`RPCError`

    :param rpc_name: RPC name
    :type rpc_name: str
    :param no_rpc_error: return with dict represent RPC error instead of
    exception
    :type no_rpc_error: bool
    :return: RPC reply
    :rtype: dict
    """
    try:
      request_data = self._create_rpc_request(rpc_name, **params)
      self._invoke_rpc(request_data)
      return self._parse_rpc_response()
    except RPCError as e:
      print "rpcerror"
      if no_rpc_error:
        result = {"rpc-reply": "Error"}
        result.update(e.to_dict())
        return result
      else:
        raise

  def __enter__ (self):
    """
    Context manager setup action.

    Usage::

      with AbstractNETCONFAdapter() as adapter:
        ...
    """
    if not self.connected:
      self.connect()
    return self

  def __exit__ (self, exc_type, exc_val, exc_tb):
    """
    Context manager cleanup action
    """
    if self.connected:
      self.disconnect()


if __name__ == "__main__":
  # TEST
  from pprint import pprint
  from collections import OrderedDict
  # print "Create VNFRemoteManager..."
  # vrm = VNFRemoteManager(server='192.168.12.128', port=830,
  # username='mininet', password='mininet', debug=True)
  # print "-" * 60
  # print "VNFRemoteManager:"
  # pprint(vrm.__dict__)
  print "-" * 60
  print "Connecting..."
  # vrm.connect()
  vrm = AbstractNETCONFAdapter(server='192.168.12.128', port=830,
                               username='mininet', password='mininet',
                               debug=True)
  vrm.RPC_NAMESPACE = u'http://csikor.tmit.bme.hu/netconf/unify/vnf_starter'
  with vrm as vrm:
    print "Connected"
    print "-" * 60
    print "Get config"
    print vrm.get_config()
    print "-" * 60
    print "Get /proc/meminfo..."
    # get /proc/meminfo
    print vrm.get("/proc/meminfo")
    # call rpc getVNFInfo
    print "-" * 60
    print "Call getVNFInfo..."
    reply = vrm.call_RPC('getVNFInfo')
    # reply = vrm.getVNFInfo()
    print "-" * 60
    print "Reply:"
    pprint(reply)
    print "-" * 60
    print "Call initiateVNF..."
    try:
      reply = vrm.call_RPC("initiateVNF", vnf_type="headerDecompressor",
                           options=OrderedDict(
                             {"name": "ip", "value": "127.0.0.1"}))
      # reply = vrm.initiateVNF(vnf_type="headerDecompressor",
      # options=OrderedDict(
      # {"name": "ip", "value": "127.0.0.1"}))
    except RPCError as e:
      pprint(e.to_dict())
      pprint(e.info.split('\n'))

    print "-" * 60
    print "Reply:"
    pprint(reply)
    print "-" * 60
    # print "Call connectVNF..."
    # reply = vrm.rpc("connectVNF", vnf_id='1', vnf_port="0", switch_id="s3")
    # print "-" * 60
    # print "Reply:"
    # pprint(reply)
    # print "-" * 60
    print "Call stopVNF..."
    try:
      reply = vrm.call_RPC("stopVNF", vnf_id='1')
      # reply = vrm.stopVNF(vnf_id='1')
    except RPCError as e:
      pprint(e.to_dict())
      pprint(e.info.split('\n'))
    print "-" * 60
    print "Reply:"
    pprint(reply)
    print "-" * 60
    print "Disconnecting..."
    # vrm.disconnect()