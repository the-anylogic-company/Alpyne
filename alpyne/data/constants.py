import logging
from abc import abstractmethod
from collections import namedtuple
from datetime import datetime
from enum import Enum, Flag, auto
from typing import Any, Type, Union, Optional, Literal, TypeVar, Generic

#from alpyne.client.utils import extended_namedtuple  # causes circular dep errors when present
def extended_namedtuple(name, source_fields):
    assert isinstance(source_fields, list)
    new_type_fields = []
    for f in source_fields:
        try:
            new_type_fields.extend(f._fields)
        except:
            new_type_fields.append(f)
    return namedtuple(name, new_type_fields)

class PyLogLevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG


class JavaLogLevel(Enum):
    SEVERE = "SEVERE"
    WARNING = "WARNING"
    INFO = "INFO"
    CONFIG = "CONFIG"
    FINE = "FINE"
    FINER = "FINER"
    FINEST = "FINEST"


# v- falsely claims `auto()` is incorrect; may fix with a hard refresh TODO
# noinspection PyArgumentList
class State(Flag):
    """
    Represents the state of the run's engine.

    In general, the engine can be considered either waiting for some type of user-input, actively processing, or
    in a halted state (which may or may not be recoverable). The various statuses divide these three categories
    into subcategories, to provide more useful context.
    """
    IDLE = auto()
    """ Just started, waiting for the configuration """

    PAUSED = auto()
    """ Mid-run, waiting for action and open to observation and output querying """

    RUNNING = auto()
    """ The model is being actively executed """

    FINISHED = auto()
    """ The model execution is finished successfully  """

    ERROR = auto()
    """ Internal model error """

    PLEASE_WAIT = auto()
    """ In the process of executing an uninterruptible command (`pause()`, `stop()`, `step()`) """

    @classmethod
    def ANY(cls):
        return ~cls(0)

    @staticmethod
    def to_flag(name: str) -> 'State':
        return State.__members__.get(name, State(0))


BaseUnitAttrs = namedtuple('BaseUnitAttrs', ['symbol'])
NumericUnitAttrs = extended_namedtuple('NumericUnitAttrs', ['conversion_factor', BaseUnitAttrs])
SpaceUnitAttrs = extended_namedtuple('SpaceUnitAttrs', ['length_unit', BaseUnitAttrs])  # area
RateUnitAttrs = extended_namedtuple('RateUnitAttrs', ['time_unit', BaseUnitAttrs])  # rate
VelocityUnitAttrs = extended_namedtuple('VelocityUnitAttrs', ['spacial_unit', RateUnitAttrs])  # accel, speed, flow, rotation speed


class IEnum(Enum):

    @abstractmethod
    def modifier(self, units: 'IEnum') -> float:
        raise NotImplementedError()

    @abstractmethod
    def convertTo(self, this_amount: float, new_units: 'IEnum') -> float:
        raise NotImplementedError()


class AmountUnits(IEnum):
    LITER = NumericUnitAttrs(0.001, 'L')
    OIL_BARREL = NumericUnitAttrs(0.158987295, 'barrels')
    CUBIC_METER = NumericUnitAttrs(1.0, 'm3')
    KILOGRAM = NumericUnitAttrs(1.0, 'kg')
    TON = NumericUnitAttrs(1000.0, 'ton')

    def __init__(self, conversion_factor, symbol):
        self.conversion_factor = conversion_factor
        self.symbol = symbol

    def modifier(self, units: 'AmountUnits') -> float:
        return self.conversion_factor / units.conversion_factor

    def convertTo(self, this_amount: float, new_units: 'AmountUnits') -> float:
        return this_amount * self.modifier(new_units)


class TimeUnits(IEnum):
    MILLISECOND = NumericUnitAttrs(0.001, "ms")
    SECOND = NumericUnitAttrs(1.0, "sec")
    MINUTE = NumericUnitAttrs(60.0, "min")
    HOUR = NumericUnitAttrs(3600.0, "hr")
    DAY = NumericUnitAttrs(86400.0, "day")
    WEEK = NumericUnitAttrs(604800.0, "wk")
    MONTH = NumericUnitAttrs(2592000.0, "mn")
    YEAR = NumericUnitAttrs(3.1536E7, "yr")

    def __init__(self, conversion_factor, symbol):
        self.conversion_factor = conversion_factor
        self.symbol = symbol

    def modifier(self, units: 'TimeUnits') -> float:
        return self.conversion_factor / units.conversion_factor

    def convertTo(self, this_amount: float, new_units: 'TimeUnits') -> float:
        return this_amount * self.modifier(new_units)


class LengthUnits(IEnum):
    MILLIMETER = NumericUnitAttrs(0.001, "mm")
    CENTIMETER = NumericUnitAttrs(0.01, "cm")
    METER = NumericUnitAttrs(1.0, "m")
    KILOMETER = NumericUnitAttrs(1000.0, "km")
    INCH = NumericUnitAttrs(0.0254, "in")
    FOOT = NumericUnitAttrs(0.3048, "ft")
    YARD = NumericUnitAttrs(0.9144, "yd")
    MILE = NumericUnitAttrs(1609.344, "m")
    NAUTICAL_MILE = NumericUnitAttrs(1853.184, "nm")

    def __init__(self, conversion_factor, symbol):
        self.conversion_factor = conversion_factor
        self.symbol = symbol

    def modifier(self, units: 'LengthUnits') -> float:
        return self.conversion_factor / units.conversion_factor

    def convertTo(self, this_amount: float, new_units: 'LengthUnits') -> float:
        return this_amount * self.modifier(new_units)


