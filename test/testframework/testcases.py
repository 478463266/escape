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
import os
import sys
from unittest.case import TestCase
from unittest.suite import TestSuite

from runner import EscapeRunResult, RunnableTestCaseInfo, CommandRunner

ESCAPE_LOG_FILE_NAME = "escape.log"


class BasicErrorChecker(object):
  """
  Container class for the basic result detection functions.
  """
  WARNING_PREFIX = "|WARNING|"
  ERROR_PREFIX = "|ERROR|"
  CRITICAL_PREFIX = "|CRITICAL|"

  SEPARATOR = "|---|"

  PRE_CONTEXT = 5
  POST_CONTEXT = 5

  RESULT_LOG = "NF-FG instantiation has been finished"
  SUCCESS_RESULT = "DEPLOYED"
  ERROR_RESULT = "DEPLOYMENT_ERROR"

  @classmethod
  def detect_error (cls, result):
    """
    Detect messages logged in ERROR or CRITICAL log level.

    :param result: result object of ESCAPE test run
    :type result: EscapeRunResult
    :return: detected error message
    :rtype: str or None
    """
    for i, line in enumerate(reversed(result.log_output)):
      if line.startswith(cls.ERROR_PREFIX) or \
         line.startswith(cls.CRITICAL_PREFIX):
        pos = len(result.log_output) - i
        return ''.join(
          result.log_output[pos - cls.PRE_CONTEXT:pos + cls.POST_CONTEXT])

  @classmethod
  def detect_unsuccessful_result (cls, result):
    """
    Detect the unsuccessful orchestration message in the result log.

    :param result: result object of ESCAPE test run
    :type result: EscapeRunResult
    :return: detected error message
    :rtype: str or None
    """
    for line in reversed(result.log_output):
      if cls.RESULT_LOG in line:
        if cls.SUCCESS_RESULT in line:
          print "Successful result detected: %s" % line
          return None
        else:
          return line
    return None


class WarningChecker(BasicErrorChecker):
  """
  Container class for the unexpected warning detection functions.
  """
  ACCEPTABLE_WARNINGS = [
    "Unidentified layer name in loaded configuration",
    "Mapping algorithm in Layer: service is disabled!",
    "Mapping algorithm in Layer: orchestration is disabled!",
    "No domain has been detected!",
    "No SGHops were given in the Service Graph!",
    "Resource parameter delay is not given",
    "Version are different!",
    "Resource parameter bandwidth is not given in",
    "If multiple infra nodes are present in the substrate graph",
    "No SAPs could be found,",
    "No SAP - SAP chain were given!",
    "Physical interface:",
    "Skip starting xterms on SAPS according to global config"
  ]

  @classmethod
  def _get_iterator_over_warnings (cls, log):
    """
    Return the iterator which iterates over only the warning logs.

    :param log: logged lines
    :type log: list[str]
    :return: iterator
    """
    return (line.split(cls.SEPARATOR)[-1]
            for line in log if line.startswith(cls.WARNING_PREFIX))

  @classmethod
  def detect_unexpected_warning (cls, result):
    """
    Detect unexpected warning log.

    :param result: result object of ESCAPE test run
    :type result: EscapeRunResult
    :return: detected warning message
    :rtype: str or None
    """
    for warning in cls._get_iterator_over_warnings(result.log_output):
      acceptable = False
      for acc_warn in cls.ACCEPTABLE_WARNINGS:
        if warning.startswith(acc_warn):
          acceptable = True
          break
      if acceptable:
        continue
      else:
        return warning
    return None


class EscapeTestCase(TestCase):
  """
  EscapeTestCase is a test case for the case01, case02 structure. It will run
  ESCAPE
  then place the result into the self.result field.
  You should implement the runTest method to verify the result
  See BasicSuccessfulTestCase
  """

  def __init__ (self, test_case_info, command_runner, **kwargs):
    """
    :type test_case_info: RunnableTestCaseInfo
    :type command_runner: CommandRunner
    """
    super(EscapeTestCase, self).__init__()
    self.test_case_info = test_case_info
    self.command_runner = command_runner
    self.result = None
    """:type result: testframework.runner.EscapeRunResult"""

  def __str__ (self):
    return "Test:\t%s\t(%s)" % (
      self.test_case_info.testcase_dir_name, self.__class__.__name__)

  def id (self):
    return super(EscapeTestCase, self).id() + str(
      self.test_case_info.full_testcase_path)

  def setUp (self):
    """
    Setup the test case fixture.

    :return:
    """
    super(EscapeTestCase, self).setUp()
    log_file = os.path.join(self.test_case_info.full_testcase_path,
                            ESCAPE_LOG_FILE_NAME)
    # Remove escape.log it exists
    if os.path.exists(log_file):
      os.remove(log_file)

  def runTest (self):
    """
    Run the test case and evaluate the result.
    """
    # Run test case
    self.run_escape()
    # Evaluate result
    self.verify_result()

  def tearDown (self):
    """
    Tear down test fixture.
    """
    super(EscapeTestCase, self).tearDown()
    # Cleanup testcase objects if the result was success
    self.command_runner.cleanup()

  def run_escape (self):
    """
    Run ESCAPE with the prepared test config.
    """
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
    """
    Parse the output log to memory as an EscapeResult object.

    :rtype: EscapeRunResult
    """
    log_file = os.path.join(self.test_case_info.full_testcase_path,
                            ESCAPE_LOG_FILE_NAME)
    try:
      with open(log_file) as f:
        return EscapeRunResult(output=f.readlines())
    except IOError as e:
      return EscapeRunResult(output=str(e), exception=e)

  def get_result_from_stream (self):
    """
    Return the buffered ESCAPE log collected by pexpect spawn process.

    :rtype: str
    """
    output_stream = self.command_runner.get_process_output_stream()
    return output_stream if output_stream else ""

  def verify_result (self):
    """
    Template method for analyzing run result.
    """
    raise NotImplementedError('Not implemented yet!')


