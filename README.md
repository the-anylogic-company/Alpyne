# Alpyne

The **A**ny**L**ogic-**Py**thon con**ne**ctor

This is a Python library for interactively running models exported from the RL experiment. 

Currently, this library released as a **public beta** (so please excuse any rough edges). If you have problems or bugs, please file them in the `Issues` tab. For general talk or questions, there's the `Discussions` tab.

Full documentation (with background information, getting started guide, and class docs) can be found @ https://t-wolfeadam.github.io/Alpyne

All contributions, including new or improved example models and training scripts, are thoroughly welcomed! See the note at the end for more specifics.

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

Basic idea/usage
----------------
In your Python code, you will create a single AnyLogicSim object which represents a connection to a single instance of your simulation model.

In creating the AnyLogicSim, you pass a reference to where your exported model is located, in addition to options for log level, engine settings, and other behavioral options.
This object then gives you access to functions for interacting with the model run, including resetting it, querying its status, applying some action, and getting outputs.

You can learn more about the specifics and deeper background information from reviewing the [documentation](https://t-wolfeadam.github.io/Alpyne) or referencing the provided examples.

Note that some examples require additional libraries to be added in your AnyLogic environment; see their individual READMEs for more details.

Before running the example scripts, you'll need to first export them from AnyLogic. To run them without any modifications, you'll need to do the following:

1. Open the given model in AnyLogic (e.g., `examples/Pathfinder/ModelSource/Pathfinder.alp`)
2. In the properties of its RL Experiment, click the export button at the top; save the zip file inside a folder named "ModelExported" to sit alongside the "ModelSource" folder
3. Most examples are setup expecting the zip file to be unpacked in-place (such that the file `ModelExported/model.jar` is valid); see the individual models' README for more specifics.
4. Run the associated Python script

Contributing
------------
Feel free to submit contributions (in the library, its documentation, or the example models or scripts) via pull requests.

General guidelines for examples:

- Training scripts should, by default, be able to run in 10 minutes or less and be able to produce results that are better than random
  - Having commandline arguments for longer / more robust training is completely acceptable
- Simpler, semi-realistic models are best; more complex ones are OK if they are understandable by people from different industries
- Models should ideally have implementations/toggles for running in non-RL, training, and testing "modes" (the specific terminology is not important); others can be freely added (e.g., heuristic)
- Models and scripts should be reasonably organized or structured (e.g., for models: aligned elements, clean flowchart connectors)
- Use standard conventions where relevant (e.g., TitledClassNames, camelCaseJavaVariables, snake_case_python_variables)

⚠ It's suggested to make a discussion post before spending too much time on an idea to avoid chancing it being rejected down the line
