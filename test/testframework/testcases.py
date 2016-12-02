# Copyright 2015 Lajos Gerecs
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
from unittest.case import TestCase
from unittest.suite import TestSuite
from unittest.util import strclass

from runner import EscapeRunResult, RunnableTestCaseInfo

RUNNER_SCRIPT_NAME = "run.sh"


class TestCaseBuilder(object):
  def __init__ (self, command_runner):
    """

    :type command_runner: testframework.runner.CommandRunner
    """
    self.command_runner = command_runner

  def build_from_config (self, test_case_config):
    """

    :type test_case_config: testframework.runner.RunnableTestCaseInfo
    :rtype: TestCase
    """
    if not os.path.exists(os.path.join(test_case_config.full_testcase_path,
                                       RUNNER_SCRIPT_NAME)):
      raise Exception("No %s in directory: %s" %
                      (RUNNER_SCRIPT_NAME, test_case_config.full_testcase_path))

    test_py_file = os.path.join(test_case_config.full_testcase_path,
                                "%s.py" % test_case_config.testcase_dir_name)

    if os.path.exists(test_py_file):
      return self._load_dynamic_test_case(test_case_config, test_py_file)
    else:
      return BasicSuccessfulTestCase(test_case_config, self.command_runner)

  def _load_dynamic_test_case (self, test_case_config, test_py_file):
    try:
      module = imp.load_source(test_case_config.testcase_dir_name(),
                               test_py_file)
      class_name = test_case_config.testcase_dir_name().capitalize()
      return getattr(module, class_name)(test_case_config, self.command_runner)
    except AttributeError:
      raise Exception("No class found in %s file." % test_py_file)

  def to_suite (self, tests):
    """

    :type tests: list[RunnableTestCaseInfo]
    :rtype: TestSuite
    """
    test_cases = [self.build_from_config(case_info) for case_info in tests]
    return TestSuite(test_cases)


class SimpleTestCase(TestCase):
  def __init__ (self, test_case_config, command_runner):
    """

    :type command_runner: CommandRunner
    :type test_case_config: RunnableTestCaseInfo
    """
    super(SimpleTestCase, self).__init__()
    self.command_runner = command_runner
    self.test_case_config = test_case_config

  def runTest (self):
    self.result = self.command_runner.execute(
      os.path.join(self.test_case_config, RUNNER_SCRIPT_NAME))


class OutputAssertions(object):
  ADAPTATION_SUCCESS = "All installation process has been finished with " \
                       "success!"
  VIRTUALIZER_DIFFERENT_VERSION = "Version is different!"

  def assert_successful_installation (self, escape_run_result):
    """

    :type escape_run_result: EscapeRunResult
    """
    if (not self._has_message(escape_run_result.log_output,
                              self.ADAPTATION_SUCCESS)):
      raise AssertionError("Success message is missing from log output!\n%s" %
                           "".join(escape_run_result.log_output[-5:]))
    else:
      return True

  def assert_virtualizer_version_matches (self, escape_run_result):
    """

    :type escape_run_result: testframework.runner.EscapeRunResult
    """
    if self._has_message(escape_run_result.log_output,
                         self.VIRTUALIZER_DIFFERENT_VERSION):
      raise AssertionError("Virtualizer version mismatch")

  def _has_message (self, log_content, expected_message):
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

  def _filter_warnings (self, log_lines):
    return [line for line in log_lines if line.startswith("|WARNING")]

  def assert_no_unusual_warnings (self, log_lines):
    warnings = self._filter_warnings(log_lines)
    for log_warn in warnings:
      is_acceptable = False
      for acceptable_warn in self.ACCEPTABLE_WARNINGS:
        if acceptable_warn in log_warn:
          is_acceptable = True
          break
      if not is_acceptable:
        raise AssertionError("Got unusual warning: " + log_warn)


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
    self.command_runner = command_runner
    self.test_case_info = test_case_info

  def run_escape (self):
    command = [os.path.join(self.test_case_info.full_testcase_path,
                            RUNNER_SCRIPT_NAME)]
    try:
      self.command_runner.execute(command)
      # print self.command_runner.last_process
      self.save_run_result()
    except KeyboardInterrupt:
      self.command_runner.kill_process()
      self.save_run_result()
      raise

  def save_run_result (self):
    log_file = self.test_case_info.full_testcase_path + "/escape.log"
    try:
      with open(log_file) as f:
        self.result = EscapeRunResult(output=f.readlines())
    except IOError as e:
      self.result = EscapeRunResult(output=str(e))

  def setUp (self):
    super(EscapeTestCase, self).setUp()
    self.run_escape()

  def __str__ (self):
    return "%s (%s)" % (
      self.test_case_info.testcase_dir_name, strclass(self.__class__))

  def id (self):
    return super(EscapeTestCase, self).id() + str(
      self.test_case_info.full_testcase_path)


class BasicSuccessfulTestCase(EscapeTestCase):
  def runTest (self):
    self.assert_successful_installation(self.result)
    self.assert_no_unusual_warnings(self.result.log_output)
