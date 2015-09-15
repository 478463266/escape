#    Filename: virtualizer3.py		 Created: 2015-07-27  15:13:25
#    This file was automatically created by a pyang plugin (PNC) developed at Ericsson Hungary Ltd., 2015
#    Authors: Robert Szabo, Balazs Miriszlai, Akos Recse
#    Credits: Robert Szabo, David Jocha, Janos Elek, Balazs Miriszlai, Akos Recse
#    Contact: Robert Szabo <robert.szabo@ericsson.com>
        
#    Yang file info:
#    Namespace: urn:unify:virtualizer
#    Prefix: virtualizer
#    Organization: ETH
#    Contact: Robert Szabo <robert.szabo@ericsson.com>
#    Revision: 2015-07-20
#    Description: Virtualizer's revised (simplified) data model

__copyright__ = "Copyright Ericsson Hungary Ltd., 2015"

import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import copy


class Yang(object):
    def __init__(self, parent=None, tag=None):
        self.parent = parent
        self.tag = tag
        self.operation = None

    def getParent(self):
        return self.parent

    def _et(self):
        pass

    def xml(self):
        root = self._et()
        xmlstr = ET.tostring(root, encoding="utf8", method="xml")
        dom = parseString(xmlstr)
        return dom.toprettyxml()

    def _parse(self, parent, root):
        pass

    def isInitialized(self):
        pass

    def getPath(self):
        if self.getParent() is not None:
            return self.getParent().getPath() + "/" + self.tag
        else:
            return self.tag

    def walkPath(self, path):
        if path == "":
            return self
        p = path.split("/")
        l = p.pop(0)
        if l == "..":
            return self.getParent().walkPath("/".join(p))
        else:
            if (l.find("[") > 0) and (l.find("]")>0):
                attrib = l[0: l.find("[")]
                keystring = l[l.find("[") + 1: l.rfind("]")]
                key = list()
                keyvalues = keystring.split(",")
                for kv in keyvalues:
                    v = kv.split("=")
                    key.append(v[1])
                if len(key) == 1:
                    return getattr(self, attrib)[key[0]].walkPath("/".join(p))
                else:
                    return getattr(self, attrib)[key].walkPath("/".join(p))
            else:
                return getattr(self, l).walkPath("/".join(p))

    def getRelPath(self, target):
        src = self.getPath()
        dst = target.getPath()
        s = src.split("/")
        d = dst.split("/")
        if s[0] != d[0]:
            return dst
        equal_ind = 0
        ret = list()
        
        if len(s) > len(d):
            lit = d
        else:
            lit = s

        for k in range(len(lit)):
            if s[k] == d[k]:
                equal_ind+=1
            else:
                break
        
        for j in range(equal_ind, len(s)):
            ret.insert(0,"..")
        for j in range(equal_ind, len(d)):
            ret.append(d[j])
        
        return '/'.join(ret)


    @classmethod
    def parse(cls, parent=None, root=None):
        temp = cls(parent=parent)
        temp._parse(parent, root)
        return temp

    def __str__(self):
        return self.xml()

    def setOperation(self, operation):
        raise NotImplementedError(self.__class__.__name__ + 'setOperation')


class Leaf(Yang):

    def __init__(self, parent=None, tag=None):
        super(Leaf, self).__init__(parent)
        self.tag = tag
        """:type: string"""
        self.data = None
        """:type: ???"""
        self.mandatory = False
        """:type: boolean"""

    def getAsText(self):
        pass

    def setAsText(self, value):
        pass

    def getValue(self):
        pass

    def setValue(self, value):
        pass

    def isInitialized(self):
        if self.data is not None:
            return True
        else:
            return False

    def _et(self, parent):
        if self.isInitialized():
            e_data = ET.SubElement(parent, self.tag)
            e_data.text = self.getAsText()
        return parent

    def clearData(self):
        if not self.containsDelete():
            self.data = None

    def reducer(self, other):
        pass

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        return False


class StringLeaf(Leaf):
    def __init__(self, parent=None, tag=None, value=None):
        super(StringLeaf, self).__init__(parent=parent, tag=tag)
        self.data = value
        """:type: string"""

    def parse(self, root):
        e_data = root.find(self.tag)
        if e_data is not None:
            if len(e_data._children)>0:
                for i in e_data.iter():
                    i.tail = None
                e_data.text = None
                self.data = e_data
            else:
                self.data = e_data.text
            root.remove(e_data)
            self.initialized = True

    def _et(self, parent):
        if self.isInitialized():
            if type(self.data) is ET.Element:
                parent.append(self.data)
            else:
                e_data = ET.SubElement(parent, self.tag)
                e_data.text = self.getAsText()
        return parent

    def getAsText(self):
        if type(self.data) == ET:
            return ET.tostring(self.data, encoding="us-ascii", method="text")
        return self.data

    def setAsText(self, value):
        self.data = value
        self.initialized = True

    def getValue(self):
        return self.data

    def setValue(self, value):
        self.data = value
        self.initialized = True


    def __eq__(self,other):
        return self.data == other.data


    def setOperation(self, operation):
        self.operation = operation


class Leafref(StringLeaf):
    def __init__(self, parent=None, tag=None, value=None):
        super(Leafref, self).__init__(parent=parent, tag=tag)
        self.target = None
        """:type: Yang"""
        if value is None:
            return
        # cannot bind as parent is not registered yet
        if type(value) is str:
            self.data = value
        elif issubclass(type(value), Yang):
            self.target = value
        else:
            raise ValueError("Leafref value is of unknown type.")

    def setValue(self, value):
        if value is None:
            self.data = None
            self.target = None
            return
        if type(value) is str:
            self.data = value
        elif issubclass(type(value), Yang):
            self.target = value
            self.data = self.getRelPath(value)
        else:
            raise ValueError("Leafref value is of unknown type.")

    def isInitialized(self):
        if (self.data is not None) or (self.target is not None):
            return True
        else:
            return False

    def getAsText(self):
        if self.data is not None:
            return self.data
        if self.target is not None:
            return self.getRelPath(self.target)
        else:
            raise ReferenceError("Leafref getAsText() is called but neither data nor target exists.")

    def getTarget(self):
        if self.data is not None:
            return self.walkPath(self.data)

class ListedYang(Yang):
    def __init__(self, parent=None, tag=None):
        super(ListedYang, self).__init__(parent, tag)

    def getParent(self):
        return self.parent.getParent()

    def getKeyValue(self):
        raise NotImplementedError("getKey() abstract method call")

    def getPath(self):
        keysvalue = self.getKeyValue()
        keys = self.getKeys()
        s = ''
        if type (keysvalue) is tuple:
            s = ', '.join('%s=%s' % t for t in zip(keys, keysvalue))
        else:
            s = keys + "=" + keysvalue
        if self.getParent() is not None:
            return self.getParent().getPath() + "/" + self.tag + "[" + s + "]"
        else:
            return self.tag + "[" + s + "]"

