# Alpyne

The **A**ny**L**ogic-**Py**thon con**ne**ctor

This is a Python library for interactively running models exported from the RL experiment. 

Currently, this library released as a **public beta** (so please excuse any rough edges). If you have problems or bugs, please file them in the `Issues` tab. For general talk or questions, there's the `Discussions` tab.

Full documentation (with background information, getting started guide, and class docs) can be found @ https://t-wolfeadam.github.io/Alpyne

All contributions, including new or improved example models and training scripts, are thoroughly welcomed!

Installation
------------
Alpyne supports Python 3.10+ and requirements the latest version of AnyLogic (as of Mar 2024: v8.8.6).

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

Note that the example "StockManagementGame" also requires you to have installed the [Pypeline library](https://github.com/t-wolfeadam/AnyLogic-Pypeline) in your AnyLogic environment.

Before running the example scripts, you'll need to first export them from AnyLogic. To run them without any modifications, you'll need to do the following:

1. Open the given model in AnyLogic (e.g., `examples/Pathfinder/ModelSource/Pathfinder.alp`)
2. In the properties of its RL Experiment, click the export button at the top; save the zip file inside a folder named "ModelExported" to sit alongside the "ModelSource" folder
3. In your file explorer, extract the contents of the zip in place (such that, e.g., the file `examples/Pathfinder/ModelExported/model.jar` is valid)
4. Run the associated Python script
