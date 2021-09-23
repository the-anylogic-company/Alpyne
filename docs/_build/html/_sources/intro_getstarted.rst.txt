
Getting started
===============

Installation
------------
Install this library by navigating to the ``dist`` directory in a terminal prompt and executing ``pip install anylogic-alpyne``/

Preparing an AnyLogic model
---------------------------
You can use *any* edition of AnyLogic (PLE, University, or Professional) with this library. However, be aware that limitations of the edition will still apply. For example, PLE users executing models which utilize industry-specific libraries have their runs limited to 1-hour simulation time). 

You will need to setup your model with the following components. For more specifics on each entry, see [[LINK]].

1. RL experiment, with the Configuration, Observation, Action, and stopping conditions filled out, as per your specifications
2. A call to the RL experiment's ``takeAction`` method, at the time you wish an action to be taken
3. (OPTIONAL) A parameter on your top-level agent for determining whether the ``takeAction`` method will be called. 
  - If the ``takeAction`` method is called through another experiment (e.g., Simulation, Parameter Variation), an error will be thrown. The parameter would be used to determine whether the method should be called. It should be true/enabled when training (e.g., you can enable it in your Configuration code) and false/disabled otherwise.

To export the model, navigate to the properties of your RL experiment and click the option at the top to export it. If you do not see an option for Alpyne or generic 3rd parties, you may use the one for "Microsoft Bonsai".

Next Steps
----------
The API and overall workflow for Alpyne is intentionally similar to the AnyLogic Cloud. In your Python code, you will create a single Client object, passing a reference to where your exported model is located, in addition to setting other options. This object then gives you access to templates for the inputs/outputs of the model in addition to methods for creating new model runs, which can then be interacted with.

You can learn more about the specifics from reviewing the other pages and the provided sample scripts.