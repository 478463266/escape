# Copyright 2015 Janos Czentye, Raphael Vicente Rosa
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
Contains helper classes for conversion between different NF-FG representations.
"""
import json
import sys
import xml.etree.ElementTree as ET

from baseclasses import __version__ as V_VERSION

try:
  # Import for ESCAPEv2
  from escape.nffg_lib.nffg import AbstractNFFG, NFFG
except ImportError:
  import os, inspect

  sys.path.insert(0, os.path.join(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")),
    "pox/ext/escape/nffg_lib/"))
  # Import for standalone running
  from nffg import AbstractNFFG, NFFG

try:
  # Import for ESCAPEv2
  import virtualizer4 as virt_lib
  from virtualizer4 import Flowentry
except ImportError:
  import os, inspect

  sys.path.insert(0, os.path.join(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")),
    "unify_virtualizer"))
  # Import for standalone running
  import virtualizer4 as virt_lib
  from virtualizer4 import Flowentry


class NFFGConverter(object):
  """
  Convert different representation of NFFG in both ways.
  """
  # port types in Virtualizer
  TYPE_VIRTUALIZER_PORT_ABSTRACT = "port-abstract"
  TYPE_VIRTUALIZER_PORT_SAP = "port-sap"
  # General option names in mapped NFFG assembled by the Mapping algorithm
  OP_TAG = 'TAG'
  OP_UNTAG = 'UNTAG'
  OP_INPORT = 'in_port'
  OP_OUTPUT = 'output'
  GENERAL_OPERATIONS = (OP_INPORT, OP_OUTPUT, OP_TAG, OP_UNTAG)
  # Specific tags
  TAG_SG_HOP = "sg_hop"
  # Operation formats in Virtualizer
  MATCH_TAG = r"dl_tag"
  ACTION_PUSH_TAG = r"push_tag"
  ACTION_POP_TAG = r"pop_tag"
  # Operand separator
  LABEL_SEPARATOR = '|'
  OP_SEPARATOR = ';'
  KV_SEPARATOR = '='
  # Field types
  TYPE_MATCH = "MATCH"
  TYPE_ACTION = "ACTION"
  # Hard-coded constants
  REQUIREMENT_PREFIX = "REQ"

  def __init__ (self, domain=None, logger=None, ensure_unique_id=None):
    # Save domain name for define domain attribute in infras
    self.domain = domain
    # If clarify_id is True, add domain name as a prefix to the node ids
    self.ensure_unique_id = ensure_unique_id
    self.log = logger if logger is not None else logging.getLogger(__name__)

  @classmethod
  def field_splitter (cls, type, field):
    """
    Split the match/action field into a dict-based format for flowrule creation.

    :param type: the name of the field ('MATCH' or 'ACTION')
    :type type: str
    :param field: field data
    :type field: str
    :return: splitted data structure
    :rtype: dict
    """
    # match = {}
    # action = {}
    # # if re.search(r';', flowrule.match):
    # #   # multiple elements in match field
    # #   in_port = re.sub(r'.*in_port=(.*);.*', r'\1', flowrule.match)
    # # else:
    # #   # single element in match field
    # #   in_port = re.sub(r'.*in_port=(.*)', r'\1', flowrule.match)
    # match['in_port'] = port.id
    # # Check match fields - currently only vlan_id
    # # TODO: add further match fields
    # if re.search(r'TAG', flowrule.match):
    #   tag = re.sub(r'.*TAG=.*\|(.*);?', r'\1', flowrule.match)
    #   match['vlan_id'] = tag
    #
    # if re.search(r';', flowrule.action):
    #   # multiple elements in action field
    #   out = re.sub(r'.*output=(.*);.*', r'\1', flowrule.action)
    # else:
    #   # single element in action field
    #   out = re.sub(r'.*output=(.*)', r'\1', flowrule.action)
    # action['out'] = out
    #
    # if re.search(r'TAG', flowrule.action):
    #   if re.search(r'UNTAG', flowrule.action):
    #     action['vlan_pop'] = True
    #   else:
    #     push_tag = re.sub(r'.*TAG=.*\|(.*);?', r'\1', flowrule.action)
    #     action['vlan_push'] = push_tag
    ret = {}
    parts = field.split(cls.OP_SEPARATOR)
    if len(parts) < 1:
      raise RuntimeError(
        "Wrong format: %s! Separator (%s) not found!" % (
          field, cls.OP_SEPARATOR))
    for part in parts:
      kv = part.split(cls.KV_SEPARATOR)
      if len(kv) != 2:
        if kv[0] == cls.OP_UNTAG and type.upper() == cls.TYPE_ACTION:
          ret['vlan_pop'] = True
          continue
        else:
          raise RuntimeError("Not a key-value pair: %s" % part)
      if kv[0] == cls.OP_INPORT:
        try:
          ret['in_port'] = int(kv[1])
        except ValueError:
          # log.warning(
          #    "in_port is not a valid port number: %s! Skip "
          #    "converting..." % kv[1])
          ret['in_port'] = kv[1]
      elif kv[0] == cls.OP_TAG:
        if type.upper() == cls.TYPE_MATCH:
          ret['vlan_id'] = kv[1].split(cls.LABEL_SEPARATOR)[-1]
        elif type.upper() == cls.TYPE_ACTION:
          ret['vlan_push'] = kv[1].split(cls.LABEL_SEPARATOR)[-1]
        else:
          raise RuntimeError('Not supported field type: %s!' % type)
      elif kv[0] == cls.OP_OUTPUT:
        ret['out'] = kv[1]
      else:
        raise RuntimeError("Unrecognizable key: %s" % kv[0])
    return ret

  def _convert_flowrule_match (self, match):
    """
    Convert Flowrule match field from NFFG format to a unified format used by
    the Virtualizer.

    Based on Open vSwitch syntax:
    http://openvswitch.org/support/dist-docs/ovs-ofctl.8.txt

    :param match: flowrule match field
    :type match: str
    :return: converted data
    :rtype: str
    """
    # E.g.:  "match": "in_port=1;TAG=SAP1|comp|1" -->
    # E.g.:  "match": "in_port=SAP2|fwd|1;TAG=SAP1|comp|1" -->
    # <match>(in_port=1)dl_tag=1</match>
    ret = []
    match_part = match.split(';')
    if len(match_part) < 2:
      if not match_part[0].startswith("in_port"):
        self.log.warning("Invalid match field: %s" % match)
      return
    for kv in match_part:
      op = kv.split('=')
      if op[0] not in self.GENERAL_OPERATIONS:
        self.log.warning("Unsupported match operand: %s" % op[0])
        continue
      if op[0] == self.OP_TAG:
        try:
          vlan_tag = int(op[1].split('|')[-1])
          ret.append("%s=%s" % (self.MATCH_TAG, format(vlan_tag, '#06x')))
        except ValueError:
          self.log.warning(
            "Wrong VLAN format: %s!" % op[1])
          continue
          # elif op[0] == self.OP_SGHOP:
          #   ret.append(kv)
    return self.OP_SEPARATOR.join(ret)

  def _convert_flowrule_action (self, action):
    """
    Convert Flowrule action field from NFFG format to a unified format used by
    the Virtualizer.

    Based on Open vSwitch syntax:
    http://openvswitch.org/support/dist-docs/ovs-ofctl.8.txt

    :param action: flowrule action field
    :type action: str
    :return: converted data
    :rtype: str
    """
    # E.g.:  "action": "output=2;UNTAG"
    ret = []
    action_part = action.split(';')
    if len(action_part) < 2:
      if not action_part[0].startswith("output"):
        self.log.warning("Invalid action field: %s" % action)
      return
    for kv in action_part:
      op = kv.split('=')
      if op[0] not in self.GENERAL_OPERATIONS:
        self.log.warning("Unsupported action operand: %s" % op[0])
        return
      if op[0] == self.OP_TAG:
        # E.g.: <action>push_tag:0x0037</action>
        try:
          vlan = int(op[1].split('|')[-1])
          ret.append("%s:%s" % (self.ACTION_PUSH_TAG, format(vlan, '#06x')))
        except ValueError:
          self.log.warning(
            "Wrong VLAN format: %s! Skip flowrule conversion..." % op[1])
          continue
      elif op[0] == self.OP_UNTAG:
        # E.g.: <action>strip_vlan</action>
        ret.append(self.ACTION_POP_TAG)
    return self.OP_SEPARATOR.join(ret)

  def _parse_virtualizer_node_ports (self, nffg, infra, vnode):
    """
    Parse ports from a Virtualizer node into an :any:`NodeInfra` node.

    :param nffg: Container NFFG
    :type nffg: :any:`NFFG`
    :param infra: infrastructure node
    :type infra: :any:`NodeInfra`
    :param vnode: Virtualizer node
    :type vnode: Infra_node
    :return: None
    """
    # Add ports to Infra Node
    for vport in vnode.ports:
      # If it is a port connected to a SAP
      if vport.port_type.get_value() == self.TYPE_VIRTUALIZER_PORT_SAP:
        # If inter-domain SAP -> id = <sap> tag
        if vport.sap.is_initialized():
          # Use unique SAP tag as the id of the SAP
          sap_id = vport.sap.get_value()  # Optional port.sap
        # Regular SAP
        else:
          # Use port name as the SAP.id if it is set else generate one
          # SAP.id <--> virtualizer.node.port.name
          if vport.name.is_initialized():
            sap_id = vport.name.get_value()
          else:
            # Backup SAP id generation
            sap_id = "SAP%s" % len([s for s in nffg.saps])
        try:
          # Use port id of the Infra node as the SAP port id
          # because sap port info was lost during NFFG->Virtualizer conversion
          sap_port_id = int(vport.id.get_value())  # Mandatory port.id
        except ValueError:
          sap_port_id = vport.id.get_value()
        # SAP.name will be the same as the SAP.id or generate one for backup
        if vport.name.is_initialized():
          sap_name = vport.name.get_value()  # Optional - port.name
        else:
          sap_name = "name-%s" % sap_id
        # Create SAP and Add port to SAP
        sap = nffg.add_sap(id=sap_id, name=sap_name)

        self.log.debug("Created SAP node: %s" % sap)

        sap_port = sap.add_port(id=sap_port_id)
        # Add port properties as metadata to SAP port
        if vport.name.is_initialized():
          sap_port.add_property("name", vport.name.get_value())
        if vport.sap.is_initialized():
          sap_port.add_property("sap", vport.sap.get_value())

        self.log.debug("Added SAP port: %s" % sap_port)

        # Add metadata from infra port metadata to sap metadata
        for key in vport.metadata:  # Optional - port.metadata
          sap.add_metadata(name=key,
                           value=vport.metadata[key].value.get_value())

        # Create and add the port of the opposite Infra node
        try:
          infra_port_id = int(vport.id.get_value())
        except ValueError:
          infra_port_id = vport.id.get_value()
        # Add port to Infra
        infra_port = infra.add_port(id=infra_port_id)
        # Add port properties as property to Infra port too
        if vport.name.is_initialized():
          infra_port.add_property("name", vport.name.get_value())
        if vport.sap.is_initialized():
          infra_port.add_property("sap", vport.sap.get_value())
        # Add infra port capabilities
        if vport.capability.is_initialized():
          infra_port.add_property("capability", vport.capability.get_value())

        self.log.debug("Added port for SAP -> %s" % infra_port)

        # Add connection between infra - SAP
        # SAP-Infra is static link --> create link for both direction
        l1, l2 = nffg.add_undirected_link(
          p1p2id="%s-%s-link" % (sap_id, infra.id),
          p2p1id="%s-%s-link-back" % (sap_id, infra.id),
          port1=sap_port,
          port2=infra_port)

        self.log.debug("Added SAP-Infra connection: %s" % l1)
        self.log.debug("Added Infra-SAP connection: %s" % l2)

      # If it is not SAP port and probably connected to another infra
      elif vport.port_type.get_value() == self.TYPE_VIRTUALIZER_PORT_ABSTRACT:
        # Add Infra port
        try:
          infra_port_id = int(vport.id.get_value())
        except ValueError:
          infra_port_id = vport.id.get_value()
        # Add port properties as property to Infra port
        infra_port = infra.add_port(id=infra_port_id)
        if vport.name.is_initialized():
          infra_port.add_property("name", vport.name.get_value())
        # If sap is set and port_type is port-abstract -> this port
        # connected to an inter-domain SAP before -> save this metadata
        if vport.sap.is_initialized():
          infra_port.add_property("sap", vport.sap.get_value())
        if vport.capability.is_initialized():
          infra_port.add_property(
            "capability", vport.capability.get_value())
        # Add metadata from non-sap port to infra port properties
        for key in vport.metadata:
          infra_port.add_property(property=key,
                                  value=vport.metadata[key].value.get_value())

        self.log.debug("Added static %s" % infra_port)
      else:
        raise RuntimeError(
          "Unsupported port type: %s" % vport.port_type.get_value())

  def _parse_virtualizer_node_nfs (self, nffg, infra, vnode):
    """
    Parse VNFs from a Virtualizer nodes into :any:`NodeNF` list.

    :param nffg: Container NFFG
    :type nffg: :any:`NFFG`
    :param infra: infrastructure node
    :type infra: :any:`NodeInfra`
    :param vnode: Virtualizer node
    :type vnode: Infra_node
    :return: None
    """
    # Create NF instances
    for v_vnf in vnode.NF_instances:
      # Get NF params
      nf_id = v_vnf.id.get_value()  # Mandatory - nf.id
      nf_name = v_vnf.name.get_value()  # Optional - nf.name, default = None
      nf_ftype = v_vnf.type.get_value()  # Optional - nf.type, default = None
      # No deployment_type in Virtualizer try to get if from metadata
      if 'deployment_type' in v_vnf.metadata.keys():
        nf_dep_type = v_vnf.metadata['deployment_type'].value.get_value()
      else:
        nf_dep_type = None
      # Add NF resources, remove optional units
      if v_vnf.resources.is_initialized():
        nf_cpu = v_vnf.resources.cpu.get_as_text().split(' ')[0]
        nf_mem = v_vnf.resources.mem.get_as_text().split(' ')[0]
        nf_storage = v_vnf.resources.storage.get_as_text().split(' ')[0]
        try:
          nf_cpu = float(nf_cpu)
        except ValueError as e:
          self.log.warning("Resource cpu value is not valid number: %s" % e)
        try:
          nf_mem = float(nf_mem)
        except ValueError as e:
          self.log.warning("Resource mem value is not valid number: %s" % e)
        try:
          nf_storage = float(nf_storage)
        except ValueError as e:
          self.log.warning(
            "Resource storage value is not valid number: %s" % e)
      else:
        nf_cpu = nf_mem = nf_storage = None
      # Get remained NF resources from metadata
      if 'delay' in v_vnf.metadata.keys():
        nf_delay = v_vnf.metadata['delay'].value.get_value()
      else:
        nf_delay = None
      if 'bandwidth' in v_vnf.metadata.keys():
        nf_bandwidth = v_vnf.metadata['bandwidth'].value.get_value()
      else:
        nf_bandwidth = None
      # Create NodeNF
      nf = nffg.add_nf(id=nf_id, name=nf_name, func_type=nf_ftype,
                       dep_type=nf_dep_type, cpu=nf_cpu, mem=nf_mem,
                       storage=nf_storage, delay=nf_delay,
                       bandwidth=nf_bandwidth)

      self.log.debug("Created NF: %s" % nf)

      # Add NF metadata
      for key in v_vnf.metadata:
        if key not in ('delay', 'bandwidth'):
          nf.add_metadata(name=key,
                          value=v_vnf.metadata[key].value.get_value())

      # Create NF ports
      for vport in v_vnf.ports:
        # Add VNF port
        try:
          nf_port_id = int(vport.id.get_value())
        except ValueError:
          nf_port_id = vport.id.get_value()
        # Create and Add port
        nf_port = nf.add_port(id=nf_port_id)
        # Add port properties as metadata to NF port
        if vport.capability.is_initialized():
          nf_port.add_property(
            "capability", vport.capability.get_value())
        if vport.name.is_initialized():
          nf_port.add_property("name", vport.name.get_value())
        # Add port properties
        for key in vport.metadata:
          nf_port.add_property(property=key,
                               value=vport.metadata[key].value.get_value())
        # VNF port can not be a SAP port -> skip <port_type> saving
        # VNF port can not be a SAP port -> skip <sap> saving

        self.log.debug("Added NF port: %s" % nf_port)

        # Add connection between Infra - NF
        # Infra - NF port on Infra side is always a dynamically generated port
        dyn_port = self.LABEL_SEPARATOR.join((infra.id,
                                              nf_id,
                                              vport.id.get_as_text()))
        # Add Infra-side port
        infra_port = infra.add_port(id=dyn_port)
        self.log.debug("Added dynamic port for NF -> %s" % infra_port)

        # NF-Infra is dynamic link --> create special undirected link
        l1, l2 = nffg.add_undirected_link(port1=nf_port,
                                          port2=infra_port,
                                          dynamic=True)
        self.log.debug("Added dynamic VNF-Infra connection: %s" % l1)
        self.log.debug("Added dynamic Infra-VNF connection: %s" % l2)

  def _parse_virtualizer_node_flowentries (self, nffg, infra, vnode):
    """
    Parse FlowEntries from a Virtualizer Node into an :any:`InfraPort`.

    :param nffg: Container NFFG
    :type nffg: :any:`NFFG`
    :param infra: infrastructure node
    :type infra: :any:`NodeInfra`
    :param vnode: Virtualizer node
    :type vnode: Infra_node
    :return: None
    """
    # Create Flowrules
    for flowentry in vnode.flowtable:
      fr_id = flowentry.id.get_value()  # Mandatory flowentry.id
      # e.g. in_port=1(;TAG=SAP1|comp|1)
      v_fe_port = flowentry.port.get_target()
      fr_match = "in_port="
      # Check if src port is a VNF port --> create the tagged port name
      if "NF_instances" in flowentry.port.get_as_text():
        v_src_nf = v_fe_port.get_parent().get_parent()
        v_src_node = v_src_nf.get_parent().get_parent()
        # Add domain name to the node id if unique_id is set
        if self.ensure_unique_id:
          src_node = "%s@%s" % (v_src_node.id.get_value(), self.domain)
        else:
          src_node = v_src_node.id.get_as_text()
        fr_match += self.LABEL_SEPARATOR.join((src_node,
                                               v_src_nf.id.get_as_text(),
                                               v_fe_port.id.get_as_text()))
      else:
        # Else just Infra port --> add only the port number
        fr_match += v_fe_port.id.get_as_text()

      v_fe_out = flowentry.out.get_target()
      fr_action = "output="
      # Check if dst port is a VNF port --> create the tagged port name
      if "NF_instances" in flowentry.out.get_as_text():
        v_dst_nf = v_fe_out.get_parent().get_parent()
        v_dst_node = v_dst_nf.get_parent().get_parent()
        if self.ensure_unique_id:
          dst_node = "%s@%s" % (v_dst_node.id.get_value(), self.domain)
        else:
          dst_node = v_dst_node.id.get_as_text()
        fr_action += self.LABEL_SEPARATOR.join((dst_node,
                                                v_dst_nf.id.get_as_text(),
                                                v_fe_out.id.get_as_text()))
      else:
        # Else just Infra port --> add only the port number
        fr_action += v_fe_out.id.get_as_text()

      # Check if there is a matching operation -> currently just TAG is used
      if flowentry.match.is_initialized() and flowentry.match.get_value():
        for op in flowentry.match.get_as_text().split(self.OP_SEPARATOR):
          # e.g. <match>dl_tag=0x0004</match> --> in_port=1;TAG=SAP2|fwd|4
          if op.startswith(self.MATCH_TAG):
            # if src or dst was a SAP: SAP.id == port.name
            # if scr or dst is a VNF port name of parent of port
            if v_fe_port.port_type.get_as_text() == \
               self.TYPE_VIRTUALIZER_PORT_SAP:
              _src_name = v_fe_port.name.get_as_text()
            else:
              _src_name = v_fe_port.get_parent().get_parent().id.get_as_text()
            if v_fe_out.port_type.get_as_text() == \
               self.TYPE_VIRTUALIZER_PORT_SAP:
              _dst_name = v_fe_out.name.get_as_text()
            else:
              _dst_name = v_fe_out.get_parent().get_parent().id.get_as_text()
            # Convert from int/hex to int
            _tag = int(op.split('=')[1], base=0)
            fr_match += ";%s=%s" % (self.OP_TAG, self.LABEL_SEPARATOR.join(
              (str(_src_name), str(_dst_name), str(_tag))))

      # Check if there is an action operation
      if flowentry.action.is_initialized() and flowentry.action.get_value():
        for op in flowentry.action.get_as_text().split(self.OP_SEPARATOR):
          # e.g. <action>push_tag:0x0003</action> -->
          # output=1;TAG=decomp|SAP2|3
          if op.startswith(self.ACTION_PUSH_TAG):
            # tag: src element name | dst element name | tag
            # if src or dst was a SAP: SAP.id == port.name
            # if scr or dst is a VNF port name of parent of port
            if v_fe_port.port_type.get_as_text() == \
               self.TYPE_VIRTUALIZER_PORT_SAP:
              _src_name = v_fe_port.name.get_as_text()
            else:
              _src_name = v_fe_port.get_parent().get_parent().id.get_as_text()
            if v_fe_out.port_type.get_as_text() == \
               self.TYPE_VIRTUALIZER_PORT_SAP:
              _dst_name = v_fe_out.name.get_as_text()
            else:
              _dst_name = v_fe_out.get_parent().get_parent().id.get_as_text()
            # Convert from int/hex to int
            _tag = int(op.split(':')[1], base=0)
            fr_action += ";%s=%s" % (self.OP_TAG, self.LABEL_SEPARATOR.join(
              (_src_name, _dst_name, str(_tag))))
          # e.g. <action>strip_vlan</action> --> output=EE2|fwd|1;UNTAG
          elif op.startswith(self.ACTION_POP_TAG):
            fr_action += ";%s" % self.OP_UNTAG

      # Get the src (port where fr need to store) and dst port id
      try:
        vport_id = int(v_fe_port.id.get_value())
      except ValueError:
        vport_id = v_fe_port.id.get_value()

      # Get port from NFFG in which need to store the fr
      try:
        # If the port is an Infra port
        if "NF_instances" not in flowentry.port.get_as_text():
          vport = nffg[infra.id].ports[vport_id]
        # If the port is a VNF port -> get the dynamic port in the Infra
        else:
          _vnf_id = v_fe_port.get_parent().get_parent().id.get_value()
          _dyn_port = [l.dst.id for u, v, l in
                       nffg.network.edges_iter([_vnf_id], data=True) if
                       l.type == NFFG.TYPE_LINK_DYNAMIC and str(l.src.id) ==
                       str(vport_id)]
          if len(_dyn_port) > 1:
            self.log.warning(
              "Multiple dynamic link detected for NF(id: %s) Use first "
              "link ..." % _vnf_id)
          elif len(_dyn_port) < 1:
            raise RuntimeError(
              "Missing infra-vnf dynamic link for vnf: %s" % _vnf_id)
          # Get dynamic port from infra
          vport = nffg[infra.id].ports[_dyn_port[0]]
      except RuntimeError as e:
        self.log.error(
          "Port: %s is not found in the NFFG: %s from the flowrule:\n%s" % (
            vport_id, e.message, flowentry))
        continue

      # Get resource values
      if flowentry.resources.is_initialized():
        if flowentry.resources.bandwidth.is_initialized():
          try:
            fr_bw = float(flowentry.resources.bandwidth.get_value())
          except ValueError:
            fr_bw = flowentry.resources.bandwidth.get_value()
        else:
          fr_bw = None
        if flowentry.resources.delay.is_initialized():
          try:
            fr_delay = float(flowentry.resources.delay.get_value())
          except ValueError:
            fr_delay = flowentry.resources.delay.get_value()
        else:
          fr_delay = None
      else:
        fr_bw = fr_delay = None

      # Get hop_id
      fr_hop_id = None
      if flowentry.name.is_initialized():
        if not flowentry.name.get_as_text().startswith(self.TAG_SG_HOP):
          log.warning(
            "Flowrule's name: %s is not following the SG hop naming "
            "convention! SG hop for %s is undefined...") % (
            flowentry.name.get_as_text(), flowentry)
        fr_hop_id = flowentry.name.get_as_text().split(':')[1]

      # Add flowrule to port
      fr = vport.add_flowrule(id=fr_id, match=fr_match, action=fr_action,
                              bandwidth=fr_bw, delay=fr_delay,
                              hop_id=fr_hop_id)

      self.log.debug("Added %s" % fr)

  def _parse_virtualizer_nodes (self, nffg, virtualizer):
    """
    Parse Infrastructure node from Virtualizer.

    :param nffg: Container NFFG
    :type nffg: :any:`NFFG`
    :param virtualizer: Virtualizer object
    :type virtualizer: Virtualizer
    :return: None
    """
    # Iterate over virtualizer/nodes --> node = Infra
    for vnode in virtualizer.nodes:
      # Node params
      if self.ensure_unique_id:
        # Add domain name to the node id if unique_id is set
        node_id = "%s@%s" % (vnode.id.get_value(), self.domain)
      else:
        node_id = vnode.id.get_value()  # Mandatory - node.id
      if vnode.name.is_initialized():  # Optional - node.name
        node_name = vnode.name.get_value()
      else:
        node_name = "name-" + node_id
      node_domain = self.domain  # Set domain as the domain of the Converter
      node_type = vnode.type.get_value()  # Mandatory - virtualizer.type
      # Node-resources params
      if vnode.resources.is_initialized():
        # Remove units and store the value only
        node_cpu = vnode.resources.cpu.get_as_text().split(' ')[0]
        node_mem = vnode.resources.mem.get_as_text().split(' ')[0]
        node_storage = vnode.resources.storage.get_as_text().split(' ')[0]
        try:
          node_cpu = float(node_cpu)
        except ValueError as e:
          self.log.warning("Resource cpu value is not valid number: %s" % e)
        try:
          node_mem = float(node_mem)
        except ValueError as e:
          self.log.warning("Resource mem value is not valid number: %s" % e)
        try:
          node_storage = float(node_storage)
        except ValueError as e:
          self.log.warning("Resource storage value is not valid number: %s" % e)
      else:
        # Default value for cpu,mem,storage: None
        node_cpu = node_mem = node_storage = None
      # Try to get bw value from metadata
      if 'bandwidth' in vnode.metadata:
        # Converted to float in Infra constructor
        node_bw = vnode.metadata['bandwidth'].value.get_value()
      else:
        # Iterate over links to summarize bw value for infra node
        node_bw = [
          float(vlink.resources.bandwidth.get_value())
          for vlink in vnode.links if vlink.resources.is_initialized() and
          vlink.resources.bandwidth.is_initialized()]
        # Default value: None
        node_bw = min(node_bw) if node_bw else None
      try:
        node_bw = float(node_bw)
      except ValueError as e:
        self.log.warning(
          "Resource bandwidth value is not valid number: %s" % e)
      if 'delay' in vnode.metadata:
        # Converted to float in Infra constructor
        node_delay = vnode.metadata['delay'].value.get_value()
      else:
        # Iterate over links to summarize delay value for infra node
        node_delay = [
          float(vlink.resources.delay.get_value())
          for vlink in vnode.links if vlink.resources.is_initialized() and
          vlink.resources.delay.is_initialized()]
        # Default value: None
        node_delay = max(node_delay) if node_delay else None
      try:
        node_delay = float(node_delay)
      except ValueError as e:
        self.log.warning("Resource delay value is not valid number: %s" % e)
      # Add Infra Node to NFFG
      infra = nffg.add_infra(id=node_id, name=node_name, domain=node_domain,
                             infra_type=node_type, cpu=node_cpu, mem=node_mem,
                             storage=node_storage, delay=node_delay,
                             bandwidth=node_bw)

      self.log.debug("Created INFRA node: %s" % infra)
      self.log.debug("Parsed resources: %s" % infra.resources)

      # Add supported types shrinked from the supported NF list
      for sup_nf in vnode.capabilities.supported_NFs:
        infra.add_supported_type(sup_nf.type.get_value())

      # Copy metadata
      for key in vnode.metadata:  # Optional - node.metadata
        if key not in ('bandwidth', 'delay'):
          infra.add_metadata(name=key,
                             value=vnode.metadata[key].value.get_value())

      # Parse Ports
      self._parse_virtualizer_node_ports(nffg=nffg, infra=infra, vnode=vnode)

      # Parse NF_instances
      self._parse_virtualizer_node_nfs(nffg=nffg, infra=infra, vnode=vnode)

      # Parse Flowentries
      self._parse_virtualizer_node_flowentries(nffg=nffg, infra=infra,
                                               vnode=vnode)

  def _parse_virtualizer_links (self, nffg, virtualizer):
    """
    Parse links from Virtualizer.

    :param nffg: Container NFFG
    :type nffg: :any:`NFFG`
    :param virtualizer: Virtualizer object
    :type virtualizer: Virtualizer
    :return: None
    """
    # Store added link in a separate structure for simplicity and speed
    added_links = []
    # Add links connecting infras
    for vlink in virtualizer.links:
      src_port = vlink.src.get_target()
      src_node = src_port.get_parent().get_parent()
      # Add domain name to the node id if unique_id is set
      if self.ensure_unique_id:
        src_node_id = "%s@%s" % (src_node.id.get_value(), self.domain)
      else:
        src_node_id = src_node.id.get_value()
      dst_port = vlink.dst.get_target()
      dst_node = dst_port.get_parent().get_parent()
      # Add domain name to the node id if unique_id is set
      if self.ensure_unique_id:
        dst_node_id = "%s@%s" % (dst_node.id.get_value(), self.domain)
      else:
        dst_node_id = dst_node.id.get_value()
      try:
        src_port_id = int(src_port.id.get_value())
      except ValueError as e:
        # self.log.warning("Source port id is not a valid number: %s" % e)
        src_port_id = src_port.id.get_value()
      try:
        dst_port_id = int(dst_port.id.get_value())
      except ValueError as e:
        # self.log.warning("Destination port id is not a valid number: %s" % e)
        dst_port_id = dst_port.id.get_value()
      params = dict()
      params['id'] = vlink.id.get_value()  # Mandatory - link.id
      if vlink.resources.is_initialized():
        params['delay'] = float(vlink.resources.delay.get_value()) \
          if vlink.resources.delay.is_initialized() else None
        params['bandwidth'] = float(vlink.resources.bandwidth.get_value()) \
          if vlink.resources.bandwidth.is_initialized() else None
      # Check the link is a possible backward link
      possible_backward = (
        "%s:%s-%s:%s" % (dst_node_id, dst_port_id, src_node_id, src_port_id))
      if possible_backward in added_links:
        params['backward'] = True
      # Add unidirectional link
      l1 = nffg.add_link(src_port=nffg[src_node_id].ports[src_port_id],
                         dst_port=nffg[dst_node_id].ports[dst_port_id],
                         **params)
      self.log.debug("Add static %slink: %s" % (
        "backward " if "backward" in params else "", l1))
      # Register the added link
      added_links.append(
        "%s:%s-%s:%s" % (src_node, src_port, dst_node, dst_port))

  def _parse_virtualizer_metadata (self, nffg, virtualizer):
    """
    Parse metadata from Virtualizer.

    Optionally can parse requirement links if they are stored in metadata.

    :param nffg: Container NFFG
    :type nffg: :any:`NFFG`
    :param virtualizer: Virtualizer object
    :type virtualizer: Virtualizer
    :return: None
    """
    for key in virtualizer.metadata:
      # If it is a compressed Requirement links
      if key.startswith(self.REQUIREMENT_PREFIX):
        req_id = key.split(':')[1]
        # Replace pre-converted ' to " to get valid JSON
        raw = virtualizer.metadata[key].value.get_value().replace("'", '"')
        values = json.loads(raw)
        try:
          values['bw'] = float(values['bw'])
        except ValueError:
          self.log.warning("Bandwidth in requirement metadata: %s is not a "
                           "valid float value!" % values['bw'])
        try:
          values['delay'] = float(values['delay'])
        except ValueError:
          self.log.warning("Delay in requirement metadata: %s is not a "
                           "valid float value!" % values['delay'])
        req = nffg.add_req(
          id=req_id,
          src_port=nffg[values['snode']].ports[values['sport']],
          dst_port=nffg[values['dnode']].ports[values['dport']],
          delay=values['delay'],
          bandwidth=values['bw'],
          sg_path=values['sg_path'])
        self.log.debug("Parsed Requirement link: %s" % req)
      # If it is just a metadata
      else:
        nffg.add_metadata(name=key,
                          value=virtualizer.metadata[key].value.get_value())

  def parse_from_Virtualizer (self, xml_data, with_virt=False):
    """
    Convert Virtualizer3-based XML str --> NFFGModel based NFFG object

    :param xml_data: XML plain data or Virtualizer object
    :type: xml_data: str or Virtualizer
    :param with_virt: return with the Virtualizer object too (default: False)
    :type with_virt: bool
    :return: created NF-FG
    :rtype: :any:`NFFG`
    """
    self.log.debug(
      "START conversion: Virtualizer(ver: %s) --> NFFG(ver: %s)" % (
        3, NFFG.version))
    # Already in Virtualizer format
    if isinstance(xml_data, virt_lib.Virtualizer):
      virtualizer = xml_data
    # Plain XML string
    elif isinstance(xml_data, basestring):
      try:
        self.log.debug("Converting data to graph-based NFFG structure...")
        # Parse given str to XML structure
        tree = ET.ElementTree(ET.fromstring(xml_data))
        # Parse Virtualizer structure
        self.log.debug("Parsing XML data to Virtualizer format...")
        virtualizer = virt_lib.Virtualizer().parse(root=tree.getroot())
      except ET.ParseError as e:
        self.log.error("Got ParseError during XML->Virtualizer conversion!")
        raise RuntimeError('ParseError: %s' % e.message)
    else:
      log.error("Not supported type for xml_data: %s" % type(xml_data))
      return
    # Get NFFG init params
    nffg_id = virtualizer.id.get_value()  # Mandatory - virtualizer.id
    if virtualizer.name.is_initialized():  # Optional - virtualizer.name
      nffg_name = virtualizer.name.get_value()
    else:
      nffg_name = "NFFG-domain-%s" % self.domain
    self.log.debug("Construct NFFG based on Virtualizer(id=%s, name=%s)" % (
      nffg_id, nffg_name))
    # Create NFFG
    nffg = NFFG(id=nffg_id, name=nffg_name)
    # Parse Infrastructure Nodes from Virtualizer
    self._parse_virtualizer_nodes(nffg=nffg, virtualizer=virtualizer)
    # Parse Infrastructure links from Virtualizer
    self._parse_virtualizer_links(nffg=nffg, virtualizer=virtualizer)
    # Parse Metadata and Requirement links from Virtualizer
    self._parse_virtualizer_metadata(nffg=nffg, virtualizer=virtualizer)
    self.log.debug("END conversion: Virtualizer(ver: %s) --> NFFG(ver: %s)" % (
      3, NFFG.version))
    return (nffg, virtualizer) if with_virt else nffg

  def _convert_nffg_infras (self, nffg, virtualizer):
    """
    Convert infras in the given :any:`NFFG` into the given Virtualizer.

    :param nffg: NFFG object
    :type nffg: :any:`NFFG`
    :param virtualizer: Virtualizer object
    :type virtualizer: Virtualizer
    :return: None
    """
    self.log.info("Converting infras...")
    for infra in nffg.infras:
      # Check in it's needed to remove domain from the end of id
      if self.ensure_unique_id:
        v_node_id = str(infra.id).split('@')[0]
      else:
        v_node_id = str(infra.id)
      v_node_name = str(infra.name) if infra.name else None  # optional
      v_node_type = str(infra.infra_type)  # Mandatory
      v_node = virt_lib.Infra_node(id=v_node_id,
                                   name=v_node_name,
                                   type=v_node_type)
      # Add resources nodes/node/resources
      if infra.resources.cpu is not None:
        v_node.resources.cpu.set_value(str(infra.resources.cpu))
      if infra.resources.mem is not None:
        v_node.resources.mem.set_value(str(infra.resources.mem))
      if infra.resources.storage is not None:
        v_node.resources.storage.set_value(str(infra.resources.storage))

      # Migrate metadata
      for key, value in infra.metadata.iteritems():
        meta_key = str(key)
        meta_value = str(value) if value is not None else None
        v_node.metadata.add(
          virt_lib.MetadataMetadata(key=meta_key, value=meta_value))

      # Add remained NFFG-related information into metadata
      if infra.resources.delay is not None:
        node_delay = str(infra.resources.delay)
        v_node.metadata.add(
          virt_lib.MetadataMetadata(key="delay", value=node_delay))
      if infra.resources.bandwidth is not None:
        node_bandwidth = str(infra.resources.bandwidth)
        v_node.metadata.add(
          virt_lib.MetadataMetadata(key="bandwidth", value=str(node_bandwidth)))
      self.log.debug("Converted %s" % infra)

      # Add ports to infra
      for port in infra.ports:
        # Check if the port is a dynamic port : 23412423523445 or sap1|comp|1
        # If it is a dynamic port, skip conversion
        try:
          if not int(port.id) < 65536:
            # Dynamic port connected to a VNF - skip
            continue
        except ValueError:
          # port is not a number
          if '|' in str(port.id):
            continue
        v_port = virt_lib.Port(id=str(port.id))
        # Detect Port properties
        if port.get_property('name'):
          v_port.name.set_value(port.get_property('name'))
        if port.get_property('capability'):
          v_port.capability.set_value(port.get_property('capability'))
        # If SAP property is exist: this port connected to a SAP
        if port.get_property('sap'):
          v_port.sap.set_value(port.get_property('sap'))
        # Set default port-type to port-abstract
        # during SAP detection the SAP<->Node port-type will be overridden
        v_port.port_type.set_value(self.TYPE_VIRTUALIZER_PORT_ABSTRACT)
        # Migrate port metadata
        for property, value in port.properties.iteritems():
          if property not in ('name', 'capability', 'sap', 'type'):
            meta_key = str(property)
            meta_value = str(value) if value is not None else None
            v_port.metadata.add(
              virt_lib.MetadataMetadata(key=meta_key, value=meta_value))
        # port_type: port-abstract & sap: -    -->  regular port
        # port_type: port-abstract & sap: <SAP...>    -->  was connected to
        # an inter-domain port - set this data in Virtualizer
        v_node.ports.add(v_port)
        self.log.debug("Added static %s" % port)

      # Add minimalistic Nodes for supported NFs based on supported list of NFFG
      for sup in infra.supported:
        v_node.capabilities.supported_NFs.add(
          virt_lib.Node(id=str(sup), type=str(sup)))

      # Add infra to virtualizer
      virtualizer.nodes.add(v_node)

      # Define full-mesh intra-links for nodes to set bandwidth and delay
      # values
      from itertools import combinations
      # Detect the number of ports
      port_num = len(v_node.ports.port._data)
      if port_num > 1:
        # There are valid port-pairs
        for i, port_pair in enumerate(combinations(
           (p.id.get_value() for p in v_node.ports), 2)):
          if infra.resources.delay is not None:
            v_link_delay = str(infra.resources.delay)
          else:
            v_link_delay = None
          if infra.resources.bandwidth is not None:
            v_link_bw = str(infra.resources.bandwidth)
          else:
            v_link_bw = None
          # Create link
          v_link = virt_lib.Link(id="resource-link%s" % i,
                                 src=v_node.ports[port_pair[0]],
                                 dst=v_node.ports[port_pair[1]],
                                 resources=virt_lib.Link_resource(
                                   delay=v_link_delay,
                                   bandwidth=v_link_bw))
          # Call bind to resolve src,dst references to workaround a bug
          v_link.bind()
          v_node.links.add(v_link)
      elif port_num == 1:
        # Only one port in infra - create loop-edge
        v_link_src = v_link_dst = iter(v_node.ports).next()
        if infra.resources.delay:
          v_link_delay = infra.resources.delay
        else:
          v_link_delay = None
        if infra.resources.bandwidth:
          v_link_bw = infra.resources.bandwidth
        else:
          v_link_bw = None
        v_link = virt_lib.Link(id="resource-link",
                               src=v_link_src,
                               dst=v_link_dst,
                               resources=virt_lib.Link_resource(
                                 delay=str(v_link_delay),
                                 bandwidth=str(v_link_bw)))
        # Call bind to resolve src,dst references to workaround a bug
        v_link.bind()
        v_node.links.add(v_link)
      else:
        # No port in Infra - unusual but acceptable
        self.log.warning(
          "No port has been detected in %s. Can not store internal "
          "bandwidth/delay value!" % infra)

  def _convert_nffg_saps (self, nffg, virtualizer):
    """
    Convert infras in the given :any:`NFFG` into the given Virtualizer.

    :param nffg: NFFG object
    :type nffg: :any:`NFFG`
    :param virtualizer: Virtualizer object
    :type virtualizer: Virtualizer
    :return: None
    """
    self.log.info("Converting SAPs...")
    # Rewrite SAP - Node ports to add SAP to Virtualizer
    for sap in nffg.saps:
      for s, n, link in nffg.network.edges_iter([sap.id], data=True):
        if link.type != NFFG.TYPE_LINK_STATIC:
          continue
        # Rewrite port-type to port-sap
        infra_id = str(n).split('@')[0] if self.ensure_unique_id else str(n)
        v_sap_port = virtualizer.nodes[infra_id].ports[str(link.dst.id)]
        v_sap_port.port_type.set_value(self.TYPE_VIRTUALIZER_PORT_SAP)
        # Add SAP.name as name to port or use sap.id
        if link.src.has_property("name"):
          v_sap_name = link.src.get_property("name")
        else:
          # Store SAP.id in the name attribute instead of SAP.name
          # SAP.id <--> virtualizer.node.port.name
          v_sap_name = str(sap.id)
        v_sap_port.name.set_value(v_sap_name)
        self.log.debug(
          "Convert SAP to port: %s in infra: %s" % (link.dst.id, n))
        # Check if the SAP is an bound, inter-domain SAP
        if nffg[s].domain is not None:
          v_sap_port.sap.set_value(s)
          self.log.debug(
            "Convert inter-domain SAP to port: %s in infra: %s" % (
              link.dst.id, n))

  def _convert_nffg_edges (self, nffg, virtualizer):
    """
    Convert edge links in the given :any:`NFFG` into the given Virtualizer.

    :param nffg: NFFG object
    :type nffg: :any:`NFFG`
    :param virtualizer: Virtualizer object
    :type virtualizer: Virtualizer
    :return: None
    """
    self.log.info("Converting edges...")
    # Add edge-link to Virtualizer
    for link in nffg.links:
      # Skip backward and non-static link conversion <-- Virtualizer links
      # are bidirectional
      if link.type != NFFG.TYPE_LINK_STATIC:
        continue
      # SAP - Infra links are not stored in Virtualizer format
      if link.src.node.type == NFFG.TYPE_SAP or \
            link.dst.node.type == NFFG.TYPE_SAP:
        continue
      self.log.debug(
        "Added link: Node: %s, port: %s <--> Node: %s, port: %s" % (
          link.src.node.id, link.src.id, link.dst.node.id, link.dst.id))
      if self.ensure_unique_id:
        src_node_id = str(link.src.node.id).split('@')[0]
        dst_node_id = str(link.dst.node.id).split('@')[0]
      else:
        src_node_id = str(link.src.node.id)
        dst_node_id = str(link.dst.node.id)
      v_link_delay = str(link.delay) if link.delay is not None else None
      v_link_bw = str(link.bandwidth) if link.bandwidth is not None else None
      v_link = virt_lib.Link(
        id=str(link.id),
        src=virtualizer.nodes[src_node_id].ports[str(link.src.id)],
        dst=virtualizer.nodes[dst_node_id].ports[str(link.dst.id)],
        resources=virt_lib.Link_resource(delay=v_link_delay,
                                         bandwidth=v_link_bw))
      # Call bind to resolve src,dst references to workaround a bug
      v_link.bind()
      virtualizer.links.add(v_link)

  def _convert_nffg_reqs (self, nffg, virtualizer):
    """
    Convert requirement links in the given :any:`NFFG` into given Virtualizer
    using topmost metadata list.

    :param nffg: NFFG object
    :type nffg: :any:`NFFG`
    :param virtualizer: Virtualizer object
    :type virtualizer: Virtualizer
    :return: None
    """
    self.log.info("Converting requirements...")
    for req in nffg.reqs:
      meta_key = "%s:%s" % (self.REQUIREMENT_PREFIX, req.id)
      # meta_value = "src:%s:%s|dst:%s:%s|delay:%s|bw:%s|path:%s" % (
      #   req.src.node.id,  # src node
      #   req.src.id,  # src port
      #   req.dst.node.id,  # dst node
      #   req.dst.id,  # dst port
      #   req.delay,  # delay
      #   req.bandwidth,  # bandwidth
      #   json.dumps(req.sg_path))  # sg hop list
      meta_value = json.dumps({
        "snode": req.src.node.id,
        "sport": req.src.id,
        "dnode": req.dst.node.id,
        "dport": req.dst.id,
        "delay": "%.3f" % req.delay,
        "bw": "%.3f" % req.bandwidth,
        "sg_path": req.sg_path}
        # Replace " with ' to avoid ugly HTTP escaping
      ).replace('"', "'").replace(' ', '')
      virtualizer.metadata.add(item=virt_lib.MetadataMetadata(key=meta_key,
                                                              value=meta_value))
      self.log.debug('Converted requirement link: %s' % req)

  def _convert_nffg_nfs (self, virtualizer, nffg):
    """
    Convert NFs in the given :any:`NFFG` into the given Virtualizer.

    :param virtualizer: Virtualizer object based on ETH's XML/Yang version.
    :param nffg: splitted NFFG (not necessarily in valid syntax)
    :return: modified Virtualizer object
    """
    self.log.info("Converting NFs...")
    # Check every infra Node
    for infra in nffg.infras:
      # Cache discovered NF to avoid multiple detection of NF which has more
      # than one port
      discovered_nfs = []
      # Recreate the original Node id
      if self.ensure_unique_id:
        v_node_id = str(infra.id).split('@')[0]
      else:
        v_node_id = str(infra.id)
      # Check in Infra exists in the Virtualizer
      if v_node_id not in virtualizer.nodes.node.keys():
        self.log.warning(
          "InfraNode: %s is not in the Virtualizer(nodes: %s)! Skip related "
          "initiations..." % (infra, virtualizer.nodes.node.keys()))
        continue
      # Get Infra node from Virtualizer
      v_node = virtualizer.nodes[v_node_id]
      # Check every outgoing edge
      for u, v, link in nffg.network.out_edges_iter([infra.id], data=True):
        # Observe only the NF neighbours
        if link.dst.node.type != NFFG.TYPE_NF:
          continue
        nf = link.dst.node
        # Skip already detected NFs
        if nf.id in discovered_nfs:
          continue
        # Check if the NF is exist in the InfraNode
        if str(v) not in v_node.NF_instances.node.keys():
          self.log.debug("Found uninitiated NF: %s in mapped NFFG" % nf)
          # Convert Resources to str for XML conversion
          v_nf_cpu = str(
            nf.resources.cpu) if nf.resources.cpu is not None else None
          v_nf_mem = str(
            nf.resources.mem) if nf.resources.mem is not None else None
          v_nf_storage = str(
            nf.resources.storage) if nf.resources.storage is not None else None
          # Create Node object for NF
          v_nf = virt_lib.Node(id=str(nf.id),
                               name=str(nf.name) if nf.name else None,
                               type=str(nf.functional_type),
                               resources=virt_lib.Software_resource(
                                 cpu=v_nf_cpu,
                                 mem=v_nf_mem,
                                 storage=v_nf_storage))
          # Set deployment type, delay, bandwidth as a metadata
          if nf.deployment_type is not None:
            v_nf.metadata.add(
              virt_lib.MetadataMetadata(key='deployment_type',
                                        value=str(nf.deployment_type)))
          if nf.resources.delay is not None:
            v_nf.metadata.add(
              virt_lib.MetadataMetadata(key='delay',
                                        value=str(nf.resources.delay)))
          if nf.resources.bandwidth is not None:
            v_nf.metadata.add(
              virt_lib.MetadataMetadata(key='bandwidth',
                                        value=str(nf.resources.bandwidth)))
          # Migrate metadata
          for key, value in nf.metadata.iteritems():
            if key not in ('deployment_type', 'delay', 'bandwidth'):
              meta_key = str(key)
              meta_value = str(value) if value is not None else None
              v_nf.metadata.add(
                virt_lib.MetadataMetadata(key=meta_key, value=meta_value))
          # Add NF to Infra object
          v_node.NF_instances.add(v_nf)
          # Cache discovered NF
          discovered_nfs.append(nf.id)

          self.log.debug(
            "Added NF: %s to Infra node(id=%s, name=%s, type=%s)" % (
              nf, v_node.id.get_as_text(),
              v_node.name.get_as_text(),
              v_node.type.get_as_text()))

          # Add NF ports
          for port in nffg[v].ports:
            v_nf_port = virt_lib.Port(id=str(port.id),
                                      port_type="port-abstract")
            v_node.NF_instances[str(v)].ports.add(v_nf_port)
            # Migrate metadata
            for property, value in port.properties.iteritems():
              meta_key = str(property)
              meta_value = str(value) if value is not None else None
              v_nf_port.metadata.add(
                virt_lib.MetadataMetadata(key=meta_key, value=meta_value))

            self.log.debug(
              "Added Port: %s to NF node: %s" % (port, v_nf.id.get_as_text()))
        else:
          self.log.debug("%s is already exist in the Virtualizer(id=%s, "
                         "name=%s)" % (nf, virtualizer.id.get_as_text(),
                                       virtualizer.name.get_as_text()))

  def _convert_nffg_flowrules (self, virtualizer, nffg):
    """
    Convert flowrules in the given :any:`NFFG` into the given Virtualizer.

    :param virtualizer: Virtualizer object based on ETH's XML/Yang version.
    :param nffg: splitted NFFG (not necessarily in valid syntax)
    :return: modified Virtualizer object
    """
    self.log.info("Converting flowrules...")
    # Check every infra Node
    for infra in nffg.infras:
      # Recreate the original Node id
      if self.ensure_unique_id:
        v_node_id = str(infra.id).split('@')[0]
      else:
        v_node_id = str(infra.id)
      # Check in Infra exists in the Virtualizer
      if v_node_id not in virtualizer.nodes.node.keys():
        self.log.warning(
          "InfraNode: %s is not in the Virtualizer(nodes: %s)! Skip related "
          "initiations..." % (infra, virtualizer.nodes.node.keys()))
        continue
      # Get Infra node from Virtualizer
      v_node = virtualizer.nodes[v_node_id]
      # Add flowrules to Virtualizer
      fe_cntr = 0
      # traverse every port in the Infra node
      for port in infra.ports:
        # Check every flowrule
        for fr in port.flowrules:
          self.log.debug("Converting flowrule: %s..." % fr)
          # Define metadata
          fe_id = "ESCAPE-flowentry" + str(fe_cntr)
          fe_cntr += 1
          fe_pri = str(100)

          # Check if match starts with in_port
          fe = fr.match.split(';')
          if fe[0].split('=')[0] != "in_port":
            self.log.warning("Missing 'in_port' from match in %s. Skip "
                             "flowrule conversion..." % fr)
            continue
          # Check if the src port is a physical or virtual port
          in_port = fe[0].split('=')[1]
          if str(port.id) in v_node.ports.port.keys():
            # Flowrule in_port is a phy port in Infra Node
            in_port = v_node.ports[str(port.id)]
            self.log.debug("Identify in_port: %s in match as a physical port "
                           "in the Virtualizer" % in_port.id.get_as_text())
          else:
            self.log.debug("Identify in_port: %s in match as a dynamic port. "
                           "Tracking associated NF port in the "
                           "Virtualizer..." % in_port)
            # in_port is a dynamic port --> search for connected NF's port
            v_nf_port = [l.dst for u, v, l in
                         nffg.network.out_edges_iter([infra.id], data=True)
                         if l.type == NFFG.TYPE_LINK_DYNAMIC and
                         str(l.src.id) == in_port]
            # There should be only one link between infra and NF
            if len(v_nf_port) < 1:
              self.log.warning("NF port is not found for dynamic Infra port: "
                               "%s defined in match field! Skip flowrule "
                               "conversion..." % in_port)
              continue
            v_nf_port = v_nf_port[0]
            in_port = v_node.NF_instances[str(v_nf_port.node.id)].ports[
              str(v_nf_port.id)]
            self.log.debug("Found associated NF port: node=%s, port=%s" % (
              in_port.get_parent().get_parent().id.get_as_text(),
              in_port.id.get_as_text()))
          # Process match field
          match = self._convert_flowrule_match(fr.match)
          # Check if action starts with outport
          fe = fr.action.split(';')
          if fe[0].split('=')[0] != "output":
            self.log.warning("Missing 'output' from action in %s."
                             "Skip flowrule conversion..." % fr)
            continue
          # Check if the dst port is a physical or virtual port
          out_port = fe[0].split('=')[1]
          if str(out_port) in v_node.ports.port.keys():
            # Flowrule output is a phy port in Infra Node
            out_port = v_node.ports[str(out_port)]
            self.log.debug("Identify outport: %s in action as a physical port "
                           "in the Virtualizer" % out_port.id.get_as_text())
          else:
            self.log.debug("Identify outport: %s in action as a dynamic port. "
                           "Track associated NF port in the Virtualizer..." %
                           out_port)
            # out_port is a dynamic port --> search for connected NF's port
            v_nf_port = [l.dst for u, v, l in
                         nffg.network.out_edges_iter([infra.id], data=True)
                         if l.type == NFFG.TYPE_LINK_DYNAMIC and
                         str(l.src.id) == out_port]
            if len(v_nf_port) < 1:
              self.log.warning("NF port is not found for dynamic Infra port: "
                               "%s defined in action field! Skip flowrule "
                               "conversion..." % out_port)
              continue
            v_nf_port = v_nf_port[0]
            out_port = v_node.NF_instances[str(v_nf_port.node.id)].ports[
              str(v_nf_port.id)]
            self.log.debug("Found associated NF port: node=%s, port=%s" % (
              # out_port.parent.parent.parent.id.get_as_text(),
              out_port.get_parent().get_parent().id.get_as_text(),
              out_port.id.get_as_text()))
          # Process action field
          action = self._convert_flowrule_action(fr.action)
          # Process resource fields
          v_fe_delay = str(fr.delay) if fr.delay is not None else None
          v_fe_bw = str(fr.bandwidth) if fr.bandwidth is not None else None
          _resources = virt_lib.Link_resource(delay=v_fe_delay,
                                              bandwidth=v_fe_bw)
          # Process hop_id field
          if fr.hop_id is not None:
            v_fe_name = "%s:%s" % (self.TAG_SG_HOP, fr.hop_id)
          else:
            v_fe_name = None
          # Add Flowentry with converted params
          virt_fe = Flowentry(id=fe_id, priority=fe_pri, port=in_port,
                              match=match, action=action, out=out_port,
                              resources=_resources, name=v_fe_name)
          self.log.debug(
            "Generated Flowentry:\n%s" % v_node.flowtable.add(virt_fe))

  def dump_to_Virtualizer (self, nffg):
    """
    Convert given :any:`NFFG` to Virtualizer format.

    :param nffg: topology description
    :type nffg: :any:`NFFG`
    :return: topology in Virtualizer format
    :rtype: Virtualizer
    """
    self.log.debug(
      "START conversion: NFFG(ver: %s) --> Virtualizer(ver: %s)" % (
        NFFG.version, V_VERSION))

    self.log.debug("Converting data to XML-based Virtualizer structure...")
    # Create Virtualizer with default id,name
    v_id = str(nffg.id)
    v_name = str(nffg.name) if nffg.name else None
    virtualizer = virt_lib.Virtualizer(id=v_id, name=v_name)
    self.log.debug("Creating Virtualizer based on %s" % nffg)
    # Convert NFFG metadata
    for key, value in nffg.metadata.iteritems():
      meta_key = str(key)
      meta_value = str(value) if value is not None else None
      virtualizer.metadata.add(item=virt_lib.MetadataMetadata(key=meta_key,
                                                              value=meta_value))
    # Convert Infras
    self._convert_nffg_infras(nffg=nffg, virtualizer=virtualizer)
    # Convert SAPs
    self._convert_nffg_saps(nffg=nffg, virtualizer=virtualizer)
    # Convert edge links
    self._convert_nffg_edges(nffg=nffg, virtualizer=virtualizer)
    # Convert NFs
    self._convert_nffg_nfs(nffg=nffg, virtualizer=virtualizer)
    # Convert Flowrules
    self._convert_nffg_flowrules(nffg=nffg, virtualizer=virtualizer)
    # Convert requirement links as metadata
    self._convert_nffg_reqs(nffg=nffg, virtualizer=virtualizer)
    # explicitly call bind to resolve relative paths for safety reason
    virtualizer.bind(relative=True)
    self.log.debug(
      "END conversion: NFFG(ver: %s) --> Virtualizer(ver: %s)" % (
        NFFG.version, 3))
    # Return with created Virtualizer
    return virtualizer

  def adapt_mapping_into_Virtualizer (self, virtualizer, nffg):
    """
    Install the mapping related modification into a Virtualizer.

    :param virtualizer: Virtualizer object based on ETH's XML/Yang version.
    :param nffg: splitted NFFG (not necessarily in valid syntax)
    :return: modified Virtualizer object
    """
    self.log.debug(
      "START adapting modifications from %s into Virtualizer(id=%s, name=%s)"
      % (nffg, virtualizer.id.get_as_text(), virtualizer.name.get_as_text()))
    self._convert_nffg_nfs(virtualizer=virtualizer, nffg=nffg)
    self._convert_nffg_flowrules(virtualizer=virtualizer, nffg=nffg)
    self._convert_nffg_reqs(virtualizer=virtualizer, nffg=nffg)
    # explicitly call bind to resolve absolute paths for safety reason
    virtualizer.bind(relative=True)
    self.log.debug(
      "END adapting modifications from %s into Virtualizer(id=%s, name=%s)" % (
        nffg, virtualizer.id.get_as_text(), virtualizer.name.get_as_text()))
    # Return with modified Virtualizer
    return virtualizer

  @staticmethod
  def unescape_output_hack (data):
    return data.replace("&lt;", "<").replace("&gt;", ">")


if __name__ == "__main__":
  import logging

  logging.basicConfig(level=logging.DEBUG)
  log = logging.getLogger(__name__)
  c = NFFGConverter(domain="OPENSTACK",
                    # ensure_unique_id=True,
                    logger=log)

  with open(
     "../../../../examples/escape-mn-mapped-test.nffg") as f:
    nffg = NFFG.parse(raw_data=f.read())
    # nffg.duplicate_static_links()
  log.debug("Parsed NFFG:\n%s" % nffg.dump())
  virt = c.dump_to_Virtualizer(nffg=nffg)
  log.debug("Converted:")
  log.debug(virt.xml())
  log.debug("Reconvert to NFFG:")
  nffg = c.parse_from_Virtualizer(xml_data=virt.xml())
  log.debug(nffg.dump())

  # with open(
  #    # "../../../../examples/OS_report1.xml") as f:
  #    "../../../../examples/escape-mn-dov-test.xml") as f:
  #   tree = tree = ET.ElementTree(ET.fromstring(f.read()))
  #   dov = virt_lib.Virtualizer.parse(root=tree.getroot())
  #   dov.bind(relative=True)
  # log.info("Parsed XML:")
  # log.info("%s" % dov)
  # nffg = c.parse_from_Virtualizer(xml_data=dov.xml())
  # log.info("Reconverted Virtualizer:")
  # log.info("%s" % nffg.dump())
  # virt = c.dump_to_Virtualizer(nffg=nffg)
  # # virt.bind()
  # log.info("Reconverted Virtualizer:")
  # log.info("%s" % virt.xml())
