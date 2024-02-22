Border Checkpoint Optimization
==============================

This is a modified version of the example from the built-in repository called "Border Checkpoint". It represents the process of crossing an international border at an official checkpoint. Passport control and vehicle inspection processes are separated for tourists arriving by buses and those who travel by car. There exists two resource pools for the bus inspectors and car inspectors; standard inspection requires one of each resource, however in depth car searches require two inspectors - whether two car inspectors (preferred) or one of each.


## Usage

To start, open the model's source and export it as a zip inside the "ModelExported" folder. As the provided optimize.py script is written to execute parallel runs and the model includes a database, it's required to keep it as a zip file.

The model source has parameters for optionally overriding the schedules (for the arrival rates and number of inspectors for cars and buses) with fixed values. Though, this is mainly provided for the purpose of testing and for having the inspector parameters assignable in the Configuration space. 

The intended way to optimize for a single shift is to set the start and stop dates based on when a shift starts and stops. After optimizing, when running the model to evaluate the schedules, and namely past the duration of one shift, values should be modified in the provided Excel file.

## Spaces

### Configuration

| Name             | Type | Default | Description                                                                |
|------------------|------|---------|----------------------------------------------------------------------------|
| numCarInspectors | int  | 0       | How many car inspectors to employ for the duration of the simulation model |
| numBusInspectors | int  | 0       | How many bus inspectors to employ for the duration of the simulation model |

Note: Setting both values to 0 will cause the sim to use the built-in schedule (i.e., pulling from the Excel file), rather than a fixed value. This is intended for evaluating the optimized schedule outside of AnyLogic.

### Observation

| Name          | Type   | Description                                                                 |
|---------------|--------|-----------------------------------------------------------------------------|
| carsQueueing  | int    | How many cars are queueing at or before the checkpoint                      |
| busesQueueing | int    | How many buses are queueing at or before the checkpoint                     |
| carTISMean    | double | The cumulative mean time in system (model units, default minutes) for cars  |
| carTISMax     | double | The cumulative max time in system (model units, default minutes) for cars   |
| busTISMean    | double | The cumulative mean time in system (model units, default minutes) for buses |
| busTISMax     | double | The cumulative max time in system (model units, default minutes) for buses  |

### Stop condition
false (i.e., no invalid conditions)

### Action

| Name | Type | Description |
|------|------|-------------|

(None)

### Outputs

| Name                | Type          | Description                                                                                                         |
|---------------------|---------------|---------------------------------------------------------------------------------------------------------------------|
| carTimeAtCheckpoint | HistogramData | Distribution for time (model units, default minutes) cars spent at the checkpoint (i.e., not including queue time)  |
| busTimeAtCheckpoint | HistogramData | Distribution for time (model units, default minutes) buses spent at the checkpoint (i.e., not including queue time) |
| carTimeInSystem     | HistogramData | Distribution for time (model units, default minutes) cars spent in the system                                       |
| busTimeInSystem     | HistogramData | Distribution for time (model units, default minutes) buses spent in the system                                      |

Note: The mean/max of the "TimeInSystem" are reflected in the observation; they are documented here for the sake of completeness.