class ListYang(Yang):
    def __init__(self, parent=None, tag=None):
        super(ListYang, self).__init__(parent, tag)
        self._data = dict()

    def isInitialized(self):
        if len(self._data) > 0:
            return True
        return False

    def getKeys(self):
        return self._data.keys()

    def add(self, item):
        if type(item) is tuple or type(item) is list:
            for i in item:
                self.add(i)
        else:
            item.parent = self
            self._data[item.getKeyValue()] = item

    def delete(self, item):
        if type(item) is str or type(item) is int:
            if item in self._data.keys():
                del self._data[item]
        elif type(item) is tuple or type(item) is list:
            for i in item:
                self.delete(i)
        else:
            del self._data[item.getKeyValue()]

    def _et(self, node):
        for key in sorted(self._data):
            self._data[key]._et(node)
        return node

    def __iter__(self):
        return self._data.__iter__()

    def next(self):
        self._data.next()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        value.parent = self

    def clearData(self):
        self._data = dict()

    def reducer(self, other):
        for item in other._data.keys():
            if not (self._data[item]== other._data[item]) or other._data[item].containsDelete() :
                self._data[item].reducer(other._data[item])
            else:
                other._data.pop(item)

    def __eq__(self, other):
        if self._data == other._data:
            return True
        return False

    def containsDelete(self):
        for key in self._data.keys():
            if self._data[key].containsDelete():
                return True
        return False

    def setOperation(self, operation):
        for key in self._data.keys():
            self._data[key].setOperation(operation)
        
#YANG construct: grouping id-name
class GroupingId_name(Yang):
    def __init__(self, parent=None, id=None, name=None):
        super(GroupingId_name, self).__init__(parent)
        #my keyword is: leaf
        self.id = StringLeaf(parent=self, tag="id")
        """:type: StringLeaf"""
        if id is not None:
            self.id.setValue(id)
        #my keyword is: leaf
        self.name = StringLeaf(parent=self, tag="name")
        """:type: StringLeaf"""
        if name is not None:
            self.name.setValue(name)

    def _parse(self, parent=None, root=None):
        self.id.parse(root)
        self.name.parse(root)

    def _et(self, node, inherited=False):
        self.id._et(node)
        self.name._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.id.isInitialized()
        inited = inited or self.name.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.id == other.id,\
            one.name == other.name,\
            ])
        return equal

    def clearData(self):
        
        self.id.clearData()
        self.name.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.id ==  other.id) or other.id.containsDelete():
            self.id.reducer(other.id)
            isEmpty = False
        elif not other.id.containsDelete():
            other.id.clearData()
        if not (self.name ==  other.name) or other.name.containsDelete():
            self.name.reducer(other.name)
            isEmpty = False
        elif not other.name.containsDelete():
            other.name.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.id == other.id,\
            self.name == other.name,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.id.setOperation(operation)
            self.name.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.id.containsDelete():
            return True
        if self.name.containsDelete():
            return True
        return False


#YANG construct: grouping id-name-type
class GroupingId_name_type(GroupingId_name):
    def __init__(self, parent=None, id=None, name=None, type=None):
        GroupingId_name.__init__(self, parent, id, name)
        #my keyword is: leaf
        self.type = StringLeaf(parent=self, tag="type")
        """:type: StringLeaf"""
        if type is not None:
            self.type.setValue(type)

    def _parse(self, parent=None, root=None):
        GroupingId_name._parse(self, parent, root)
        self.type.parse(root)

    def _et(self, node, inherited=False):
        GroupingId_name._et(self, node, True)
        self.type._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.type.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.type == other.type,\
            GroupingId_name.compare(one,other),\
            ])
        return equal

    def clearData(self):
        
        self.type.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.type ==  other.type) or other.type.containsDelete():
            self.type.reducer(other.type)
            isEmpty = False
        elif not other.type.containsDelete():
            other.type.clearData()
        GroupingId_name.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.type == other.type,\
            GroupingId_name.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            self.type.setOperation(operation)
            GroupingId_name.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.type.containsDelete():
            return True
        if GroupingId_name.containsDelete(self):
            return True
        return False


#YANG construct: grouping port
class GroupingPort(GroupingId_name):
    def __init__(self, parent=None, id=None, name=None, port_type=None, capability=None, sap=None):
        GroupingId_name.__init__(self, parent, id, name)
        #my keyword is: leaf
        self.port_type = StringLeaf(parent=self, tag="port_type")
        """:type: StringLeaf"""
        if port_type is not None:
            self.port_type.setValue(port_type)
        #my keyword is: leaf
        self.capability = StringLeaf(parent=self, tag="capability")
        """:type: StringLeaf"""
        if capability is not None:
            self.capability.setValue(capability)
        #my keyword is: leaf
        self.sap = StringLeaf(parent=self, tag="sap")
        """:type: StringLeaf"""
        if sap is not None:
            self.sap.setValue(sap)

    def _parse(self, parent=None, root=None):
        GroupingId_name._parse(self, parent, root)
        self.port_type.parse(root)
        self.capability.parse(root)
        self.sap.parse(root)

    def _et(self, node, inherited=False):
        GroupingId_name._et(self, node, True)
        self.port_type._et(node)
        self.capability._et(node)
        self.sap._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.port_type.isInitialized()
        inited = inited or self.capability.isInitialized()
        inited = inited or self.sap.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.port_type == other.port_type,\
            one.capability == other.capability,\
            one.sap == other.sap,\
            GroupingId_name.compare(one,other),\
            ])
        return equal

    def clearData(self):
        
        self.port_type.clearData()
        self.capability.clearData()
        self.sap.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.port_type ==  other.port_type) or other.port_type.containsDelete():
            self.port_type.reducer(other.port_type)
            isEmpty = False
        elif not other.port_type.containsDelete():
            other.port_type.clearData()
        if not (self.capability ==  other.capability) or other.capability.containsDelete():
            self.capability.reducer(other.capability)
            isEmpty = False
        elif not other.capability.containsDelete():
            other.capability.clearData()
        if not (self.sap ==  other.sap) or other.sap.containsDelete():
            self.sap.reducer(other.sap)
            isEmpty = False
        elif not other.sap.containsDelete():
            other.sap.clearData()
        GroupingId_name.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.port_type == other.port_type,\
            self.capability == other.capability,\
            self.sap == other.sap,\
            GroupingId_name.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            self.port_type.setOperation(operation)
            self.capability.setOperation(operation)
            self.sap.setOperation(operation)
            GroupingId_name.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.port_type.containsDelete():
            return True
        if self.capability.containsDelete():
            return True
        if self.sap.containsDelete():
            return True
        if GroupingId_name.containsDelete(self):
            return True
        return False


