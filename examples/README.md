Examples
========

This folder contains examples that are intended to cover a range of different topics and implementation options, both on the simulation side (e.g., methadology used, mechanisms to load trained policies) and the Python side (e.g., libraries and algorithms for training).

Each example has the following:

- A "ModelSource" folder containing the source AnyLogic model
- An "ModelExported" folder containing the exported RL Experiment from the model
- One or more Python scripts
- Its own README file with background about the model and what it's "solving", in addition to additional requirements

⚠️ The files for the exported model are not shipped with the repo. See the next section for more information.

Usage
-----

The necessary Python libraries needed to run all the scripts can be installed by the 'examples' optional dependency (i.e., `pip install anylogic-alpyne[examples]`).

Be aware that some AnyLogic models require you to have some custom libraries added to your AnyLogic environment, used for querying/inferencing the trained policies. These are detailed further in the specific READMEs.

Once the necessary libraries are installed, you will need to export the model. To comply with the way that the scripts are setup, do the following:

1. Open the model source in AnyLogic
2. At the top of the RL Experiment's properties, click the button to export the model as a zip; save it within the "ModelExported" folder (creating it if it does not exist)
3. In your file explorer, unpack the zip in place, such that the file "ModelExported/model.jar" is valid
4. Delete the zip file

You should now be able to run any of the scripts without errors. The way you load the information back into the model will depend on the specific example and are detailed further in the example's README.

Contributions
-------------

From improvements on existing training scripts to new models, contributions are greatly welcomed! General guidelines:

- Training scripts should, by default, be able to run in 10 minutes or less and be able to produce results that are better than random
  - Having commandline arguments for longer / more robust training is completely acceptable
- Simpler, semi-realistic models are best (like the ones in the example repository); more complex ones are OK if they are understandable by people from different industries 
- Models should be at least have implementations and toggles for "training" and "testing" (of the policy); others can be freely added (e.g., manual, heuristic)
- Models should be reasonably organized or structured (e.g., aligned elements, clean flowchart connectors)
- Use standard conventions where relevant (e.g., TitledClassNames, camelCaseJavaVariables, snake_case_python_variables)

⚠ If planning to build a model with the intention of including it in this repo, it's suggested to make a discussion post first to avoid chancing it being rejected down the line