class AngleUnits(IEnum):
    TURN = NumericUnitAttrs(6.283185307179586, 'turn')
    RADIAN = NumericUnitAttrs(1.0, 'rad')
    DEGREE = NumericUnitAttrs(0.017453292519943295, 'deg')

    def __init__(self, conversion_factor, symbol):
        self.conversion_factor = conversion_factor
        self.symbol = symbol

    def modifier(self, units: 'AngleUnits') -> float:
        return self.conversion_factor / units.conversion_factor

    def convertTo(self, this_amount: float, new_units: 'AngleUnits') -> float:
        return this_amount * self.modifier(new_units)


class RateUnits(IEnum):
    PER_MILLISECOND = RateUnitAttrs(TimeUnits.MILLISECOND, "per ms")
    PER_SECOND = RateUnitAttrs(TimeUnits.SECOND, "per sec")
    PER_MINUTE = RateUnitAttrs(TimeUnits.MINUTE, "per min")
    PER_HOUR = RateUnitAttrs(TimeUnits.HOUR, "per hr")
    PER_DAY = RateUnitAttrs(TimeUnits.DAY, "per day")
    PER_WEEK = RateUnitAttrs(TimeUnits.WEEK, "per wk")
    PER_MONTH = RateUnitAttrs(TimeUnits.MONTH, "per month")
    PER_YEAR = RateUnitAttrs(TimeUnits.YEAR, "per year")

    def __init__(self, time_unit, symbol):
        self.time_unit = time_unit
        self.symbol = symbol

    def modifier(self, units: 'RateUnits') -> float:
        return 1.0 / self.time_unit.modifier(units.time_unit)

    def convertTo(self, this_amount: float, new_units: 'RateUnits') -> float:
        return this_amount * self.modifier(new_units)


class AccelerationUnits(IEnum):
    MPS_SQ = VelocityUnitAttrs(LengthUnits.METER, TimeUnits.SECOND, "mps2")
    FPS_SQ = VelocityUnitAttrs(LengthUnits.FOOT, TimeUnits.SECOND, "fps2")

    def __init__(self, length_unit, time_unit, symbol):
        self.length_unit = length_unit
        self.time_unit = time_unit
        self.symbol = symbol

    def modifier(self, units: 'AccelerationUnits') -> float:
        d = self.time_unit.modifier(units.time_unit)
        return self.length_unit.modifier(units.length_unit) / d * d

    def convertTo(self, this_amount: float, new_units: 'AccelerationUnits') -> float:
        return this_amount * self.modifier(new_units)


class SpeedUnits(IEnum):
    MPS = VelocityUnitAttrs(LengthUnits.METER, TimeUnits.SECOND, "meters per second")
    KPH = VelocityUnitAttrs(LengthUnits.KILOMETER, TimeUnits.HOUR, "kilometers per hour")
    FPS = VelocityUnitAttrs(LengthUnits.FOOT, TimeUnits.SECOND, "feet per second")
    FPM = VelocityUnitAttrs(LengthUnits.FOOT, TimeUnits.MINUTE, "feet per minute")
    MPH = VelocityUnitAttrs(LengthUnits.MILE, TimeUnits.HOUR, "miles per hour")
    KN = VelocityUnitAttrs(LengthUnits.NAUTICAL_MILE, TimeUnits.HOUR, "knots")

    def __init__(self, length_unit, time_unit, symbol):
        self.length_unit = length_unit
        self.time_unit = time_unit
        self.symbol = symbol

    def modifier(self, units: 'SpeedUnits') -> float:
        return self.length_unit.modifier(units.length_unit) / self.time_unit.modifier(units.time_unit)

    def convertTo(self, this_amount: float, new_units: 'SpeedUnits') -> float:
        return this_amount * self.modifier(new_units)


class FlowRateUnits(IEnum):
    LITER_PER_SECOND = VelocityUnitAttrs(AmountUnits.LITER, TimeUnits.SECOND, "liter per second")
    OIL_BARREL_PER_SECOND = VelocityUnitAttrs(AmountUnits.OIL_BARREL, TimeUnits.SECOND, "oil barrel per second")
    CUBIC_METER_PER_SECOND = VelocityUnitAttrs(AmountUnits.CUBIC_METER, TimeUnits.SECOND, "meter3 per second")
    KILOGRAM_PER_SECOND = VelocityUnitAttrs(AmountUnits.KILOGRAM, TimeUnits.SECOND, "kilogram per second")
    TON_PER_SECOND = VelocityUnitAttrs(AmountUnits.TON, TimeUnits.SECOND, "ton per second")

    def __init__(self, amount_unit, time_unit, symbol):
        self.amount_unit = amount_unit
        self.time_unit = time_unit
        self.symbol = symbol

    def modifier(self, units: 'FlowRateUnits') -> float:
        return self.amount_unit.modifier(units.amount_unit) / self.time_unit.modifier(units.time_unit)

    def convertTo(self, this_amount: float, new_units: 'FlowRateUnits') -> float:
        return this_amount * self.modifier(new_units)


class RotationSpeedUnits(IEnum):
    RPM = VelocityUnitAttrs(AngleUnits.TURN, TimeUnits.MINUTE, "rotations per minute")
    RAD_PER_SECOND = VelocityUnitAttrs(AngleUnits.RADIAN, TimeUnits.SECOND, "radians per second")
    DEG_PER_SECOND = VelocityUnitAttrs(AngleUnits.DEGREE, TimeUnits.SECOND, "degrees per second")

    def __init__(self, angle_unit, time_unit, symbol):
        self.angle_unit = angle_unit
        self.time_unit = time_unit
        self.symbol = symbol

    def modifier(self, units: 'RotationSpeedUnits') -> float:
        return self.angle_unit.modifier(units.angle_unit) / self.time_unit.modifier(units.time_unit)

    def convertTo(self, this_amount: float, new_units: 'RotationSpeedUnits') -> float:
        return this_amount * self.modifier(new_units)
