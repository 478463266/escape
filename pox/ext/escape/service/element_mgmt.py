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
Contains classes relevant to element management

:class:`AbstractElementManager` is an abstract class for element managers

:class:`ClickManager` represent the interface to Click elements
"""


class AbstractElementManager(object):
  """
  Abstract class for element management components (EM)

  :warning::
    Not implemented yet!
  """

  def __init__ (self):
    """
    Init
    """
    pass


class ClickManager(AbstractElementManager):
  """
  Manager class for specific VNF management based on Clicky

  :warning::
    Not implemented yet!
  """

  def __init__ (self):
    """
    Init
    """
    super(ClickManager, self).__init__()