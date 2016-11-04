from __future__ import print_function
import abc
import os
import subprocess
import time
import signal
import pexpect
from pexpect import fdpexpect
from threading import Timer


class TestRunner:
  def __init__ (self, escape, test_runner_config):
    """

    :type escape: Escape
    :type test_runner_config: TestRunnerConfig
    """
    self._test_runner_config = test_runner_config
    self.escape = escape

  def run_testcase (self, filename):
    path = os.path.join(self._test_runner_config.test_case_directory, filename)
    return self.escape.run(path)


class Logger:
  def log_start (self, message):
    print(message)

  def log_end_output (self, stderr):
    print(stderr)

  def timed_out (self, pexpect_proc):
    print("Timed out: " + pexpect_proc)


class Escape():
  __metaclass__ = abc.ABCMeta

  def __init__ (self):
    pass

  @abc.abstractmethod
  def run (self, filepath):
    pass


class TestRunnerConfig():
  def __init__ (self, test_case_directory):
    self.test_case_directory = test_case_directory


class CommandLineEscape(Escape):
  OPT_QUIT_ON_DEPLOY = "-q"
  OPT_DEBUG = "-d"
  OPT_TEST_OUTPUT = "-t"
  OPT_RUN_INFRA = "-f"
  OPT_SOURCE_FILE = "-s"

  def __init__ (self, escape_path=__file__ + "/../../escape.py", logger=Logger()):
    self.logger = logger
    self._escape_path = os.path.abspath(escape_path)
    self._cwd = os.path.dirname(self._escape_path)

  def _kill_process (self, p):
    self.logger.timed_out(p)
    p.sendcontrol('c')

  def run (self, filepath):
    command = [
      self._escape_path,
      self.OPT_DEBUG,
      self.OPT_TEST_OUTPUT,
      self.OPT_RUN_INFRA,
      self.OPT_QUIT_ON_DEPLOY,
      self.OPT_SOURCE_FILE,
      filepath,
    ]

    self.logger.log_start("Starting testcase " + filepath + " : " + ", ".join(command))

    proc = pexpect.spawn(command[0],
                         args=command[2:],
                         timeout=120,
                         cwd=self._cwd
                         )

    kill_timer = Timer(100, self._kill_process, [proc])
    kill_timer.start()

    proc.expect(pexpect.EOF)

    stdout, stderr = "", proc.before
    self.logger.log_end_output(stderr)
    kill_timer.cancel()
    return EscapeRunResult(stdout, stderr)


class EscapeRunResult():
  def __init__ (self, stdout="", stderr=""):
    self.stdout = stderr
    self.stderr = stderr
