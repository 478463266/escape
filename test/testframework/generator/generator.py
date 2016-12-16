# Copyright (c) 2016 Balazs Nemeth
#
# This file is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This file is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX. If not, see <http://www.gnu.org/licenses/>.

import e2e_reqs_for_testframework as e2e_reqs
import networkx_nffg_generator as nrg
import sg_generator


def eight_loop_requests (seed=0, **kwargs):
  """
  Request is generated for augmented-dfn-gwin.nffg.
  """
  return sg_generator.get_8loop_request(seed=seed, **kwargs)


def complex_e2e_reqs (seed=0, **kwargs):
  """
  Request is generated for the given NFFG substrate network.
  """
  return e2e_reqs.main(seed=seed, **kwargs)


def networkx_request_generator (gen_func, seed=0, **kwargs):
  """
  Chooses a built-in NetworkX topology generator which creates 
  request graph NFFG.
  """
  return nrg.networkx_request_generator(gen_func, seed=0, **kwargs)
