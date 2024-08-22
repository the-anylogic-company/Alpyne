from abc import abstractmethod
from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum
from math import inf
from typing import Callable

from alpyne.utils import parse_number, extended_namedtuple
from alpyne.typing import Number


@dataclass
class _AnalysisObject:
    def __new__(cls, *args, **kwargs):
        if cls is _AnalysisObject:
            raise TypeError(f"only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def __post_init__(self):
        """ Post-processing any values, namely to turn any "Infinity"/"-Infinity" to Python numbers """
        for name, value in vars(self).items():
            if isinstance(value, str):
                setattr(self, name, parse_number(value))


@dataclass
class _Statistics(_AnalysisObject):
    count: int = 0
    mean: float = 0.0
    confidence: float = inf
    min: float = inf
    max: float = -inf
    deviation: float = 0.0


@dataclass
class StatisticsDiscrete(_Statistics):
    sum: float = 0.0


@dataclass
class StatisticsContinuous(_Statistics):
    integral: float = 0.0


@dataclass
class DataSet(_AnalysisObject):
    xmin: float = inf
    xmean: float = 0.0
    xmedian: float = 0.0
    xmax: float = -inf
    ymin: float = inf
    ymean: float = 0.0
    ymedian: float = 0.0
    ymax: float = -inf
    plainDataTable: list[list[float]] = field(default_factory=list)

    @property
    def x_values(self) -> list[float]:
        return [row[0] for row in self.plainDataTable]

    @property
    def y_values(self) -> list[float]:
        return [row[1] for row in self.plainDataTable]


@dataclass
class HistogramSmartData(_AnalysisObject):
    count: int = 0
    lowerBound: float = 0.0
    intervalWidth: float = 0.1
    hits: list[int] = field(default_factory=list)
    statistics: _Statistics = field(default_factory=_Statistics)

    def __post_init__(self):
        super().__post_init__()
        # given statistics may initially be passed as a dict; convert to the correct type
        if isinstance(self.statistics, dict):
            self.statistics = _Statistics(**self.statistics)


@dataclass
class HistogramSimpleData(HistogramSmartData):
    hitsOutLow: float = 0.0
    hitsOutHigh: float = 0.0


@dataclass
class Histogram2DData(_AnalysisObject):
    hits: list[list[int]] = field(default_factory=list)
    hitsOutLow: list[int] = field(default_factory=list)
    hitsOutHigh: list[int] = field(default_factory=list)
    xMin: float = inf
    xMax: float = -inf
    yMin: float = inf
    yMax: float = -inf


_BaseUnitAttrs = namedtuple('BaseUnitAttrs', ['symbol'])
"""Baseline named tuple, inherited by the others with a similar name; all enums have a 'symbol' attribute describing the string label for the unit"""

_NumericUnitAttrs = extended_namedtuple('NumericUnitAttrs', ['conversion_factor', _BaseUnitAttrs])
"""Named tuple used to describe units with only a numeric attribute; used by units describing Amount, Time, Length, and Angle"""

_SpaceUnitAttrs = extended_namedtuple('SpaceUnitAttrs', ['length_unit', _BaseUnitAttrs])  # area
"""Named tuple used to describe units with a length component; used by AreaUnits"""

_RateUnitAttrs = extended_namedtuple('RateUnitAttrs', ['time_unit', _BaseUnitAttrs])  # rate
"""Named tuple used to describe units with a time component; used by RateUnits"""

_VelocityUnitAttrs = extended_namedtuple('VelocityUnitAttrs',
                                         ['spacial_unit', _RateUnitAttrs])  # accel, speed, flow, rotation speed
"""Named tuple used to describe units with time and spacial components; used by units describing Acceleration, Speed, Flow, and RotationSpeed"""


class _UnitEnum(Enum):
    """Abstract, base class inherited by other unit classes"""

    def __init__(self, symbol=None):
        self.symbol = symbol or "?"

    @abstractmethod
    def modifier(self, units: '_UnitEnum') -> float:
        raise NotImplementedError()

    @abstractmethod
    def convert_to(self, this_amount: float, new_units: '_UnitEnum') -> float:
        raise NotImplementedError()


class AmountUnits(_UnitEnum):
    LITER = _NumericUnitAttrs(0.001, 'L')
    OIL_BARREL = _NumericUnitAttrs(0.158987295, 'barrels')
    CUBIC_METER = _NumericUnitAttrs(1.0, 'm3')
    KILOGRAM = _NumericUnitAttrs(1.0, 'kg')
    TON = _NumericUnitAttrs(1000.0, 'ton')

    def __init__(self, conversion_factor, symbol):
        super().__init__(symbol)
        self.conversion_factor = conversion_factor

    def modifier(self, units: 'AmountUnits') -> float:
        return self.conversion_factor / units.conversion_factor

    def convert_to(self, this_amount: float, new_units: 'AmountUnits') -> float:
        return this_amount * self.modifier(new_units)


class TimeUnits(_UnitEnum):
    MILLISECOND = _NumericUnitAttrs(0.001, "ms")
    SECOND = _NumericUnitAttrs(1.0, "sec")
    MINUTE = _NumericUnitAttrs(60.0, "min")
    HOUR = _NumericUnitAttrs(3600.0, "hr")
    DAY = _NumericUnitAttrs(86400.0, "day")
    WEEK = _NumericUnitAttrs(604800.0, "wk")
    MONTH = _NumericUnitAttrs(2592000.0, "mn")
    YEAR = _NumericUnitAttrs(3.1536E7, "yr")

    def __init__(self, conversion_factor, symbol):
        super().__init__(symbol)
        self.conversion_factor = conversion_factor

    def modifier(self, units: 'TimeUnits') -> float:
        return self.conversion_factor / units.conversion_factor

    def convert_to(self, this_amount: float, new_units: 'TimeUnits') -> float:
        return this_amount * self.modifier(new_units)


class LengthUnits(_UnitEnum):
    MILLIMETER = _NumericUnitAttrs(0.001, "mm")
    CENTIMETER = _NumericUnitAttrs(0.01, "cm")
    METER = _NumericUnitAttrs(1.0, "m")
    KILOMETER = _NumericUnitAttrs(1000.0, "km")
    INCH = _NumericUnitAttrs(0.0254, "in")
    FOOT = _NumericUnitAttrs(0.3048, "ft")
    YARD = _NumericUnitAttrs(0.9144, "yd")
    MILE = _NumericUnitAttrs(1609.344, "m")
    NAUTICAL_MILE = _NumericUnitAttrs(1853.184, "nm")

    def __init__(self, conversion_factor, symbol):
        super().__init__(symbol)
        self.conversion_factor = conversion_factor

    def modifier(self, units: 'LengthUnits') -> float:
        return self.conversion_factor / units.conversion_factor

    def convert_to(self, this_amount: float, new_units: 'LengthUnits') -> float:
        return this_amount * self.modifier(new_units)


class AngleUnits(_UnitEnum):
    TURN = _NumericUnitAttrs(6.283185307179586, 'turn')
    RADIAN = _NumericUnitAttrs(1.0, 'rad')
    DEGREE = _NumericUnitAttrs(0.017453292519943295, 'deg')

    def __init__(self, conversion_factor, symbol):
        super().__init__(symbol)
        self.conversion_factor = conversion_factor

    def modifier(self, units: 'AngleUnits') -> float:
        return self.conversion_factor / units.conversion_factor

    def convert_to(self, this_amount: float, new_units: 'AngleUnits') -> float:
        return this_amount * self.modifier(new_units)


class AreaUnits(_UnitEnum):
    SQ_MILLIMETER = _SpaceUnitAttrs(LengthUnits.MILLIMETER, "mm2")
    SQ_CENTIMETER = _SpaceUnitAttrs(LengthUnits.CENTIMETER, "cm2")
    SQ_METER = _SpaceUnitAttrs(LengthUnits.METER, "m2")
    SQ_KILOMETER = _SpaceUnitAttrs(LengthUnits.KILOMETER, "km2")
    SQ_INCH = _SpaceUnitAttrs(LengthUnits.INCH, "in2")
    SQ_FOOT = _SpaceUnitAttrs(LengthUnits.FOOT, "ft2")
    SQ_YARD = _SpaceUnitAttrs(LengthUnits.YARD, "yard2")
    SQ_MILE = _SpaceUnitAttrs(LengthUnits.MILE, "mile2")
    SQ_NAUTICAL_MILE = _SpaceUnitAttrs(LengthUnits.NAUTICAL_MILE, "nautmile2")

    def __init__(self, length_unit: 'LengthUnits', symbol: str):
        super().__init__(symbol)
        self.si = length_unit.modifier(LengthUnits.METER) ** 2
        self.length_unit = length_unit

    def modifier(self, units: 'AreaUnits') -> float:
        return self.si / units.si

    def convert_to(self, this_amount: float, new_units: 'AreaUnits') -> float:
        return this_amount * self.modifier(new_units)


class RateUnits(_UnitEnum):
    PER_MILLISECOND = _RateUnitAttrs(TimeUnits.MILLISECOND, "per ms")
    PER_SECOND = _RateUnitAttrs(TimeUnits.SECOND, "per sec")
    PER_MINUTE = _RateUnitAttrs(TimeUnits.MINUTE, "per min")
    PER_HOUR = _RateUnitAttrs(TimeUnits.HOUR, "per hr")
    PER_DAY = _RateUnitAttrs(TimeUnits.DAY, "per day")
    PER_WEEK = _RateUnitAttrs(TimeUnits.WEEK, "per wk")
    PER_MONTH = _RateUnitAttrs(TimeUnits.MONTH, "per month")
    PER_YEAR = _RateUnitAttrs(TimeUnits.YEAR, "per year")

    def __init__(self, time_unit, symbol):
        super().__init__(symbol)
        self.time_unit = time_unit

    def modifier(self, units: 'RateUnits') -> float:
        return 1.0 / self.time_unit.modifier(units.time_unit)

    def convert_to(self, this_amount: float, new_units: 'RateUnits') -> float:
        return this_amount * self.modifier(new_units)


class AccelerationUnits(_UnitEnum):
    MPS_SQ = _VelocityUnitAttrs(LengthUnits.METER, TimeUnits.SECOND, "mps2")
    FPS_SQ = _VelocityUnitAttrs(LengthUnits.FOOT, TimeUnits.SECOND, "fps2")

    def __init__(self, length_unit, time_unit, symbol):
        super().__init__(symbol)
        self.length_unit = length_unit
        self.time_unit = time_unit

    def modifier(self, units: 'AccelerationUnits') -> float:
        d = self.time_unit.modifier(units.time_unit)
        return self.length_unit.modifier(units.length_unit) / d * d

    def convert_to(self, this_amount: float, new_units: 'AccelerationUnits') -> float:
        return this_amount * self.modifier(new_units)


class SpeedUnits(_UnitEnum):
    MPS = _VelocityUnitAttrs(LengthUnits.METER, TimeUnits.SECOND, "meters per second")
    KPH = _VelocityUnitAttrs(LengthUnits.KILOMETER, TimeUnits.HOUR, "kilometers per hour")
    FPS = _VelocityUnitAttrs(LengthUnits.FOOT, TimeUnits.SECOND, "feet per second")
    FPM = _VelocityUnitAttrs(LengthUnits.FOOT, TimeUnits.MINUTE, "feet per minute")
    MPH = _VelocityUnitAttrs(LengthUnits.MILE, TimeUnits.HOUR, "miles per hour")
    KN = _VelocityUnitAttrs(LengthUnits.NAUTICAL_MILE, TimeUnits.HOUR, "knots")

    def __init__(self, length_unit, time_unit, symbol):
        super().__init__(symbol)
        self.length_unit = length_unit
        self.time_unit = time_unit

    def modifier(self, units: 'SpeedUnits') -> float:
        return self.length_unit.modifier(units.length_unit) / self.time_unit.modifier(units.time_unit)

    def convert_to(self, this_amount: float, new_units: 'SpeedUnits') -> float:
        return this_amount * self.modifier(new_units)


class FlowRateUnits(_UnitEnum):
    LITER_PER_SECOND = _VelocityUnitAttrs(AmountUnits.LITER, TimeUnits.SECOND, "liter per second")
    OIL_BARREL_PER_SECOND = _VelocityUnitAttrs(AmountUnits.OIL_BARREL, TimeUnits.SECOND, "oil barrel per second")
    CUBIC_METER_PER_SECOND = _VelocityUnitAttrs(AmountUnits.CUBIC_METER, TimeUnits.SECOND, "meter3 per second")
    KILOGRAM_PER_SECOND = _VelocityUnitAttrs(AmountUnits.KILOGRAM, TimeUnits.SECOND, "kilogram per second")
    TON_PER_SECOND = _VelocityUnitAttrs(AmountUnits.TON, TimeUnits.SECOND, "ton per second")

    def __init__(self, amount_unit, time_unit, symbol):
        super().__init__(symbol)
        self.amount_unit = amount_unit
        self.time_unit = time_unit

    def modifier(self, units: 'FlowRateUnits') -> float:
        return self.amount_unit.modifier(units.amount_unit) / self.time_unit.modifier(units.time_unit)

    def convert_to(self, this_amount: float, new_units: 'FlowRateUnits') -> float:
        return this_amount * self.modifier(new_units)


class RotationSpeedUnits(_UnitEnum):
    RPM = _VelocityUnitAttrs(AngleUnits.TURN, TimeUnits.MINUTE, "rotations per minute")
    RAD_PER_SECOND = _VelocityUnitAttrs(AngleUnits.RADIAN, TimeUnits.SECOND, "radians per second")
    DEG_PER_SECOND = _VelocityUnitAttrs(AngleUnits.DEGREE, TimeUnits.SECOND, "degrees per second")

    def __init__(self, angle_unit, time_unit, symbol):
        super().__init__(symbol)
        self.angle_unit = angle_unit
        self.time_unit = time_unit

    def modifier(self, units: 'RotationSpeedUnits') -> float:
        return self.angle_unit.modifier(units.angle_unit) / self.time_unit.modifier(units.time_unit)

    def convert_to(self, this_amount: float, new_units: 'RotationSpeedUnits') -> float:
        return this_amount * self.modifier(new_units)


@dataclass
class UnitValue:
    """
    A custom type to represent some numerical value with units.
    """
    value: Number
    unit: _UnitEnum | str  # will get converted to correct unit during initialization

    def __str__(self):
        return f"{self.value} {self.unit.symbol}"

    def __repr__(self):
        return str(self)

    def __post_init__(self):
        # convert unit to proper type
        if isinstance(self.unit, str):
            # loop thru all unit types, finding the first with a member whose name matches `self.unit`,
            # then overwrite with the new value
            for cls in (
            AmountUnits, TimeUnits, LengthUnits, AngleUnits, AreaUnits, RateUnits, AccelerationUnits, SpeedUnits,
            FlowRateUnits, RotationSpeedUnits):
                try:
                    unit = next(filter(lambda e: e.name == self.unit, cls))
                    self.unit = unit
                    return
                except StopIteration:
                    pass
            raise AttributeError(f"Could not find correct unit-type for provided unit '{self.unit}'")

    def _check_type_and_convert(self, other):
        if isinstance(other, (int, float)):
            return other, self.unit
        if not isinstance(other, UnitValue):
            raise NotImplementedError(
                f"Can only apply an operation on a UnitValue and a number, not type {type(other)}")
        if type(self.unit) != type(other.unit):
            raise NotImplementedError(
                f"Cannot apply operation on UnitValue objects with different unit types (this={self.unit}, other={other.unit})")
        return other.unit.convert_to(other.value, self.unit), self.unit

    def _apply_operation(self, other: Number | 'UnitValue',
                         operation: Callable[[Number | 'UnitValue', Number | 'UnitValue'], Number]):
        other_value, unit = self._check_type_and_convert(other)
        new_value = operation(self.value, other_value)
        return UnitValue(new_value, unit)

    def __call__(self, *args, **kwargs) -> float:
        if len(args) != 1 or kwargs:
            raise TypeError("Call to unit value only accepts 1 argument for the new unit to convert to.")
        new_unit: _UnitEnum = args[0]
        if not isinstance(new_unit, type(self.unit)):
            raise TypeError("Argument to unit value must be of the same type as the original units")
        return self.unit.convert_to(self.value, new_unit)

    def __add__(self, other: Number | 'UnitValue'):
        return self._apply_operation(other, lambda a, b: a + b)

    def __sub__(self, other: Number | 'UnitValue'):
        return self._apply_operation(other, lambda a, b: a - b)

    def __mul__(self, other: Number | 'UnitValue'):
        return self._apply_operation(other, lambda a, b: a * b)

    def __truediv__(self, other: Number | 'UnitValue'):
        return self._apply_operation(other, lambda a, b: a / b)

    def __iadd__(self, other):
        new_uv = self.__add__(other)
        self.value = new_uv.value

    def __isub__(self, other):
        new_uv = self.__sub__(other)
        self.value = new_uv.value

    def __imul__(self, other):
        new_uv = self.__mul__(other)
        self.value = new_uv.value

    def __itruediv__(self, other):
        new_uv = self.__truediv__(other)
        self.value = new_uv.value

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __iter__(self):
        yield self.value
        yield self.unit
