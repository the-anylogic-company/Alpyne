
Getting started
===============

Installation
------------
To install this library from the source with minimum dependencies, execute ``pip install .``; from pypi, execute ``pip install anylogic-alpyne``.

To include the optional dependencies, for running the example scripts, use ``pip install .[examples]`` or ``pip install anylogic-alpyne[examples``.

Preparing an AnyLogic model
---------------------------
You can use *any* edition of AnyLogic (PLE, University, or Professional) with this library. However, be aware that limitations of the edition will still apply. For example, PLE users executing models which utilize industry-specific libraries have their runs limited to 1-hour simulation time.

You will need to setup your model with the following components. For more specifics on each entry, see the following section, `Components of an RL-ready model <components-rlready-model.html>`_ and/or the official AnyLogic `RL Experiment Help Article <https://anylogic.help/anylogic/experiments/rl-experiment.html>`_.

1. RL experiment, with the Configuration, Observation, Action, and stopping conditions filled out, as per your specifications
2. A call to the RL experiment's ``takeAction`` method, at the time you wish an action to be taken
3. (OPTIONAL) A parameter on your top-level agent for determining whether the ``takeAction`` method will be called (e.g., to avoid errors from being thrown when running other experiment types)

Afterwards, export the RL Experiment via the top button of its experiment properties or by right clicking your model > Export... > Reinforcement Learning.

.. warning:: The exported experiment is only executable by supported platforms (e.g., Alpyne) and said platforms can only execute your model exported in this way (i.e., not from any other exported experiment type).

Next Steps
----------
In your Python code, you will create a single AnyLogicSim object which represents a connection to a single instance of your model.

In creating the AnyLogicSim, you pass a reference to where your exported model is located, in addition to options for log level, engine settings, and other behavioral options.
This object then gives you access to functions for interacting with the model run, including resetting it, querying its status, applying some action, and getting outputs.

You can learn more about the specifics from reviewing the other pages and the provided sample scripts.
