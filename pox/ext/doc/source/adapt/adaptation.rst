*adaptation.py* module
======================

Contains classes relevant to the main adaptation function of the Controller
Adaptation Sublayer.

.. inheritance-diagram::
   escape.adapt.adaptation.ComponentConfigurator
   escape.adapt.adaptation.ControllerAdapter
   escape.adapt.adaptation.DoVChangedEvent
   escape.adapt.adaptation.DomainVirtualizer
   escape.adapt.adaptation.GlobalResourceManager
   :parts: 1

:any:`ComponentConfigurator` creates, initializes, stores and manages different
adaptation components, i.e. derived classes of :any:`AbstractDomainManager` and
:any:`AbstractESCAPEAdapter`.

:any:`ControllerAdapter` implements the centralized functionality of high-level
adaptation and installation of :any:`NFFG`.

:any:`DoVChangedEvent` can signal for the specific Virtualizers the DOV is
changed.

:any:`DomainVirtualizer` implements the standard virtualization/generalization
logic of the Resource Orchestration Sublayer.

:any:`GlobalResourceManager` stores and manages the global Virtualizer.

Module contents
---------------

.. automodule:: escape.adapt.adaptation
   :members:
   :private-members:
   :special-members:
   :exclude-members: __dict__,__weakref__,__module__
   :undoc-members:
   :show-inheritance:

