# Copyright 2015 Lajos Gerecs, Janos Czentye
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
import copy
import imp
import importlib
import json
import logging
import os
import sys
from collections import Iterable
from threading import Timer

import pexpect
from pexpect import ExceptionPexpect

log = logging.getLogger()


class Tee(object):
  """
  Inspired by the bash command: tee

  tee - read from standard input and write to standard output and files
  """

  def __init__ (self, filename):
    super(Tee, self).__init__()
    self.file = open(filename, mode="w", buffering=0)
    self.stdout = sys.stdout
    sys.stdout = self

  def __del__ (self):
    sys.stdout = self.stdout
    self.file.close()

  def write (self, data):
    self.file.write(data)
    self.stdout.write(data)

  def __enter__ (self):
    return self

  def __exit__ (self, exc_type, exc_val, exc_tb):
    self.__del__()


class EscapeRunResult():
  """
  Container class for storing the result of the test run.
  """

  def __init__ (self, output=None, exception=None):
    self.log_output = output
    self.exception = exception

  def was_error (self):
    return self.exception is not None

  def __iter__ (self):
    return iter(self.log_output)


class CommandRunner(object):
  """
  Main runner class which capable of running the test script and kill the
  process explicitly or based on the timeout value.
  """
  KILL_TIMEOUT = 15

  def __init__ (self, cmd, cwd=None, kill_timeout=None, on_kill=None,
                output_stream=None):
    self._command = self.__evaluate_cmd(cmd)
    self._cwd = cwd if cwd else os.path.dirname(__file__)
    self.kill_timeout = kill_timeout if kill_timeout else self.KILL_TIMEOUT
    self.on_kill_hook = on_kill
    self.output_stream = output_stream
    self.__process = None
    self.__kill_timer = None
    self.__killed = False

  @property
  def is_killed (self):
    return self.__killed

  @property
  def is_alive(self):
    return self.__process and self.__process.isalive()

  @staticmethod
  def __evaluate_cmd (cmd):
    """
    Split command to list for pexpect.

    :param cmd: str or list
    :rtype: list[str]
    """
    if isinstance(cmd, basestring):
      return cmd.split(' ')
    elif isinstance(cmd, Iterable):
      return list(cmd)
    else:
      return None

  def execute (self):
    """
    Create and start the process. Block until the process ends or timeout is
    exceeded.
    """
    try:
      self.__process = pexpect.spawn(self._command[0],
                                     args=self._command[1:],
                                     timeout=self.kill_timeout + 1,
                                     cwd=self._cwd,
                                     logfile=self.output_stream)
      self.__kill_timer = Timer(self.kill_timeout, self.kill_process,
                                [self.__process])
      self.__kill_timer.start()
      self.__process.expect(pexpect.EOF)
    except ExceptionPexpect as e:
      log.error("Got exception during execution of ESCAPE: %s" % e)
      self.kill_process()
    else:
      if self.__kill_timer:
        self.__kill_timer.cancel()
    return self

  def kill_process (self, *args, **kwargs):
    """
    Kill the process and call the optional hook function.
    """
    log.warning("Kill process...")
    self.stop()
    self.__killed = True
    if self.on_kill_hook:
      self.on_kill_hook()

  def stop (self):
    """
    Stop the process.

    :return: None
    """
    if self.__process:
      self.__process.sendcontrol('c')
    if self.__kill_timer:
      self.__kill_timer.cancel()

  def get_process_output_stream (self):
    """
    :return: Return with the process buffer.
    """
    return self.__process.before if self.__process.before else ""

  def clone (self):
    return copy.deepcopy(self)

  def cleanup (self):
    self.__process = None
    self.__kill_timer = None


class RunnableTestCaseInfo(object):
  """
  Container class for storing the relevant information and config values of a
  test case.
  """
  CONFIG_FILE_NAME = "test.config"
  CONFIG_CONTAINER_NAME = "test"
  RUNNER_SCRIPT_NAME = "run.sh"
  README_FILE_NAME = "README.txt"

  def __init__ (self, case_path):
    # Removing trailing slash
    self.__case_path = os.path.normpath(case_path)
    self.sub_name = None

  @property
  def testcase_dir_name (self):
    """
    :return: directory name of the test case
    :rtype: str
    """
    return os.path.basename(self.__case_path)

  @property
  def name (self):
    if self.sub_name is not None:
      return "%s-%s" % (self.testcase_dir_name, self.sub_name)
    else:
      return self.testcase_dir_name

  @property
  def full_testcase_path (self):
    """
    :return: absolute path of the test case directory.
    :rtype: str
    """
    return self.__case_path

  @property
  def test_command (self):
    """
    :return: absolute command path of the test case runner script.
    :rtype: str
    """
    return os.path.join(self.full_testcase_path,
                        self.RUNNER_SCRIPT_NAME)

  @property
  def config_file_name (self):
    """
    :return: absolute path of the test case config file.
    :rtype: str
    """
    return os.path.join(self.full_testcase_path,
                        self.CONFIG_FILE_NAME)

  def readme (self):
    """
    :return: load the README file
    :rtype: str
    """
    with open(os.path.join(self.full_testcase_path,
                           self.README_FILE_NAME)) as f:
      readme = f.read()
    return readme if readme else ""

  def load_test_case_class (self):
    """
    :return: Return the TestCase class and it's parameters defined in the
      test case config file
    :rtype: tuple(object, dict)
    """
    misc = imp.load_source("misc", os.path.join(os.path.abspath(
      os.path.dirname(__file__)), "../../escape/escape/util/misc.py"))
    with open(self.config_file_name, 'r') as f:
      config = json.load(f, object_hook=misc.unicode_to_str)
      try:
        test_args = copy.copy(config[self.CONFIG_CONTAINER_NAME])
        m = test_args.pop('module')
        c = test_args.pop('class')
        return getattr(importlib.import_module(m), c), test_args
      except KeyError:
        pass
    return None, None

  def __repr__ (self):
    return "RunnableTestCase [%s]" % self.testcase_dir_name

  def clone (self):
    return copy.deepcopy(self)
