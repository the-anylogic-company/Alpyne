# Pathfinder

This model is a toy environment depicting an agent on an 8x8 grid which has a number of "holes" the agent is trying to avoid and one "goal" space that the agent is attempting to get to. Various options allow you to control how "dangerous" the environment is and the what directions the agent is allowed to move in. 


## Usage

The model's Main agent has a "mode" parameter that can be in one of four operational modes:

- Manual: Allows you to direct which direction the agent should move in
- Random: Causes the agent to move in a random valid direction
- RL: Calls the RL Experiment's `takeAction` function
- QTable: Loads the JSON file containing a list of shape (<n_states>, <n_actions>) and takes actions based on the max value in the state its in

The provided script expects an unzipped version of the exported model (i.e., `ModelExported\model.jar` should be a valid file path). It trains a policy using basic Q-learning (i.e., no neural networks), using an implementation defined in the script. The specific board configuration (defined via the seed) and hyperparameters were optimized to ensure an interesting board configuration that would be reliable to train. The resulting policy is saved as a JSON file which is imported and parsed using the Jackson library (built into AnyLogic).

## Spaces

### Configuration

| Name                  | Type    | Default | Description                                                                                                                                                                                                                                        |
|-----------------------|---------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| useMooreNeighbors     | boolean | false   | Whether to use Moore-neighbors (8 directional) vs Euclidean (4 directional)                                                                                                                                                                        |
| slipChance            | double  | 0.0     | The chance to ignore the provided action and take a random one                                                                                                                                                                                     |
| slipChanceSeed        | Long    | null    | The seed for the PRNG dedicated to slip chances; if null, a random one is used. This is provided to allow a random stream independent from the default one which is used to control the board configuration. It has no effect if slip chance is 0. |
| numHoles              | int     | 0       | How many hole spaces to place randomly on the board                                                                                                                                                                                                |
| minStepsRequired      | int     | 0       | The minimum number of steps or movements from the agents start to the goal (randomly placed)                                                                                                                                                       |
| throwOnInvalidActions | boolean | false   | Whether to trigger a model error if attempting to perform an invalid action (moving outside board or using an ordinal direction with euclidean neighbors); when true, invalid actions are ignored and the agent stays in place                     |

Warning: With a slip chance and throwing on invalid actions, it is possible for a valid action to turn invalid or visa versa.

Note: The engine's seed determines the initial placements of all spaces and the random attempts to swap the agent/holes/empty spaces in order to ensure a path is possible and the minimum steps requirement is fulfilled.  

### Observation

| Name  | Type    | Description                                                        |
|-------|---------|--------------------------------------------------------------------|
| cells | int[][] | An 8x8 array; 0 = empty, 1 = goal, -1 = hole                       |
| pos   | int[]   | An array containing the agent's current row and column (0 indexed) |

### Stop condition
If the agent is inside a hole or the goal

### Action

| Name | Type   | Description                                                                                                  |
|------|--------|--------------------------------------------------------------------------------------------------------------|
| dir  | String | Direction to move the agent in; a constant from AnyLogic's `CellDirection` enum (e.g., "NORTH", "NORTHEAST") |

### Outputs

| Name  | Type           | Description                                                                                                |
|-------|----------------|------------------------------------------------------------------------------------------------------------|
| score | Output[double] | -1 if the agent is in a hole, 1 if in the goal space, 0 for empty position; updated on the model finishing |