#YANG construct: grouping link-resource
class GroupingLink_resource(Yang):
    def __init__(self, parent=None, delay=None, bandwidth=None):
        super(GroupingLink_resource, self).__init__(parent)
        #my keyword is: leaf
        self.delay = StringLeaf(parent=self, tag="delay")
        """:type: StringLeaf"""
        if delay is not None:
            self.delay.setValue(delay)
        #my keyword is: leaf
        self.bandwidth = StringLeaf(parent=self, tag="bandwidth")
        """:type: StringLeaf"""
        if bandwidth is not None:
            self.bandwidth.setValue(bandwidth)

    def _parse(self, parent=None, root=None):
        self.delay.parse(root)
        self.bandwidth.parse(root)

    def _et(self, node, inherited=False):
        self.delay._et(node)
        self.bandwidth._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.delay.isInitialized()
        inited = inited or self.bandwidth.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.delay == other.delay,\
            one.bandwidth == other.bandwidth,\
            ])
        return equal

    def clearData(self):
        
        self.delay.clearData()
        self.bandwidth.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.delay ==  other.delay) or other.delay.containsDelete():
            self.delay.reducer(other.delay)
            isEmpty = False
        elif not other.delay.containsDelete():
            other.delay.clearData()
        if not (self.bandwidth ==  other.bandwidth) or other.bandwidth.containsDelete():
            self.bandwidth.reducer(other.bandwidth)
            isEmpty = False
        elif not other.bandwidth.containsDelete():
            other.bandwidth.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.delay == other.delay,\
            self.bandwidth == other.bandwidth,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.delay.setOperation(operation)
            self.bandwidth.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.delay.containsDelete():
            return True
        if self.bandwidth.containsDelete():
            return True
        return False


#YANG construct: grouping flowentry
class GroupingFlowentry(GroupingId_name):
    def __init__(self, parent=None, id=None, name=None, priority=None, port=None, match=None, action=None, out=None, resources=None):
        GroupingId_name.__init__(self, parent, id, name)
        #my keyword is: leaf
        self.priority = StringLeaf(parent=self, tag="priority")
        """:type: StringLeaf"""
        if priority is not None:
            self.priority.setValue(priority)
        #my keyword is: leaf
        self.port = Leafref(parent=self, tag="port", value=port)
        """:type: Leafref"""
        self.port.mandatory = True
        """:type: boolean"""
        #my keyword is: leaf
        self.match = StringLeaf(parent=self, tag="match")
        """:type: StringLeaf"""
        if match is not None:
            self.match.setValue(match)
        self.match.mandatory = True
        """:type: boolean"""
        #my keyword is: leaf
        self.action = StringLeaf(parent=self, tag="action")
        """:type: StringLeaf"""
        if action is not None:
            self.action.setValue(action)
        self.action.mandatory = True
        """:type: boolean"""
        #my keyword is: leaf
        self.out = Leafref(parent=self, tag="out", value=out)
        """:type: Leafref"""
        #my keyword is: container
        self.resources = None
        """:type: FlowentryResources"""
        if resources is not None:
            self.resources = resources
        else:
            self.resources = FlowentryResources(parent=self)

    def _parse(self, parent=None, root=None):
        GroupingId_name._parse(self, parent, root)
        self.priority.parse(root)
        self.port.parse(root)
        self.match.parse(root)
        self.action.parse(root)
        self.out.parse(root)
        e_resources = root.find("resources")
        if e_resources is not None:
            self.resources= FlowentryResources.parse(self, e_resources)
            for key in e_resources.attrib.keys():
                if key == "operation":
                    item.setOperation(e_resources.attrib[key])
                    item.operation = e_resources.attrib[key]

    def _et(self, node, inherited=False):
        GroupingId_name._et(self, node, True)
        self.priority._et(node)
        self.port._et(node)
        self.match._et(node)
        self.action._et(node)
        self.out._et(node)
        if self.resources.isInitialized():
            self.resources._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.priority.isInitialized()
        inited = inited or self.port.isInitialized()
        inited = inited or self.match.isInitialized()
        inited = inited or self.action.isInitialized()
        inited = inited or self.out.isInitialized()
        inited = inited or self.resources.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.priority == other.priority,\
            one.port == other.port,\
            one.match == other.match,\
            one.action == other.action,\
            one.out == other.out,\
            one.resources == other.resources,\
            GroupingId_name.compare(one,other),\
            ])
        return equal

    def clearData(self):
        
        self.priority.clearData()
        self.port.clearData()
        self.match.clearData()
        self.action.clearData()
        self.out.clearData()
        self.resources.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.priority ==  other.priority) or other.priority.containsDelete():
            self.priority.reducer(other.priority)
            isEmpty = False
        elif not other.priority.containsDelete():
            other.priority.clearData()
        if not (self.port ==  other.port) or other.port.containsDelete():
            self.port.reducer(other.port)
            isEmpty = False
        elif not other.port.containsDelete():
            other.port.clearData()
        if not (self.match ==  other.match) or other.match.containsDelete():
            self.match.reducer(other.match)
            isEmpty = False
        elif not other.match.containsDelete():
            other.match.clearData()
        if not (self.action ==  other.action) or other.action.containsDelete():
            self.action.reducer(other.action)
            isEmpty = False
        elif not other.action.containsDelete():
            other.action.clearData()
        if not (self.out ==  other.out) or other.out.containsDelete():
            self.out.reducer(other.out)
            isEmpty = False
        elif not other.out.containsDelete():
            other.out.clearData()
        if not (self.resources ==  other.resources) or other.resources.containsDelete():
            self.resources.reducer(other.resources)
            isEmpty = False
        elif not other.resources.containsDelete():
            other.resources.clearData()
        GroupingId_name.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.priority == other.priority,\
            self.port == other.port,\
            self.match == other.match,\
            self.action == other.action,\
            self.out == other.out,\
            self.resources == other.resources,\
            GroupingId_name.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            self.priority.setOperation(operation)
            self.port.setOperation(operation)
            self.match.setOperation(operation)
            self.action.setOperation(operation)
            self.out.setOperation(operation)
            self.resources.setOperation(operation)
            GroupingId_name.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.priority.containsDelete():
            return True
        if self.port.containsDelete():
            return True
        if self.match.containsDelete():
            return True
        if self.action.containsDelete():
            return True
        if self.out.containsDelete():
            return True
        if self.resources.containsDelete():
            return True
        if GroupingId_name.containsDelete(self):
            return True
        return False


