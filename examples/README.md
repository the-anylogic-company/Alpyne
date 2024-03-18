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

Before running the example scripts, you'll need to first export them from AnyLogic. To run them without any modifications, you'll need to do the following:

1. Open the given model in AnyLogic (e.g., `examples/Pathfinder/ModelSource/Pathfinder.alp`)
2. In the properties of its RL Experiment, click the export button at the top; save the zip file inside a folder named "ModelExported" to sit alongside the "ModelSource" folder
3. Most examples are setup expecting the zip file to be unpacked in-place (such that the file `ModelExported/model.jar` is valid); see the individual models' README for more specifics.
4. Run the associated Python script