class BasicSuccessfulTestCase(EscapeTestCase, WarningChecker):
  """
  Basic successful result and warning checking.
  """

  def verify_result (self):
    # Detect ERROR messages first
    detected_error = self.detect_error(self.result)
    self.assertIsNone(detected_error,
                      msg="ERROR detected:\n%s" % detected_error)
    # Search for successful orchestration message
    error_result = self.detect_unsuccessful_result(self.result)
    self.assertIsNone(error_result,
                      msg="Unsuccessful result detected:\n%s" % error_result)
    # Detect unexpected WARNINGs that possibly means abnormal behaviour
    warning = self.detect_unexpected_warning(self.result)
    self.assertIsNone(warning,
                      msg="Unexpected WARNING detected:\n%s" % warning)


class RootPrivilegedSuccessfulTestCase(BasicSuccessfulTestCase):
  """
  Skip the test if the root password is requested on the console.
  """
  SUDO_KILL_TIMEOUT = 2

  def check_root_privilege (self):
    # Due to XMLTestRunner implementation test cannot skip in setUp()
    if CommandRunner("sudo uname",
                     kill_timeout=self.SUDO_KILL_TIMEOUT).execute().is_killed:
      self.skipTest("Root privilege is required to run the testcase: %s" %
                    self.test_case_info.testcase_dir_name)

  def runTest (self):
    # Check root privilege first
    self.check_root_privilege()
    # Run test case
    super(RootPrivilegedSuccessfulTestCase, self).runTest()


class TestCaseBuilder(object):
  """
  Builder class for creating the overall TestSuite object.
  """
  # TODO - check the possibility to refactor to unittest.TestLoader

  DEFAULT_TESTCASE_CLASS = BasicSuccessfulTestCase
  CONFIG_CONTAINER_NAME = "test"

  def __init__ (self, cwd, show_output=False, kill_timeout=None):
    self.cwd = cwd
    self.show_output = show_output
    self.kill_timeout = kill_timeout

  def _create_command_runner (self, case_info):
    """
    Create the specific runner object which runs and optionally kills ESCAPE.

    :type case_info: RunnableTestCaseInfo
    :rtype: CommandRunner
    """
    return CommandRunner(cwd=self.cwd,
                         cmd=case_info.test_command,
                         kill_timeout=self.kill_timeout,
                         output_stream=sys.stdout if self.show_output else None)

  def build_from_config (self, case_info):
    """
    Build a Testcase object based on the test config file and the given test
    case info object.

    :param case_info: config object contains the test case data
    :type case_info: RunnableTestCaseInfo
    :return: instantiated specific TestCase class
    :rtype: EscapeTestCase
    """
    # Check running script
    if not os.path.exists(case_info.test_command):
      raise Exception("Running script: %s for testcase: %s was not found"
                      % (case_info.test_command, case_info.full_testcase_path))
    # Create CommandRunner for test case
    cmd_runner = self._create_command_runner(case_info=case_info)
    # Create TestCase class
    if os.path.exists(case_info.config_file_name):
      TESTCASE_CLASS, test_args = case_info.load_test_case_class()
      if TESTCASE_CLASS:
        return TESTCASE_CLASS(test_case_info=case_info,
                              command_runner=cmd_runner,
                              **test_args)
    return self.DEFAULT_TESTCASE_CLASS(test_case_info=case_info,
                                       command_runner=cmd_runner)

  def to_suite (self, tests):
    """
    Creates the container TestSuite object and populate with the TestCase
    objects based on the given test config objects.

    :param tests: test case config objects
    :type tests: list[RunnableTestCaseInfo]
    :return: overall TestSuite object
    :rtype: TestSuite
    """
    test_cases = [self.build_from_config(case_info) for case_info in tests]
    return TestSuite(test_cases)