#YANG construct: grouping flowtable
class GroupingFlowtable(Yang):
    def __init__(self, parent=None, flowtable=None):
        super(GroupingFlowtable, self).__init__(parent)
        #my keyword is: container
        self.flowtable = None
        """:type: FlowtableFlowtable"""
        if flowtable is not None:
            self.flowtable = flowtable
        else:
            self.flowtable = FlowtableFlowtable(parent=self)

    def _parse(self, parent=None, root=None):
        e_flowtable = root.find("flowtable")
        if e_flowtable is not None:
            self.flowtable= FlowtableFlowtable.parse(self, e_flowtable)
            for key in e_flowtable.attrib.keys():
                if key == "operation":
                    item.setOperation(e_flowtable.attrib[key])
                    item.operation = e_flowtable.attrib[key]

    def _et(self, node, inherited=False):
        if self.flowtable.isInitialized():
            self.flowtable._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.flowtable.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.flowtable == other.flowtable,\
            ])
        return equal

    def clearData(self):
        
        self.flowtable.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.flowtable ==  other.flowtable) or other.flowtable.containsDelete():
            self.flowtable.reducer(other.flowtable)
            isEmpty = False
        elif not other.flowtable.containsDelete():
            other.flowtable.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.flowtable == other.flowtable,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.flowtable.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.flowtable.containsDelete():
            return True
        return False


#YANG construct: grouping link
class GroupingLink(GroupingId_name):
    def __init__(self, parent=None, id=None, name=None, src=None, dst=None, resources=None):
        GroupingId_name.__init__(self, parent, id, name)
        #my keyword is: leaf
        self.src = Leafref(parent=self, tag="src", value=src)
        """:type: Leafref"""
        #my keyword is: leaf
        self.dst = Leafref(parent=self, tag="dst", value=dst)
        """:type: Leafref"""
        #my keyword is: container
        self.resources = None
        """:type: LinkResources"""
        if resources is not None:
            self.resources = resources
        else:
            self.resources = LinkResources(parent=self)

    def _parse(self, parent=None, root=None):
        GroupingId_name._parse(self, parent, root)
        self.src.parse(root)
        self.dst.parse(root)
        e_resources = root.find("resources")
        if e_resources is not None:
            self.resources= LinkResources.parse(self, e_resources)
            for key in e_resources.attrib.keys():
                if key == "operation":
                    item.setOperation(e_resources.attrib[key])
                    item.operation = e_resources.attrib[key]

    def _et(self, node, inherited=False):
        GroupingId_name._et(self, node, True)
        self.src._et(node)
        self.dst._et(node)
        if self.resources.isInitialized():
            self.resources._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.src.isInitialized()
        inited = inited or self.dst.isInitialized()
        inited = inited or self.resources.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.src == other.src,\
            one.dst == other.dst,\
            one.resources == other.resources,\
            GroupingId_name.compare(one,other),\
            ])
        return equal

    def clearData(self):
        
        self.src.clearData()
        self.dst.clearData()
        self.resources.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.src ==  other.src) or other.src.containsDelete():
            self.src.reducer(other.src)
            isEmpty = False
        elif not other.src.containsDelete():
            other.src.clearData()
        if not (self.dst ==  other.dst) or other.dst.containsDelete():
            self.dst.reducer(other.dst)
            isEmpty = False
        elif not other.dst.containsDelete():
            other.dst.clearData()
        if not (self.resources ==  other.resources) or other.resources.containsDelete():
            self.resources.reducer(other.resources)
            isEmpty = False
        elif not other.resources.containsDelete():
            other.resources.clearData()
        GroupingId_name.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.src == other.src,\
            self.dst == other.dst,\
            self.resources == other.resources,\
            GroupingId_name.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            self.src.setOperation(operation)
            self.dst.setOperation(operation)
            self.resources.setOperation(operation)
            GroupingId_name.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.src.containsDelete():
            return True
        if self.dst.containsDelete():
            return True
        if self.resources.containsDelete():
            return True
        if GroupingId_name.containsDelete(self):
            return True
        return False


#YANG construct: grouping links
class GroupingLinks(Yang):
    def __init__(self, parent=None, links=None):
        super(GroupingLinks, self).__init__(parent)
        #my keyword is: container
        self.links = None
        """:type: LinksLinks"""
        if links is not None:
            self.links = links
        else:
            self.links = LinksLinks(parent=self)

    def _parse(self, parent=None, root=None):
        e_links = root.find("links")
        if e_links is not None:
            self.links= LinksLinks.parse(self, e_links)
            for key in e_links.attrib.keys():
                if key == "operation":
                    item.setOperation(e_links.attrib[key])
                    item.operation = e_links.attrib[key]

    def _et(self, node, inherited=False):
        if self.links.isInitialized():
            self.links._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.links.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.links == other.links,\
            ])
        return equal

    def clearData(self):
        
        self.links.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.links ==  other.links) or other.links.containsDelete():
            self.links.reducer(other.links)
            isEmpty = False
        elif not other.links.containsDelete():
            other.links.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.links == other.links,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.links.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.links.containsDelete():
            return True
        return False


#YANG construct: grouping software-resource
class GroupingSoftware_resource(Yang):
    def __init__(self, parent=None, cpu=None, mem=None, storage=None):
        super(GroupingSoftware_resource, self).__init__(parent)
        #my keyword is: leaf
        self.cpu = StringLeaf(parent=self, tag="cpu")
        """:type: StringLeaf"""
        if cpu is not None:
            self.cpu.setValue(cpu)
        self.cpu.mandatory = True
        """:type: boolean"""
        #my keyword is: leaf
        self.mem = StringLeaf(parent=self, tag="mem")
        """:type: StringLeaf"""
        if mem is not None:
            self.mem.setValue(mem)
        self.mem.mandatory = True
        """:type: boolean"""
        #my keyword is: leaf
        self.storage = StringLeaf(parent=self, tag="storage")
        """:type: StringLeaf"""
        if storage is not None:
            self.storage.setValue(storage)
        self.storage.mandatory = True
        """:type: boolean"""

    def _parse(self, parent=None, root=None):
        self.cpu.parse(root)
        self.mem.parse(root)
        self.storage.parse(root)

    def _et(self, node, inherited=False):
        self.cpu._et(node)
        self.mem._et(node)
        self.storage._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.cpu.isInitialized()
        inited = inited or self.mem.isInitialized()
        inited = inited or self.storage.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.cpu == other.cpu,\
            one.mem == other.mem,\
            one.storage == other.storage,\
            ])
        return equal

    def clearData(self):
        
        self.cpu.clearData()
        self.mem.clearData()
        self.storage.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.cpu ==  other.cpu) or other.cpu.containsDelete():
            self.cpu.reducer(other.cpu)
            isEmpty = False
        elif not other.cpu.containsDelete():
            other.cpu.clearData()
        if not (self.mem ==  other.mem) or other.mem.containsDelete():
            self.mem.reducer(other.mem)
            isEmpty = False
        elif not other.mem.containsDelete():
            other.mem.clearData()
        if not (self.storage ==  other.storage) or other.storage.containsDelete():
            self.storage.reducer(other.storage)
            isEmpty = False
        elif not other.storage.containsDelete():
            other.storage.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.cpu == other.cpu,\
            self.mem == other.mem,\
            self.storage == other.storage,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.cpu.setOperation(operation)
            self.mem.setOperation(operation)
            self.storage.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.cpu.containsDelete():
            return True
        if self.mem.containsDelete():
            return True
        if self.storage.containsDelete():
            return True
        return False


