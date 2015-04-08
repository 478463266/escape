# Copyright 2015 Janos Czentye
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
"""
from escape.adapt import log as log


class AbstractDomainAdapter(object):
  """
  Abstract class for different domain adapters

  Follows the Adapter design pattern
  """

  def __init__ (self):
    """
    Init
    """
    super(AbstractDomainAdapter, self).__init__()


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