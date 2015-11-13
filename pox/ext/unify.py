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
  Initiate and run POX with ESCAPE components.

  :param event: POX's going up event
  :type event: GoingUpEvent
  :return: None
  """
  # Launch ESCAPE components
  if init_param['full']:
    # Launch Infrastructure Layer (IL) optionally
    from infrastructure import launch

    launch(topo=init_param['topo'])
  # Launch Controller Adaptation Sublayer (CAS)
  from adaptation import launch

  launch(with_infr=init_param['full'])
  # Launch Resource Orchestration Sublayer (ROS)
  from orchestration import launch

  launch(agent=init_param['agent'], rosapi=init_param['rosapi'],
         cfor=init_param['cfor'])
  if not init_param['agent']:
    # Launch Service Layer (mostly SAS)
    from service import launch

    launch(sg_file=init_param['sg_file'], gui=init_param['gui'])


@poxutil.eval_args
def launch (sg_file='', config=None, gui=False, agent=False, rosapi=False,
            full=False, debug=True, cfor=False, topo=None):
  """
  Launch function called by POX core when core is up.

  :param sg_file: Path of the input Service graph (optional)
  :type sg_file: str
  :param config: additional config file with different name
  :type config: str
  :param gui: Signal for initiate GUI (optional)
  :type gui: bool
  :param agent: Do not start the service layer (optional)
  :type agent: bool
  :param rosapi:
  :param full: Initiate Infrastructure Layer also
  :type full: bool
  :param debug: run in debug mode  (optional)
  :type debug: bool
  :param cfor: start Cf-Or REST API (optional)
  :type cfor: bool
  :param topo: Path of the initial topology graph (optional)
  :type topo: str
  :return: None
  """
  global init_param
  init_param.update(locals())
  # Run POX with DEBUG logging level
  from pox.log.level import launch

  launch(DEBUG=debug)
  # Import colourful logging
  from pox.samples.pretty_log import launch

  launch()
  # Save additional config file name into POX's core as an attribute to avoid to
  # confuse with POX's modules
  if config:
    setattr(core, "config_file_name", config)
  # Register _start_components() to be called when POX is up
  core.addListenerByName("GoingUpEvent", _start_components)
  core.getLogger().info("Starting ESCAPEv2 components...")
