
Event sequence in model creation process
========================================

.. epigraph::
    **Summary:** The starting of an AnyLogic model internally goes through multiple stages. Users may want to be familiar with this if the model startup is a sensitive time with critical events occuring.

.. figure:: _static/adv-event-sequence-01.png
   :alt: Conceptual illustration of setting up the engine, creating the model elements, starting, and running the model
   :align: center

The starting of an AnyLogic model has multiple stages. The order that
events occur is important when you want to initialize the model in a
specific manner. In these cases, to determine the right step for your
initialization task, you'll need to understand the differences between
each stage of the initialization process. The following is an overview
of this process.

1. **Building the simulation “engine”**: The engine drives the model
execution and maintains the event queue, the default random number
generator, etc. High-level parameters related to the experiment are
setup immediately after the engine’s creation (e.g., model time unit,
RNG, start/end time or date).

2. **Creating the top-level agent (e.g., Main) and the immediate
objects inside it.** At this point, the object for the top-level agent
is created. References to the objects within it are created, but not
yet initialized: simple objects, like variables or parameters, can be
assigned at this stage; however, populations and collections are still
empty.

.. important:: At the end of this step – where just the top-level agent is created - is when that the Configuration parameters of an RL experiment are used to initialize each simulation run (training episode).

3. **Engine starts in preparation for the model execution**: At this
point, the Engine will then instantiate all complex objects inside the
model environment and start their initialization activities (e.g.,
scheduling initial events). First, complex objects (nested agents)
will be instantiated from the top-level agent (possibly constructed
from parameter values, if the model is setup to do so) downwards, into
the nested agents. Second, all agents in the environment with be
started. The starting order differs from the creation order. This
startup happens in inner agents first, then outwards towards their
encompassing environment (e.g., top-level agent). At the end of this
step is when “time” can begin.

Modelers often want to add custom initialization tasks before the
model starts to run. That’s why every agent (including the top-level
agent) has a code extension “On startup” field. The model executes the
code you add to this field during the final stage of the start
process.

The code you add to “On Startup” of nested agents get executed before
their encompassing agent. However, if you schedule events in “On
startup” fields, the event that is in the encompassing agent’s On
Startup will be executed first due to the default LIFO order of
execution!

.. important:: You can only pause the engine – for example, to call the ``takeAction`` function (which pauses the model to trigger an iteration) - in a running model! Since the code in the “On Startup” field is executed before the model is running, attempting to call ``takeAction`` will not do anything!

4. **Engine runs, and scheduled events get executed**: At this point,
all elements of the model are created, and all the initial events are
scheduled. The engine now begins running and executing the events.

.. note:: If you have an event in the model that is set to run at time zero (e.g., via an Event with a Trigger Type of “Timeout” and “occurrence time” equal to zero), it will happen at the start of this stage – thus occurring after the events set on the previous step (On Startup)