#YANG construct: grouping node
class GroupingNode(GroupingId_name_type, GroupingLinks):
    """Any node: infrastructure or NFs"""
    def __init__(self, parent=None, id=None, name=None, type=None, ports=None, links=None, resources=None):
        GroupingId_name_type.__init__(self, parent, id, name, type)
        GroupingLinks.__init__(self, parent, links)
        #my keyword is: container
        self.ports = None
        """:type: NodePorts"""
        if ports is not None:
            self.ports = ports
        else:
            self.ports = NodePorts(parent=self)
        #my keyword is: container
        self.resources = None
        """:type: NodeResources"""
        if resources is not None:
            self.resources = resources
        else:
            self.resources = NodeResources(parent=self)

    def _parse(self, parent=None, root=None):
        GroupingId_name_type._parse(self, parent, root)
        GroupingLinks._parse(self, parent, root)
        e_ports = root.find("ports")
        if e_ports is not None:
            self.ports= NodePorts.parse(self, e_ports)
            for key in e_ports.attrib.keys():
                if key == "operation":
                    item.setOperation(e_ports.attrib[key])
                    item.operation = e_ports.attrib[key]
        e_resources = root.find("resources")
        if e_resources is not None:
            self.resources= NodeResources.parse(self, e_resources)
            for key in e_resources.attrib.keys():
                if key == "operation":
                    item.setOperation(e_resources.attrib[key])
                    item.operation = e_resources.attrib[key]

    def _et(self, node, inherited=False):
        GroupingId_name_type._et(self, node, True)
        if self.ports.isInitialized():
            self.ports._et(node)
        GroupingLinks._et(self, node, True)
        if self.resources.isInitialized():
            self.resources._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.ports.isInitialized()
        inited = inited or self.resources.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.ports == other.ports,\
            one.resources == other.resources,\
            GroupingId_name_type.compare(one,other),\
            GroupingLinks.compare(one,other),\
            ])
        return equal

    def clearData(self):
        
        self.ports.clearData()
        self.resources.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.ports ==  other.ports) or other.ports.containsDelete():
            self.ports.reducer(other.ports)
            isEmpty = False
        elif not other.ports.containsDelete():
            other.ports.clearData()
        if not (self.resources ==  other.resources) or other.resources.containsDelete():
            self.resources.reducer(other.resources)
            isEmpty = False
        elif not other.resources.containsDelete():
            other.resources.clearData()
        GroupingLinks.reducer(self,other)
        GroupingId_name_type.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.ports == other.ports,\
            self.resources == other.resources,\
            GroupingId_name_type.compare(self,other),\
            GroupingLinks.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            self.ports.setOperation(operation)
            self.resources.setOperation(operation)
            GroupingId_name_type.setOperation(self,operation)
            GroupingLinks.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.ports.containsDelete():
            return True
        if self.resources.containsDelete():
            return True
        if GroupingId_name_type.containsDelete(self):
            return True
        if GroupingLinks.containsDelete(self):
            return True
        return False


#YANG construct: grouping nodes
class GroupingNodes(Yang):
    def __init__(self, parent=None):
        super(GroupingNodes, self).__init__(parent)
        #my keyword is: list
        self.node = ListYang(parent=self, tag="node")
        """:type: list(Node)"""

    def _parse(self, parent=None, root=None):
        e_node = root.find("node")
        while e_node is not None:
            item = Node.parse(self, e_node)
            for key in e_node.attrib.keys():
                if key == "operation":
                    item.setOperation(e_node.attrib[key])
                    item.operation = e_node.attrib[key]
            key = item.getKeyValue()
            self.node[key] = item
            root.remove(e_node)
            e_node = root.find("node")

    def _et(self, node, inherited=False):
        self.node._et(node)
        return node

    def add(self, item):
        if type(item) is tuple or type(item) is list:
            for i in item:
                self.add(i)
        else:
            self.node[item.getKeyValue()] = item

    def delete(self, item):
        if type(item) is str or type(item) is int:
            if item in self.node.getKeys():
                self.node.delete(item)
        elif type(item) is tuple or type(item) is list:
            for i in item:
                self.delete(i)
        else:
            self.node.delete(item.getKeyValue())

    def __getitem__(self, key):
        return self.node[key]

    def __iter__(self):
        return self.node._data.itervalues()

        
    def isInitialized(self):
        inited = False
        inited = inited or self.node.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.node == other.node,\
            ])
        return equal

    def clearData(self):
        
        self.node.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.node ==  other.node) or other.node.containsDelete():
            self.node.reducer(other.node)
            isEmpty = False
        elif not other.node.containsDelete():
            other.node.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.node == other.node,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.node.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.node.containsDelete():
            return True
        return False


