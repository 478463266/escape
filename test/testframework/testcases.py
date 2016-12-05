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
import imp
import os
import sys
from unittest.case import TestCase
from unittest.suite import TestSuite
from unittest.util import strclass

from runner import EscapeRunResult, RunnableTestCaseInfo, CommandRunner

RUNNER_SCRIPT_NAME = "run.sh"
ESCAPE_LOG_FILE_NAME = "escape.log"


class OutputAssertions(object):
  ADAPTATION_SUCCESS = "All installation process has been finished with " \
                       "success!"
  VIRTUALIZER_DIFFERENT_VERSION = "Version is different!"

  def check_successful_installation (self, result):
    """

    :type result: EscapeRunResult
    """
    # if (not self._has_message(escape_run_result.log_output,
    #                           self.ADAPTATION_SUCCESS)):
    #   raise AssertionError("Success message is missing from log output!\n%s" %
    #                        "".join(escape_run_result.log_output[-5:]))
    #
    # else:
    #   return True
    success = self._has_message(result.log_output,
                                self.ADAPTATION_SUCCESS)
    return True if success else self.get_result_lines(result.log_output)

  def check_virtualizer_version_matches (self, result):
    """

    :type result: testframework.runner.EscapeRunResult
    """
    # if self._has_message(escape_run_result.log_output,
    #                      self.VIRTUALIZER_DIFFERENT_VERSION):
    #   raise AssertionError("Virtualizer version mismatch")
    version_mismatch = self._has_message(result.log_output,
                                         self.VIRTUALIZER_DIFFERENT_VERSION)
    return True if not version_mismatch else "Got Virtualizer version mismatch!"

  @staticmethod
  def get_result_lines (log):
    return "Success message is missing from log output!\n%s" % "".join(
      log.log_output[-5:])

  @staticmethod
  def _has_message (log_content, expected_message):
    for log_line in log_content:
      if expected_message in log_line:
        return True

    return False


class WarningChecker(object):
  ACCEPTABLE_WARNINGS = [
    "Mapping algorithm in Layer: service is disabled! Skip mapping step and "
    "forward service request to lower layer",
    "No SGHops were given in the Service Graph! Could it be retreived? based "
    "on the Flowrules?",
    "Resource parameter delay is not given in",
    "Version are different!",
    "Resource parameter bandwidth is not given in",
    "If multiple infra nodes are present in the substrate graph and their "
    "VNF-Infra mapping is supposed to mean a "
    "placement criterion on the (possibly decomposed) Infra node, it will not "
    "be considered, because it is NYI.",
    "No SAP - SAP chain were given! All request links will be mapped as best "
    "effort links!",
    "Physical interface: eth0 is not found! Skip binding",
    "Skip starting xterms on SAPS according to global config"
  ]

  @staticmethod
  def _filter_warnings (log):
    return [line for line in log if line.startswith("|WARNING")]

  def check_no_unusual_warnings (self, result):
    warnings = self._filter_warnings(result.log_output)
    for warn in warnings:
      # for acceptable_warn in self.ACCEPTABLE_WARNINGS:
      #   if acceptable_warn in log_warn:
      #     is_acceptable = True
      #     break
      if warn not in self.ACCEPTABLE_WARNINGS:
        return warn
        # if not is_acceptable:
        #   raise AssertionError("Got unusual warning: " + log_warn)
    return True


class EscapeTestCase(TestCase, OutputAssertions, WarningChecker):
  """
  EscapeTestCase is a test case for the case01, case02 structure. It will run
  ESCAPE
  then place the result into the self.result field.
  You should implement the runTest method to verify the result
  See BasicSuccessfulTestCase
  """

  def __init__ (self, test_case_info, command_runner):
    """
    :type test_case_info: testframework.runner.RunnableTestCaseInfo
    :type command_runner: testframework.runner.CommandRunner
    """
    TestCase.__init__(self)
    self.test_case_info = test_case_info
    self.command_runner = command_runner
    self.result = None
    """:type result: testframework.runner.EscapeRunResult"""

  def __str__ (self):
    return "%s (%s)" % (
      self.test_case_info.testcase_dir_name, strclass(self.__class__))

  def id (self):
    return super(EscapeTestCase, self).id() + str(
      self.test_case_info.full_testcase_path)

  def setUp (self):
    super(EscapeTestCase, self).setUp()
    # Call cleanup template method
    self.test_case_cleanup()

  def runTest (self):
    # Run test case
    self.run_escape()
    # Evaluate result
    self.verify_result()

  def test_case_cleanup (self):
    # Remove escape.log it exists
    log_file = os.path.join(self.test_case_info.full_testcase_path,
                            ESCAPE_LOG_FILE_NAME)
    if os.path.exists(log_file):
      os.remove(log_file)
      print self, "DEL", log_file

  def run_escape (self):
    try:
      # Run ESCAPE test
      self.command_runner.execute()
      # Collect result
      self.result = self.collect_result_from_log()
    except KeyboardInterrupt:
      self.command_runner.kill_process()
      self.collect_result_from_log()
      raise

  def collect_result_from_log (self):
    log_file = os.path.join(self.test_case_info.full_testcase_path,
                            ESCAPE_LOG_FILE_NAME)
    try:
      with open(log_file) as f:
        return EscapeRunResult(output=f.readlines())
    except IOError as e:
      return EscapeRunResult(output=str(e), exception=e)

  def get_result_from_stream (self):
    output_stream = self.command_runner.get_process_output_stream()
    return output_stream if output_stream else ""

  def verify_result (self):
    # Template method for analyzing run result
    raise NotImplementedError('Not implemented yet!')


