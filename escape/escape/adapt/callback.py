# Copyright 2017 Janos Czentye <czentye@tmit.bme.hu>
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
import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from escape.adapt import log as log

log = log.getChild('callback')


class CallbackHandler(BaseHTTPRequestHandler):
  RESULT_PARAM_NAME = "response-code"
  MESSAGE_ID_NAME = "message-id"

  def log_message (self, format, *args):
    """
    Disable logging of incoming messages.

    :param format: message format
    :type format: str
    :return: None
    """
    pass

  def do_POST (self):
    self._dispatch_request()

  def _dispatch_request (self):
    self.__process_request()
    self.send_response(200)
    self.send_header('Connection', 'close')
    self.end_headers()

  def __process_request (self):
    params = self.__get_request_params()
    if self.RESULT_PARAM_NAME in params and self.MESSAGE_ID_NAME in params:
      self.server.invoke_hook(msg_id=params.get(self.MESSAGE_ID_NAME),
                              result=params.get(self.RESULT_PARAM_NAME))
    else:
      log.warning("Received callback with missing params: %s" % params)

  def __get_request_params (self):
    params = {}
    query = urlparse.urlparse(self.path).query
    if query:
      query = query.split('&')
      for param in query:
        if '=' in param:
          name, value = param.split('=', 1)
          params[name] = value
        else:
          params[param] = True
    # Check message-id in headers as backup
    if self.MESSAGE_ID_NAME not in params:
      if self.MESSAGE_ID_NAME in self.headers:
        params[self.MESSAGE_ID_NAME] = self.headers[self.MESSAGE_ID_NAME]
    return params


class CallbackManager(HTTPServer, Thread):
  DEFAULT_SERVER_ADDRESS = "localhost"
  DEFAULT_PREFIX = "callbacks"
  DEFAULT_PORT = 9000
  DEFAULT_WAIT_TIMEOUT = 3

  def __init__ (self, hook, domain_name, address=DEFAULT_SERVER_ADDRESS,
                port=DEFAULT_PORT, wait_timeout=DEFAULT_WAIT_TIMEOUT,
                **kwargs):
    Thread.__init__(self, name=self.__class__.__name__)
    HTTPServer.__init__(self, (address, port), CallbackHandler)
    self.__hook = hook
    self.domain_name = domain_name
    self.wait_timeout = wait_timeout
    self.__register = {}
    self.daemon = True

  @property
  def url (self):
    return "http://%s:%s/callback" % self.server_address

  def run (self):
    try:
      log.debug("Start %s for domain: %s on %s:%s" % (self.__class__.__name__,
                                                      self.domain_name,
                                                      self.server_address[0],
                                                      self.server_address[1]))
      self.serve_forever()
    except KeyboardInterrupt:
      raise
    except Exception as e:
      log.error("Got exception in %s: %s" % (self.__class__.__name__, e))
    finally:
      self.server_close()

  def subscribe_callback (self, id, data):
    log.debug("Register callback for response: %s on domain: %s" %
              (id, self.domain_name))
    if id not in self.__register:
      self.__register[id] = data
    else:
      log.warning("Hook is already registered for id: %s on domain: %s"
                  % (id, self.domain_name))

  def unsubscribe_callback (self, id):
    log.debug("Unregister callback for response: %s from domain: %s"
              % (id, self.domain_name))
    return self.__register.pop(id, None)

  def invoke_hook (self, msg_id, result):
    try:
      result = int(result)
    except ValueError:
      log.error("Received response code is not valid: %s! Abort callback..."
                % result)
      return
    if msg_id not in self.__register:
      log.warning("Received unregistered callback with id: %s from domain: %s"
                  % (msg_id, self.domain_name))
      return
    log.debug("Received valid callback with id: %s, result: %s from domain: %s"
              % (msg_id, result, self.domain_name))
    self.__hook(msg_id, result)