*mapping.py* module
===================

Contains abstract classes for NFFG mapping.

Classes of the module:

.. inheritance-diagram::
   escape.util.mapping
   :parts: 1

:any:`AbstractMappingStrategy` is an abstract class for containing entirely
the mapping algorithm as a class method.

:any:`ProcessorError` can signal unfulfilled requirements.

:any:`AbstractMappingDataProcessor` is an abstract class to implement pre and
post processing functions right before/after the mapping.

:any:`ProcessorSkipper` implements a non-processing class to skip pre/post
processing gracefully.

:any:`PrePostMapNotifier` is simple processor class for notifying other POX
modules about pre/post map event.

:any:`PreMapEvent` signals pre-mapping event.

:any:`PostMapEvent` signals post-mapping event.

:any:`AbstractMapper` is an abstract class for orchestration method which
should implement mapping preparations and invoke actual mapping algorithm.

:any:`AbstractOrchestrator` implements the common functionality for
orchestrator's in different layers.

Module contents
---------------

.. automodule:: escape.util.mapping
   :members:
   :private-members:
   :special-members:
   :exclude-members: __dict__,__weakref__,__module__
   :undoc-members:
   :show-inheritance:


