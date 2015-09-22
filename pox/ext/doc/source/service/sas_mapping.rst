*sas_mapping.py* module
=======================

Contains classes which implement SG mapping functionality.

.. inheritance-diagram::
   escape.service.sas_mapping.DefaultServiceMappingStrategy
   escape.service.sas_mapping.SGMappingFinishedEvent
   escape.service.sas_mapping.ServiceGraphMapper
   :parts: 3

:any:`DefaultServiceMappingStrategy` implements a default mapping algorithm
which map given SG on a single Bis-Bis.

:any:`SGMappingFinishedEvent` can signal end of service graph mapping.

:any:`ServiceGraphMapper` perform the supplementary tasks for SG mapping.

Module contents
---------------

.. automodule:: escape.service.sas_mapping
   :members:
   :private-members:
   :special-members:
   :exclude-members: __dict__,__weakref__,__module__
   :undoc-members:
   :show-inheritance:



