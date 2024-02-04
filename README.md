# Alpyne

The **A**ny**L**ogic-**Py**thon con**ne**ctor

This is a Python library for interactively running models exported from the RL experiment. 

Currently, this library released as a **public beta** (so please excuse any rough edges). If you have problems or bugs, please file them in the `Issues` tab. For general talk or questions, there's the `Discussions` tab.

Full documentation (with background information, getting started guide, and class docs) can be found @ https://t-wolfeadam.github.io/Alpyne

Installation
------------
Alpyne supports Python 3.10+ and requirements the latest version of AnyLogic.

To install this library with its base minimum components, use ``pip install anylogic-alpyne``

To include the requirements necessary for running the examples, use ``pip install anylogic-alpyne[examples]``

Preparing an AnyLogic model
---------------------------
You can use *any* edition of AnyLogic (PLE, University, or Professional) with this library. However, be aware that limitations of the edition will still apply. For example, PLE users executing models which utilize industry-specific libraries have their runs limited to 1-hour simulation time. 

You will need to setup your model with the following components.

1. RL experiment, with the Configuration, Observation, Action, and stopping conditions filled out, as per your specifications
2. A call to the RL experiment's ``takeAction`` method, at the moment you wish an action to be taken

To export the model, navigate to the properties of your RL experiment and click the export button at the top.

Basic usage
-----------
In your Python code, you will create a single AnyLogicSim object which represents a connection to a single instance of your simulation model.

In creating the AnyLogicSim, you pass a reference to where your exported model is located, in addition to options for log level, engine settings, and other behavioral options.
This object then gives you access to functions for interacting with the model run, including resetting it, querying its status, applying some action, and getting outputs.

You can learn more about the specifics and deeper background information from reviewing the [documentation](https://t-wolfeadam.github.io/Alpyne) or referencing the provided examples.

Note that to run the examples, you will need to export them from AnyLogic.