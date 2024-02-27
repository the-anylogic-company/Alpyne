# Stock Management Game (RL)

This is a modified version of the model in the built-in repository with the same base name. It depicts a single warehouse in a supply chain, modeled at a very abstract level: the warehouse has an inventory level ("stock") which it continuously adds to at a given rate ("order rate"); the supplied rate can be updated at any point in range \[0, 50\], but any change is lagged in updating. Concurrently, the stock is continuously consumed (i.e., demand) at a fluctuating rate which changes daily; its real value and its fluctuations are intended to be information exogenous to any sort of controller/policy. If there is not enough stock to supply the demand, it should be considered lost sales (though it is not tracked by the model); it is assumed the warehouse can stock approximately 10,000 units, though there is no technical upper limit.

The goal is to learn a policy which is able to control the order rate such that the held stock remains high enough to avoid loss in sales, but not too high that it approaches the assumed maximum.

## Usage

⚠️To export the model without compile-time errors and without changing the source, you'll need to at least add the Pypeline library to your AnyLogic environment ([on GitHub](https://github.com/t-wolfeadam/AnyLogic-Pypeline)). For running inferences on the trained policy, you will need to configure the PyCommunicator object in the model to point to your desired Python environment.

The model's Main agent has a "mode" parameter that can be in one of four operational modes:

- User-controlled: Pauses to allow you to control the assigned order rate via a slider before auto-resuming
- Automatic: Enables automatic control of the set order rate; choosing this allows you to set the "autoMode" parameter, which has static, random, and heuristic options
- AI training: Calls the RL Experiment's `takeAction` function
- AI testing: Uses the *Pypeline* add-on to enable requesting updated values for the new rate based on the observation, passed as a JSON string (logic defined in the Python script within the source folder)

The provided script expects an unzipped version of the exported model (i.e., `ModelExported\model.jar` should be a valid file path). It trains a PPO policy using the Stable Baselines library. It's saved as a zip file and loaded in using the Pypeline add-on library for AnyLogic and a helper script.

## Spaces

### Configuration

| Name                   | Type       | Default       | Description                                                               |
|------------------------|------------|---------------|---------------------------------------------------------------------------|
| acquisition_lag_days   | int        | 7             | How many days between a set order rate and when it's updated              |
| action_recurrence_days | double     | 30            | How many days to simulate between actions                                 |
| stop_condition_limits  | double\[\] | \[500, 9500\] | The min/max allowed stock levels without considering the episode "failed" |
| demand_volatility      | double     | 0.5           | The sigma parameter of the normal distribution for demand noise           |

### Observation

Note: the intended observation for a learning policy is similar to the one the end user can see in the original model - that is, information about the current and historical stock level and the current and historical order rate. Any additional information - namely pertaining to the demand - is provided but intended to be for debugging purposes only.

| Name       | Type   | Description                                                           |
|------------|--------|-----------------------------------------------------------------------|
| stock      | double | Amount of stock held                                                  |
| last_stock | double | How much stock held at the last action                                |
| order_rate | double | The current order rate (i.e., the last action, when recurrence > lag) |
| demand     | double | The current demand, provided for debugging purposes only              |

### Stop condition
If the stock level was detected as being outside the limits provided by the configuration (checked daily).

### Action

| Name       | Type   | Description                                                     |
|------------|--------|-----------------------------------------------------------------|
| order_rate | double | The new order rate to set; clipped to the valid range, (0 - 50) |

### Outputs

| Name             | Type           | Description                                                           |
|------------------|----------------|-----------------------------------------------------------------------|
| amountSold       | Output[double] | How much total stock was sold; updated on simulation end              |
| demandRateDS     | DataSet        | Daily demands, up to the last year                                    |
| assignedRatesHD  | Histogram      | Distribution of assigned order rates (i.e., actions)                  |
| demandByRate     | Histogram2D    | 2D Distribution of demand (X) by order rate (Y); updated once per day |
| stockAmountStats | Statistics     | Statistics on stock amounts; updated once per day                     |
