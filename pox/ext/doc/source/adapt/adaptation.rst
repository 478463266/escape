*adaptation.py* module
======================

Contains classes relevant to the main adaptation function of the Controller
Adaptation Sublayer.

.. figure::  ../_static/adaptation.png
   :align:  center

:any:`ComponentConfigurator` creates, initializes, stores and manages different
adaptation components, i.e. derived classes of :any:`AbstractDomainManager` and
:any:`AbstractDomainAdapter`.

:any:`ControllerAdapter` implements the centralized functionality of high-level
adaptation and installation of :any:`NFFG`.

:any:`DomainVirtualizer` implements the standard virtualization/generalization
logic of the Resource Orchestration Sublayer.

:any:`DomainResourceManager` stores and manages the global Virtualizer.

Module contents
---------------

.. automodule:: escape.adapt.adaptation
   :members:
   :private-members:
   :special-members:
   :exclude-members: __dict__,__weakref__,__module__
   :undoc-members:
   :show-inheritance:

