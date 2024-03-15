# Activity Based Costing Analysis (RL)

This is a modified version of the model in the built-in repository with the same base name. It depicts a simplified factory floor in which each incoming product seizes one unit of resource A, then one unit of resource B, then is processed by a machine, releases A, is conveyed to the exit, and releases B just before the exit. The queues while waiting for each resource have a limited capacity; exceeding this will cause the simulation to pre-maturely stop, as if the system is exceeded its capacity.

Additionally, there are costs are associated to each part of the system which are accumulated while the products move through the system. This includes product existence cost, idle and busy costs for resources, and costs for process time (less time = faster to process = higher cost) and conveying speed (faster speed = higher cost). The resulting output metric is mean cost per product, or the cumulative costs divided by the number of products which have left the system.

The default model has an optimization experiment intended to find, *for a fixed arrival rate*, the optimal set of parameters (number of A and B resources, mean process delay, conveyor speed) such that the mean cost per product is minimized.

Reinforcement Learning is used to find a policy which is able to optimally set the parameters for any arrival rate.

## Usage

You can run the model with animation using its Simulation experiment to experiment with settings the different parameters.

The model has a parameter for "enabling a learning agent" - i.e., makes calls to the RL Experiment's `takeAction` function - which will be set to true when running the model through Alpyne.

The provided scripts expect an unzipped version of the exported model (i.e., `ModelExported\model.jar` should be a valid file path). It trains a SAC policy using the Stable Baselines library.

## Spaces

### Configuration

| Name             | Type   | Default | Description                                                                                                   |
|------------------|--------|---------|---------------------------------------------------------------------------------------------------------------|
| arrivalRate      | double | 0       | How many products arrive per day (on average); typical range: (0.1, 2)                                        |
| sizeBufferQueues | int    | 0       | The maximum agents that can wait be a resource before the run is considered "failed"; typical range: (10, 90) |

Note: The defaults shown are the ones used by the RL Experiment. Actually running the model with either set to 0 will cause unintended results or errors.

### Observation

Note: the intended observation for a learning policy is similar to the one the end user can see in the original model - that is, information about the current and historical stock level and the current and historical order rate. Any additional information - namely pertaining to the demand - is provided but intended to be for debugging purposes only.

| Name                 | Type   | Description                                                          |
|----------------------|--------|----------------------------------------------------------------------|
| arrivalRate          | double | The set rate of mean arrivals per day                                |
| utilizationResourceA | double | The current percent usage of resource A                              |
| utilizationResourceB | double | The current percent usage of resource B                              |
| ratioFullQueueA      | double | The percent of how full resource A's queue is                        |
| ratioFullQueueB      | double | The percent of how full resource B's queue is                        |
| recentNProducts      | int    | How many products have been completed                                |
| ratioCostIdleA       | double | The percent of costs attributed to resource A being idle             |
| ratioCostIdleB       | double | The percent of costs attributed to resource B being idle             |
| ratioCostWaiting     | double | The percent of costs attributed to products waiting for any resource |
| ratioCostProcessing  | double | The percent of costs attributed to time spent processing             |
| ratioCostMoving      | double | The percent of costs attributed to time spent conveying to the exit  |
| costPerProduct       | double | The all-included total cost per product                              |

### Stop condition
If either queue (for resource A or resource B) reaches its capacity

### Action

Actions are taken at time 0 and then every 6 months / 180 days (long enough to get metrics with high confidence).
As this interval is long enough to achieve a steady state, the default sim is set up to stop at this point.

| Name          | Type   | Description                                                     |
|---------------|--------|-----------------------------------------------------------------|
| numResourceA  | int    | The number of resource A agents (1-20)                          |
| numResourceB  | int    | The number of resource B agents (1-20)                          |
| processDelay  | double | The mean time (seconds) required to process each product (1-20) |
| conveyorSpeed | double | The speed (meters per second) of the conveyor (0.00001-15)      |

Note: The ranges specified are assumed to be adhered to

### Outputs

| Name                      | Type           | Description                             |
|---------------------------|----------------|-----------------------------------------|
| outputTotalCostPerProduct | Output[double] | The all-included total cost per product |

Note: This is the same as the field in the observation