#YANG construct: grouping infra-node
class GroupingInfra_node(GroupingNode, GroupingFlowtable):
    def __init__(self, parent=None, id=None, name=None, type=None, ports=None, links=None, resources=None, NF_instances=None, capabilities=None, flowtable=None):
        GroupingNode.__init__(self, parent, id, name, type, ports, links, resources)
        GroupingFlowtable.__init__(self, parent, flowtable)
        #my keyword is: container
        self.NF_instances = None
        """:type: Infra_nodeNf_instances"""
        if NF_instances is not None:
            self.NF_instances = NF_instances
        else:
            self.NF_instances = Infra_nodeNf_instances(parent=self)
        #my keyword is: container
        self.capabilities = None
        """:type: Infra_nodeCapabilities"""
        if capabilities is not None:
            self.capabilities = capabilities
        else:
            self.capabilities = Infra_nodeCapabilities(parent=self)

    def _parse(self, parent=None, root=None):
        GroupingNode._parse(self, parent, root)
        GroupingFlowtable._parse(self, parent, root)
        e_NF_instances = root.find("NF_instances")
        if e_NF_instances is not None:
            self.NF_instances= Infra_nodeNf_instances.parse(self, e_NF_instances)
            for key in e_NF_instances.attrib.keys():
                if key == "operation":
                    item.setOperation(e_NF_instances.attrib[key])
                    item.operation = e_NF_instances.attrib[key]
        e_capabilities = root.find("capabilities")
        if e_capabilities is not None:
            self.capabilities= Infra_nodeCapabilities.parse(self, e_capabilities)
            for key in e_capabilities.attrib.keys():
                if key == "operation":
                    item.setOperation(e_capabilities.attrib[key])
                    item.operation = e_capabilities.attrib[key]

    def _et(self, node, inherited=False):
        GroupingNode._et(self, node, True)
        if self.NF_instances.isInitialized():
            self.NF_instances._et(node)
        if self.capabilities.isInitialized():
            self.capabilities._et(node)
        GroupingFlowtable._et(self, node, True)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.NF_instances.isInitialized()
        inited = inited or self.capabilities.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.NF_instances == other.NF_instances,\
            one.capabilities == other.capabilities,\
            GroupingNode.compare(one,other),\
            GroupingFlowtable.compare(one,other),\
            ])
        return equal

    def clearData(self):
        
        self.NF_instances.clearData()
        self.capabilities.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.NF_instances ==  other.NF_instances) or other.NF_instances.containsDelete():
            self.NF_instances.reducer(other.NF_instances)
            isEmpty = False
        elif not other.NF_instances.containsDelete():
            other.NF_instances.clearData()
        if not (self.capabilities ==  other.capabilities) or other.capabilities.containsDelete():
            self.capabilities.reducer(other.capabilities)
            isEmpty = False
        elif not other.capabilities.containsDelete():
            other.capabilities.clearData()
        GroupingFlowtable.reducer(self,other)
        GroupingNode.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.NF_instances == other.NF_instances,\
            self.capabilities == other.capabilities,\
            GroupingNode.compare(self,other),\
            GroupingFlowtable.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            self.NF_instances.setOperation(operation)
            self.capabilities.setOperation(operation)
            GroupingNode.setOperation(self,operation)
            GroupingFlowtable.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.NF_instances.containsDelete():
            return True
        if self.capabilities.containsDelete():
            return True
        if GroupingNode.containsDelete(self):
            return True
        if GroupingFlowtable.containsDelete(self):
            return True
        return False


#YANG construct: list flowentry
class Flowentry(GroupingFlowentry, ListedYang):
    def __init__(self, parent=None, id=None, name=None, priority=None, port=None, match=None, action=None, out=None, resources=None):
        GroupingFlowentry.__init__(self, parent, id, name, priority, port, match, action, out, resources)
        self.tag="flowentry"

    def _parse(self, parent=None, root=None):
        GroupingFlowentry._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingFlowentry._et(self, node, True)
        return node

    def getKeyValue(self):
        return self.id.getValue()

    def getKeys(self):
        return self.id.tag

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingFlowentry.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingFlowentry.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingFlowentry.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingFlowentry.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingFlowentry.containsDelete(self):
            return True
        return False


#YANG construct: list link
class Link(GroupingLink, ListedYang):
    def __init__(self, parent=None, id=None, name=None, src=None, dst=None, resources=None):
        GroupingLink.__init__(self, parent, id, name, src, dst, resources)
        self.tag="link"

    def _parse(self, parent=None, root=None):
        GroupingLink._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingLink._et(self, node, True)
        return node

    def getKeyValue(self):
        keys =[]
        keys.append(self.src.getValue())
        keys.append(self.dst.getValue())
        return tuple(keys)

    def getKeys(self):
        keys =[]
        keys.append(self.src.tag)
        keys.append(self.dst.tag)
        return tuple(keys)

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingLink.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingLink.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingLink.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingLink.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingLink.containsDelete(self):
            return True
        return False


#YANG construct: list port
class Port(GroupingPort, ListedYang):
    def __init__(self, parent=None, id=None, name=None, port_type=None, capability=None, sap=None):
        GroupingPort.__init__(self, parent, id, name, port_type, capability, sap)
        self.tag="port"

    def _parse(self, parent=None, root=None):
        GroupingPort._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingPort._et(self, node, True)
        return node

    def getKeyValue(self):
        return self.id.getValue()

    def getKeys(self):
        return self.id.tag

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingPort.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingPort.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingPort.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingPort.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingPort.containsDelete(self):
            return True
        return False


#YANG construct: list node
class Node(GroupingNode, ListedYang):
    def __init__(self, parent=None, id=None, name=None, type=None, ports=None, links=None, resources=None):
        GroupingNode.__init__(self, parent, id, name, type, ports, links, resources)
        self.tag="node"

    def _parse(self, parent=None, root=None):
        GroupingNode._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingNode._et(self, node, True)
        return node

    def getKeyValue(self):
        return self.id.getValue()

    def getKeys(self):
        return self.id.tag

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingNode.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingNode.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingNode.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingNode.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingNode.containsDelete(self):
            return True
        return False


#YANG construct: list node
class Infra_node(GroupingInfra_node, ListedYang):
    def __init__(self, parent=None, id=None, name=None, type=None, ports=None, links=None, resources=None, NF_instances=None, capabilities=None, flowtable=None):
        GroupingInfra_node.__init__(self, parent, id, name, type, ports, links, resources, NF_instances, capabilities, flowtable)
        self.tag="node"

    def _parse(self, parent=None, root=None):
        GroupingInfra_node._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingInfra_node._et(self, node, True)
        return node

    def getKeyValue(self):
        return self.id.getValue()

    def getKeys(self):
        return self.id.tag

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingInfra_node.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingInfra_node.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingInfra_node.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingInfra_node.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingInfra_node.containsDelete(self):
            return True
        return False


#YANG construct: container resources
class FlowentryResources(GroupingLink_resource):
    def __init__(self, parent=None, delay=None, bandwidth=None):
        GroupingLink_resource.__init__(self, parent, delay, bandwidth)
        self.tag="resources"

    def _parse(self, parent=None, root=None):
        GroupingLink_resource._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingLink_resource._et(self, node, True)
        return node


    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingLink_resource.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingLink_resource.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingLink_resource.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingLink_resource.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingLink_resource.containsDelete(self):
            return True
        return False


