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
Contains abstract classes for concrete layer API modules
"""
from SocketServer import ThreadingMixIn
import urlparse
import json
import os.path
import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from escape import __version__, CONFIG
from escape.util.misc import SimpleStandaloneHelper
from pox.lib.revent import EventMixin
from pox.core import core


class AbstractAPI(EventMixin):
  """
  Abstract class for UNIFY's API

  Contain common functions

  Follows Facade design pattern
  """
  # Default value for logger. Should be overwritten by child classes
  _core_name = "AbstractAPI"
  # Explicitly defined dependencies as POX components
  dependencies = ()
  # Events raised by this class, but already defined in superclass
  # _eventMixin_events = set()

  def __init__ (self, standalone=False, **kwargs):
    """
    Abstract class constructor

    Handle core registration along with :func:`_all_dependencies_met()`

    Set given parameters (standalone parameter is mandatory) automatically as::

      self._<param_name> = <param_value>

    Base constructor functions have to be called as the last step in derived
    classes. Same situation with :func:`_all_dependencies_met()` respectively.
    Must not override these function, just use :func:`initialize()` for
    init steps. Actual API classes must only call :func:`super()` in their
    constructor with the form::

      super(<API Class name>, self).__init__(standalone=standalone, **kwargs)

    .. warning::
      Do not use prefixes in the name of event handlers, because of automatic
      dependency discovery considers that as a dependent component and this
      situation cause a dead lock (component will be waiting to each other to
      set up)

    :param standalone: started in standalone mode or not
    :type standalone: bool
    """
    super(AbstractAPI, self).__init__()
    # Save custom parameters with the given name
    self._standalone = standalone
    for key, value in kwargs.iteritems():
      setattr(self, '_' + key, value)
    # Check if need to skip dependency handling
    if standalone:
      # Initiate component manually
      self._all_dependencies_met()
    else:
      # Wait for the necessary POX component until they are resolved and set
      # up event handlers. The dependencies are given explicitly which are
      # defined in the actual API and not use automatic event handler based
      # dependency discovery to avoid issues come from fully event-driven
      # structure.
      # See more in POXCore document.
      core.core.listen_to_dependencies(self, getattr(self, 'dependencies', ()))

  def _all_dependencies_met (self):
    """
    Called when every component on which depends are initialized on POX core

    Contain dependency relevant initialization.

    :return: None
    """
    self.initialize()
    # With fully event-driven communication between the layers the dependency
    # handling takes care by listen_to_dependencies() run into a dead-lock.
    # The root of this problem is the bidirectional or cyclic dependency
    # between the components, so basically the layers will always wait to each
    # other to be registered on core. To avoid this situation the naming
    # convention of event handlers on which the dependency checking based is
    # not followed (aka leave _handle_<component name>_<event name>) and
    # the event listeners is set up manually. For automatic core registration
    # the components have to contain dependencies explicitly.
    for dep in self.dependencies:
      if not self._standalone:
        if core.core.hasComponent(dep):
          dep_layer = core.components[dep]
          # Register actual event handlers on dependent layer
          dep_layer.addListeners(self)
          # Register dependent layer's event handlers on actual layer
          self.addListeners(dep_layer)
        else:
          raise AttributeError("Component is not registered on core")
      else:
        # In case of standalone mode set up a StandaloneHelper in this object
        # with the name of the dependency to handle raised events automatically
        setattr(self, dep, SimpleStandaloneHelper(self, dep))
    # Subscribe for GoingDownEvent to finalize API classes
    # shutdown() function will be called if POX's core going down
    core.addListenerByName('GoingDownEvent', self.shutdown)
    # Subscribe core event to advanced functions
    # Listeners' name must follow POX naming conventions
    core.addListeners(self)
    # Everything is set up an "running" so register the component on pox.core
    # as a final step. Other dependent component can finish initialization now.
    core.core.register(self._core_name, self)
    # Set "running" config for convenience purposes
    try:
      CONFIG[self._core_name]["LOADED"] = True
    except KeyError:
      CONFIG[self._core_name] = {"LOADED": True}

  def initialize (self):
    """
    Init function for child API classes to simplify dynamic initialization

    Called when every component on which depends are initialized and registered
    in POX core

    This function should be overwritten by child classes.

    :return: None
    """
    pass

  def shutdown (self, event):
    """
    Finalization, deallocation, etc. of actual component

    Should be overwritten by child classes

    :param event: shutdown event raised by POX core
    :type event: GoingDownEvent
    :return: None
    """
    pass

  @staticmethod
  def _read_json_from_file (graph_file):
    """
    Read the given file and return a string formatted as JSON

    :param graph_file: file path
    :type graph_file: str
    :return: JSON data
    :rtype: str
    """
    if graph_file and not graph_file.startswith('/'):
      graph_file = os.path.abspath(graph_file)
    with open(graph_file, 'r') as f:
      graph = json.load(f)
    return graph

  def __str__ (self):
    """
    Print class type and non-private attributes with their types for debugging

    :return: specific string
    :rtype: str
    """
    print '<%s.%s object at %s>' % (
      self.__class__.__module__, self.__class__.__name__, hex(id(self)))
    print "Non-private attributes:"
    import pprint

    return pprint.pformat(
      [(f, type(getattr(self, f))) for f in dir(self) if not f.startswith('_')])


class RESTServer(HTTPServer, ThreadingMixIn):
  """
  Base HTTP server for RESTful API

  Initiate an :class:`HTTPServer` and run it in different thread
  """

  def __init__ (self, RequestHandlerClass, address='127.0.0.1', port=8008):
    """
      Set up an :class:`BaseHTTPServer.HTTPServer` in a different
      thread

      :param RequestHandlerClass: Class of a handler which handles HTTP request
      :type RequestHandlerClass: AbstractRequestHandler
      :param address: Used IP address
      :type address: str
      :param port: Used port number
      :type port: int
      """
    HTTPServer.__init__(self, (address, port), RequestHandlerClass)
    # self._server = Server((address, port), RequestHandlerClass)
    self._thread = threading.Thread(target=self.run)
    self._thread.daemon = True
    self.started = False

  def start (self):
    """
    Start RESTServer thread
    """
    self.started = True
    self._thread.start()

  def stop (self):
    """
    Stop RESTServer thread
    """
    if self.started:
      self.shutdown()

  def run (self):
    """
    Handle one request at a time until shutdown.
    """
    self.RequestHandlerClass.log.debug(
      "Init REST-API on %s:%d!" % self.server_address)
    # Start API loop
    self.serve_forever()
    self.RequestHandlerClass.log.debug(
      "REST-API on %s:%d is shutting down..." % self.server_address)


class RESTError(Exception):
  """
  Exception class for REST errors
  """

  def __init__ (self, msg=None, code=0):
    super(RESTError, self).__init__()
    self._msg = msg
    self._code = code

  @property
  def msg (self):
    return self._msg

  @property
  def code (self):
    return int(self._code)

  def __str__ (self):
    return self._msg


class AbstractRequestHandler(BaseHTTPRequestHandler):
  """
  Minimalistic RESTful API for Layer APIs

  Handle /escape/* URLs.

  Method calling permissions represented in escape_intf dictionary

  .. warning::
    This class is out of the context of the recoco's co-operative thread
    context! While you don't need to worry much about synchronization between
    recoco tasks, you do need to think about synchronization between recoco task
    and normal threads. Synchronisation is needed to take care manually - use
    relevant helper function of core object: :func:`callLater()`/
    :func:`raiseLater()` or use :func:`schedule_as_coop_task()
    <escape.util.misc.schedule_as_coop_task>` decorator defined in
    :mod:`escape.util.misc` on the called function
  """
  # For HTTP Response messages
  server_version = "ESCAPE/" + __version__
  static_prefix = "escape"
  # Bind HTTP verbs to UNIFY's API functions
  request_perm = {'GET': (), 'POST': (), 'PUT': (), 'DELETE': ()}
  # Name of the layer API to which the server bounded
  bounded_layer = None
  # Logger. Should be overrided in child classes
  log = core.getLogger("REST-API")

  def do_GET (self):
    """
    Get information about an entity. R for CRUD convention.
    """
    self._process_url()

  def do_POST (self):
    """
    Create an entity. C for CRUD convention.
    """
    self._process_url()

  def do_PUT (self):
    """
    Update an entity. U for CRUD convention.
    """
    self._process_url()

  def do_DELETE (self):
    """
    Delete an entity. D for CRUD convention.
    """
    self._process_url()

  def _process_url (self):
    """
    Split HTTP path and call the carved function if it is defined in this class
    and in request_perm

    :return: None
    """
    self.log.debug("Got HTTP request: %s" % str(self.raw_requestline).rstrip())
    http_method = self.command.upper()
    real_path = urlparse.urlparse(self.path).path
    try:
      if real_path.startswith('/%s/' % self.static_prefix):
        func_name = real_path.split('/')[2]
        if http_method in self.request_perm:
          if func_name in self.request_perm[http_method]:
            if hasattr(self, func_name):
              getattr(self, func_name)()
              self.send_acknowledge()
          else:
            self.send_error(406)
        else:
          self.send_error(501)
      else:
        self.send_error(404)
    except RESTError as e:
      # Handle all the errors
      if e.code:
        self.send_error(e.code, e.msg)
      else:
        self.send_error(500, e.msg)
    finally:
      self.wfile.flush()
      self.wfile.close()

  def _parse_json_body (self):
    """
    Parse HTTP request body in JSON format

    ::note::

      Parsed JSON object is Unicode

    GET, DELETE messages don't have body - return empty dict by default

    :return: request body in JSON format
    :rtype: str
    """
    charset = 'utf-8'
    try:
      splitted_type = self.headers['Content-Type'].split('charset=')
      if len(splitted_type) > 1:
        charset = splitted_type[1]
      content_len = int(self.headers['Content-Length'])
      raw_data = self.rfile.read(content_len)
      return json.loads(raw_data, encoding=charset)
    except KeyError as e:
      # Content-Length header is not defined
      # or charset is not defined in Content-Type header.
      if e.args[0] == 'Content-Length':
        # 411: ('Length Required', 'Client must specify Content-Length.'),
        raise RESTError(code=411)
      else:
        raise RESTError(code=412,
                        msg="Missing header from request: %s" % e.args[0])
    except ValueError as e:
      # Failed to parse request body to JSON
      self.log_error("Request parsing failed: %s", e)
      raise RESTError(code=415, msg="Request parsing failed: %s" % e)

  def send_REST_headers (self):
    self.send_header('Allow', ','.join([str(x) for x in self.request_perm]))

  def send_acknowledge (self, msg='{"result": "Accepted"}'):
    msg.encode("UTF-8")
    self.send_response(202)
    self.send_header('Content-Type', 'text/json; charset=UTF-8')
    self.send_header('Content-Length', len(msg))
    self.send_REST_headers()
    self.end_headers()
    self.wfile.write(msg)

  def _send_json_response (self, data, encoding='utf-8'):
    """
    Send requested data in JSON format

    :param data: data in JSON format
    :type data: dict
    :param encoding: Set data encoding (optional)
    :type encoding: str
    :return: None
    """
    response_body = json.dumps(data, encoding=encoding)
    self.send_response(200)
    self.send_header('Content-Type', 'text/json; charset=' + encoding)
    self.send_header('Content-Length', len(response_body))
    self.end_headers()
    self.wfile.write(response_body)
    self.wfile.flush()

  error_content_type = "text/json"

  def send_error (self, code, message=None):
    """
    Override original function to send back allowed HTTP verbs and set format
    to JSON
    """

    def _quote_html (html):
      return html.replace("&", "&amp;").replace("<", "&lt;").replace(">",
                                                                     "&gt;")

    try:
      short, long = self.responses[code]
    except KeyError:
      short, long = '???', '???'
    if message is None:
      message = short
    explain = long
    self.log_error("code %d, message %s", code, message)
    # using _quote_html to prevent Cross Site Scripting attacks (see bug
    # #1100201)
    content = (self.error_message_format % {'code': code,
                                            'message': _quote_html(message),
                                            'explain': explain})
    self.send_response(code, message)
    self.send_header("Content-Type", self.error_content_type)
    self.send_header('Connection', 'close')
    self.send_REST_headers()
    self.end_headers()
    if self.command != 'HEAD' and code >= 200 and code not in (204, 304):
      self.wfile.write(content)

  def log_error (self, mformat, *args):
    """
    Overwritten to use POX logging mechanism
    """
    self.log.warning("%s - - [%s] %s" % (
      self.client_address[0], self.log_date_time_string(), mformat % args))

  def log_message (self, mformat, *args):
    """
    Disable logging of incoming messages
    """
    pass

  def log_full_message (self, mformat, *args):
    """
    Overwritten to use POX logging mechanism
    """
    self.log.debug("%s - - [%s] %s" % (
      self.client_address[0], self.log_date_time_string(), mformat % args))

  def _proceed_API_call (self, function, *args, **kwargs):
    """
    Fail-safe method to call API function

    The cooperative micro-task context is handled by actual APIs

    Should call this with params, not directly the function of actual API

    :param function: function name
    :type function: str
    :param args: Optional params
    :type args: tuple
    :param kwargs: Optional named params
    :type kwargs: dict
    :return: None
    """
    if core.core.hasComponent(self.bounded_layer):
      layer = core.components[self.bounded_layer]
      if hasattr(layer, function):
        return getattr(layer, function)(*args, **kwargs)
      else:
        # raise NotImplementedError
        self.log.warning(
          'Mistyped or not implemented API function call: %s ' % function)
        raise RESTError(
          msg='Mistyped or not implemented API function call: %s ' % function)
    else:
      self.log.error('Error: No component has registered with the name: %s, '
                     'ABORT function call!' % self.bounded_layer)