class BasicSuccessfulTestCase(EscapeTestCase):
  def check_errors (self):
    if self.result.was_error():
      output = self.get_result_from_stream()
      for line in output.splitlines():
        if line.startswith('[sudo]'):
          self.skipTest(reason=line)

  def verify_result (self):
    self.check_errors()

    success = self.check_successful_installation(self.result)
    self.assertTrue(success, msg=success)

    no_warning = self.check_no_unusual_warnings(self.result)
    self.assertTrue(no_warning, msg=no_warning)


class RootPrivilegedSuccessfulTestCase(BasicSuccessfulTestCase):
  def check_root_privilege (self):
    # Due to XMLTestRunner implementation test cannot skip in setUp()
    if CommandRunner("sudo uname", kill_timeout=2).execute().is_killed:
      self.skipTest("Root privilege is required to run the testcase: %s" %
                    self.test_case_info.testcase_dir_name)

  def runTest (self):
    self.check_root_privilege()
    # Run test case
    super(RootPrivilegedSuccessfulTestCase, self).runTest()


class TestCaseBuilder(object):
  # TODO - check the possibility to refactor to unittest.TestLoader

  DEFAULT_TESTCASE_CLASS = BasicSuccessfulTestCase
  # DEFAULT_TESTCASE_CLASS = RootPrivilegedSuccessfulTestCase

  def __init__ (self, cwd, show_output=False, kill_timeout=None):
    self.cwd = cwd
    self.show_output = show_output
    self.kill_timeout = kill_timeout

  @staticmethod
  def _get_test_command (case_config):
    return os.path.join(case_config.full_testcase_path,
                        RUNNER_SCRIPT_NAME)

  def _create_command_runner (self, case_info):
    return CommandRunner(cwd=self.cwd,
                         cmd=self._get_test_command(case_info),
                         kill_timeout=self.kill_timeout,
                         output_stream=sys.stdout if self.show_output else None)

  def build_from_config (self, case_info):
    """

    :type case_info: testframework.runner.RunnableTestCaseInfo
    :rtype: TestCase
    """
    runner_script = self._get_test_command(case_config=case_info)
    if not os.path.exists(runner_script):
      raise Exception("No %s in directory: %s" %
                      (RUNNER_SCRIPT_NAME, case_info.full_testcase_path))

    test_py_file = os.path.join(case_info.full_testcase_path,
                                "%s.py" % case_info.testcase_dir_name)

    cmd_runner = self._create_command_runner(case_info=case_info)
    if os.path.exists(test_py_file):
      return self._load_dynamic_test_case(case_info=case_info,
                                          test_py_file=test_py_file)
    else:
      return self.DEFAULT_TESTCASE_CLASS(test_case_info=case_info,
                                         command_runner=cmd_runner)

  def _load_dynamic_test_case (self, case_info, test_py_file):
    try:
      module = imp.load_source(case_info.testcase_dir_name(),
                               test_py_file)
      class_name = case_info.testcase_dir_name().capitalize()
      cmd_runner = CommandRunner(cwd=self.cwd,
                                 cmd=self._get_test_command(case_info))
      return getattr(module, class_name)(test_case_info=case_info,
                                         command_runner=cmd_runner)
    except AttributeError:
      raise Exception("No class found in %s file." % test_py_file)

  def to_suite (self, tests):
    """

    :type tests: list[RunnableTestCaseInfo]
    :rtype: TestSuite
    """
    test_cases = [self.build_from_config(case_info) for case_info in tests]
    return TestSuite(test_cases)