#YANG construct: container flowtable
class FlowtableFlowtable(Yang):
    def __init__(self, parent=None):
        super(FlowtableFlowtable, self).__init__(parent)
        self.tag="flowtable"
        #my keyword is: list
        self.flowentry = ListYang(parent=self, tag="flowentry")
        """:type: list(Flowentry)"""

    def _parse(self, parent=None, root=None):
        e_flowentry = root.find("flowentry")
        while e_flowentry is not None:
            item = Flowentry.parse(self, e_flowentry)
            for key in e_flowentry.attrib.keys():
                if key == "operation":
                    item.setOperation(e_flowentry.attrib[key])
                    item.operation = e_flowentry.attrib[key]
            key = item.getKeyValue()
            self.flowentry[key] = item
            root.remove(e_flowentry)
            e_flowentry = root.find("flowentry")

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        self.flowentry._et(node)
        return node

    def add(self, item):
        if type(item) is tuple or type(item) is list:
            for i in item:
                self.add(i)
        else:
            self.flowentry[item.getKeyValue()] = item

    def delete(self, item):
        if type(item) is str or type(item) is int:
            if item in self.flowentry.getKeys():
                self.flowentry.delete(item)
        elif type(item) is tuple or type(item) is list:
            for i in item:
                self.delete(i)
        else:
            self.flowentry.delete(item.getKeyValue())

    def __getitem__(self, key):
        return self.flowentry[key]

    def __iter__(self):
        return self.flowentry._data.itervalues()

        
    def isInitialized(self):
        inited = False
        inited = inited or self.flowentry.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.flowentry == other.flowentry,\
            ])
        return equal

    def clearData(self):
            self.flowentry.clearData()
            

    def clearData(self):
        
        self.flowentry.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.flowentry ==  other.flowentry) or other.flowentry.containsDelete():
            self.flowentry.reducer(other.flowentry)
            isEmpty = False
        elif not other.flowentry.containsDelete():
            other.flowentry.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.flowentry == other.flowentry,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.flowentry.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.flowentry.containsDelete():
            return True
        return False

#YANG construct: container resources
class LinkResources(GroupingLink_resource):
    def __init__(self, parent=None, delay=None, bandwidth=None):
        GroupingLink_resource.__init__(self, parent, delay, bandwidth)
        self.tag="resources"

    def _parse(self, parent=None, root=None):
        GroupingLink_resource._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingLink_resource._et(self, node, True)
        return node


    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingLink_resource.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingLink_resource.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingLink_resource.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingLink_resource.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingLink_resource.containsDelete(self):
            return True
        return False


#YANG construct: container links
class LinksLinks(Yang):
    def __init__(self, parent=None):
        super(LinksLinks, self).__init__(parent)
        self.tag="links"
        #my keyword is: list
        self.link = ListYang(parent=self, tag="link")
        """:type: list(Link)"""

    def _parse(self, parent=None, root=None):
        e_link = root.find("link")
        while e_link is not None:
            item = Link.parse(self, e_link)
            for key in e_link.attrib.keys():
                if key == "operation":
                    item.setOperation(e_link.attrib[key])
                    item.operation = e_link.attrib[key]
            key = item.getKeyValue()
            self.link[key] = item
            root.remove(e_link)
            e_link = root.find("link")

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        self.link._et(node)
        return node

    def add(self, item):
        if type(item) is tuple or type(item) is list:
            for i in item:
                self.add(i)
        else:
            self.link[item.getKeyValue()] = item

    def delete(self, item):
        if type(item) is str or type(item) is int:
            if item in self.link.getKeys():
                self.link.delete(item)
        elif type(item) is tuple or type(item) is list:
            for i in item:
                self.delete(i)
        else:
            self.link.delete(item.getKeyValue())

    def __getitem__(self, key):
        return self.link[key]

    def __iter__(self):
        return self.link._data.itervalues()

        
    def isInitialized(self):
        inited = False
        inited = inited or self.link.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.link == other.link,\
            ])
        return equal

    def clearData(self):
            self.link.clearData()
            

    def clearData(self):
        
        self.link.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.link ==  other.link) or other.link.containsDelete():
            self.link.reducer(other.link)
            isEmpty = False
        elif not other.link.containsDelete():
            other.link.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.link == other.link,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.link.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.link.containsDelete():
            return True
        return False


#YANG construct: container ports
class NodePorts(Yang):
    def __init__(self, parent=None):
        super(NodePorts, self).__init__(parent)
        self.tag="ports"
        #my keyword is: list
        self.port = ListYang(parent=self, tag="port")
        """:type: list(Port)"""

    def _parse(self, parent=None, root=None):
        e_port = root.find("port")
        while e_port is not None:
            item = Port.parse(self, e_port)
            for key in e_port.attrib.keys():
                if key == "operation":
                    item.setOperation(e_port.attrib[key])
                    item.operation = e_port.attrib[key]
            key = item.getKeyValue()
            self.port[key] = item
            root.remove(e_port)
            e_port = root.find("port")

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        self.port._et(node)
        return node

    def add(self, item):
        if type(item) is tuple or type(item) is list:
            for i in item:
                self.add(i)
        else:
            self.port[item.getKeyValue()] = item

    def delete(self, item):
        if type(item) is str or type(item) is int:
            if item in self.port.getKeys():
                self.port.delete(item)
        elif type(item) is tuple or type(item) is list:
            for i in item:
                self.delete(i)
        else:
            self.port.delete(item.getKeyValue())

    def __getitem__(self, key):
        return self.port[key]

    def __iter__(self):
        return self.port._data.itervalues()

        
    def isInitialized(self):
        inited = False
        inited = inited or self.port.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.port == other.port,\
            ])
        return equal

    def clearData(self):
            self.port.clearData()
            

    def clearData(self):
        
        self.port.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.port ==  other.port) or other.port.containsDelete():
            self.port.reducer(other.port)
            isEmpty = False
        elif not other.port.containsDelete():
            other.port.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.port == other.port,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.port.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.port.containsDelete():
            return True
        return False


#YANG construct: container resources
class NodeResources(GroupingSoftware_resource):
    def __init__(self, parent=None, cpu=None, mem=None, storage=None):
        GroupingSoftware_resource.__init__(self, parent, cpu, mem, storage)
        self.tag="resources"

    def _parse(self, parent=None, root=None):
        GroupingSoftware_resource._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingSoftware_resource._et(self, node, True)
        return node


    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingSoftware_resource.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingSoftware_resource.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingSoftware_resource.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingSoftware_resource.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingSoftware_resource.containsDelete(self):
            return True
        return False


#YANG construct: container NF_instances
class Infra_nodeNf_instances(GroupingNodes):
    def __init__(self, parent=None):
        GroupingNodes.__init__(self, parent, )
        self.tag="NF_instances"

    def _parse(self, parent=None, root=None):
        GroupingNodes._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingNodes._et(self, node, True)
        return node


    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingNodes.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingNodes.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingNodes.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingNodes.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingNodes.containsDelete(self):
            return True
        return False


