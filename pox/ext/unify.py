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
Basic POX module for ESCAPE

Initiate appropriate APIs

Follows POX module conventions
"""
import pox.lib.util as poxutil
from pox.core import core

# Initial parameters
init_param = {}


# noinspection PyUnusedLocal
def _start_components (event):
  """
  Initiate and run POX with ESCAPE components

  :param event: POX's going up event
  :type event: GoingUpEvent
  :return: None
  """
  # Launch ESCAPE components
  # Launch Service Layer (mostly SAS)
  from sas import launch

  launch(sg_file=init_param['sg_file'], gui=init_param['gui'])
  # Launch Resource Orchestration Sublayer (ROS)
  from ros import launch

  launch()
  # Launch Controller Adaptation Sublayer (CAS)
  from cas import launch

  launch()


@poxutil.eval_args
def launch (sg_file='', gui=False):
  """
  Launch function called by POX core when core is up

  :param sg_file: Path of the input Service graph (optional)
  :type sg_file: str
  :param gui: Signal for initiate GUI (optional)
  :type gui: bool
  :return: None
  """
  global init_param
  init_param.update(locals())

  # Run POX with DEBUG logging level
  from pox.log.level import launch

  launch(DEBUG=True)

  # Import colourful logging
  from pox.samples.pretty_log import launch

  launch()
  # Register _start_components() to be called when POX is up
  core.addListenerByName("GoingUpEvent", _start_components)