from datetime import datetime
from typing import Literal, Union

EngineSettingKeys = Literal["units", "start_time", "start_date", "stop_time", "stop_date", "seed"]
"""Valid keys related to the engine settings; used when passing the dictionary with override values in the `AnyLogicSim`'s constructor keyword argument"""

Number = Union[int, float]
"""Describes any valid number type"""

OutputType = Union[int, float, str, bool, datetime, "UnitValue", "StatisticsDiscrete", "StatisticsContinuous", "DataSet", "HistogramSimpleData", "HistogramSmartData", "Histogram2DData"]
"""Describes the types from calling `outputs()`; includes all analysis and Output objects (anything with units are described by `UnitValue`)"""