#YANG construct: container capabilities
class Infra_nodeCapabilities(Yang):
    def __init__(self, parent=None, supported_NFs=None):
        super(Infra_nodeCapabilities, self).__init__(parent)
        self.tag="capabilities"
        #my keyword is: container
        self.supported_NFs = None
        """:type: Infra_nodeCapabilitiesSupported_nfs"""
        if supported_NFs is not None:
            self.supported_NFs = supported_NFs
        else:
            self.supported_NFs = Infra_nodeCapabilitiesSupported_nfs(parent=self)

    def _parse(self, parent=None, root=None):
        e_supported_NFs = root.find("supported_NFs")
        if e_supported_NFs is not None:
            self.supported_NFs= Infra_nodeCapabilitiesSupported_nfs.parse(self, e_supported_NFs)
            for key in e_supported_NFs.attrib.keys():
                if key == "operation":
                    item.setOperation(e_supported_NFs.attrib[key])
                    item.operation = e_supported_NFs.attrib[key]

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        if self.supported_NFs.isInitialized():
            self.supported_NFs._et(node)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.supported_NFs.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.supported_NFs == other.supported_NFs,\
            ])
        return equal

    def clearData(self):
        
        self.supported_NFs.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.supported_NFs ==  other.supported_NFs) or other.supported_NFs.containsDelete():
            self.supported_NFs.reducer(other.supported_NFs)
            isEmpty = False
        elif not other.supported_NFs.containsDelete():
            other.supported_NFs.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.supported_NFs == other.supported_NFs,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.supported_NFs.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.supported_NFs.containsDelete():
            return True
        return False


#YANG construct: container supported_NFs
class Infra_nodeCapabilitiesSupported_nfs(GroupingNodes):
    def __init__(self, parent=None):
        GroupingNodes.__init__(self, parent, )
        self.tag="supported_NFs"

    def _parse(self, parent=None, root=None):
        GroupingNodes._parse(self, parent, root)

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingNodes._et(self, node, True)
        return node


    @classmethod
    def compare(cls, one, other):
        equal = all([\
            GroupingNodes.compare(one,other),\
            ])
        return equal

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        GroupingNodes.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            GroupingNodes.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            GroupingNodes.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if GroupingNodes.containsDelete(self):
            return True
        return False


#YANG construct: container virtualizer
class Virtualizer(GroupingId_name, GroupingLinks):
    """Container for a single virtualizer"""
    def __init__(self, parent=None, id=None, name=None, nodes=None, links=None):
        GroupingId_name.__init__(self, parent, id, name)
        GroupingLinks.__init__(self, parent, links)
        self.tag="virtualizer"
        #my keyword is: container
        self.nodes = None
        """:type: VirtualizerNodes"""
        if nodes is not None:
            self.nodes = nodes
        else:
            self.nodes = VirtualizerNodes(parent=self)

    def _parse(self, parent=None, root=None):
        GroupingId_name._parse(self, parent, root)
        GroupingLinks._parse(self, parent, root)
        e_nodes = root.find("nodes")
        if e_nodes is not None:
            self.nodes= VirtualizerNodes.parse(self, e_nodes)
            for key in e_nodes.attrib.keys():
                if key == "operation":
                    item.setOperation(e_nodes.attrib[key])
                    item.operation = e_nodes.attrib[key]

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        GroupingId_name._et(self, node, True)
        if self.nodes.isInitialized():
            self.nodes._et(node)
        GroupingLinks._et(self, node, True)
        return node

    def isInitialized(self):
        inited = False
        inited = inited or self.nodes.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.nodes == other.nodes,\
            GroupingId_name.compare(one,other),\
            GroupingLinks.compare(one,other),\
            ])
        return equal

    def clearData(self):
        
        self.nodes.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.nodes ==  other.nodes) or other.nodes.containsDelete():
            self.nodes.reducer(other.nodes)
            isEmpty = False
        elif not other.nodes.containsDelete():
            other.nodes.clearData()
        GroupingLinks.reducer(self,other)
        GroupingId_name.reducer(self,other)
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.nodes == other.nodes,\
            GroupingId_name.compare(self,other),\
            GroupingLinks.compare(self,other),\
            ])
        return equal

    def setOperation(self, operation):
            self.nodes.setOperation(operation)
            GroupingId_name.setOperation(self,operation)
            GroupingLinks.setOperation(self,operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.nodes.containsDelete():
            return True
        if GroupingId_name.containsDelete(self):
            return True
        if GroupingLinks.containsDelete(self):
            return True
        return False


#YANG construct: container nodes
class VirtualizerNodes(Yang):
    def __init__(self, parent=None):
        super(VirtualizerNodes, self).__init__(parent)
        self.tag="nodes"
        #my keyword is: list
        self.node = ListYang(parent=self, tag="node")
        """:type: list(Infra_node)"""

    def _parse(self, parent=None, root=None):
        e_node = root.find("node")
        while e_node is not None:
            item = Infra_node.parse(self, e_node)
            for key in e_node.attrib.keys():
                if key == "operation":
                    item.setOperation(e_node.attrib[key])
                    item.operation = e_node.attrib[key]
            key = item.getKeyValue()
            self.node[key] = item
            root.remove(e_node)
            e_node = root.find("node")

    def _et(self, node=None):
        if node is not None:
            node= ET.SubElement(node, self.tag)
        else:
            node= ET.Element(self.tag)
        self.node._et(node)
        return node

    def add(self, item):
        if type(item) is tuple or type(item) is list:
            for i in item:
                self.add(i)
        else:
            self.node[item.getKeyValue()] = item

    def delete(self, item):
        if type(item) is str or type(item) is int:
            if item in self.node.getKeys():
                self.node.delete(item)
        elif type(item) is tuple or type(item) is list:
            for i in item:
                self.delete(i)
        else:
            self.node.delete(item.getKeyValue())

    def __getitem__(self, key):
        return self.node[key]

    def __iter__(self):
        return self.node._data.itervalues()

        
    def isInitialized(self):
        inited = False
        inited = inited or self.node.isInitialized()
        return inited
        

    @classmethod
    def compare(cls, one, other):
        equal = all([\
            one.node == other.node,\
            ])
        return equal

    def clearData(self):
            self.node.clearData()
            

    def clearData(self):
        
        self.node.clearData()
        

    def reducer(self, other):
        isEmpty = True
        if hasattr(other,'id'):
            tempId = copy.deepcopy(other.id)
        
        if not (self.node ==  other.node) or other.node.containsDelete():
            self.node.reducer(other.node)
            isEmpty = False
        elif not other.node.containsDelete():
            other.node.clearData()
        if hasattr(other,'id') and not isEmpty:
            other.id = tempId
        return isEmpty
    
    def __eq__(self, other):
        equal = all([\
            self.node == other.node,\
            ])
        return equal

    def setOperation(self, operation):
            self.operation = "delete"
            self.node.setOperation(operation)

    def containsDelete(self):
        if self.operation == 'delete':
            return True
        if self.node.containsDelete():
            return True
        return False


