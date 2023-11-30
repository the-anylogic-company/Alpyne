from collections import namedtuple
from typing import Union
from math import inf

from alpyne.data.model_data import Number


def parse_number(value: Union[Number, str]) -> Number:
    if isinstance(value, str):
        if value == 'Infinity':
            return inf
        elif value == '-Infinity':
            return -inf
        else:
            raise ValueError(f"Unrecognized number type: {value}")
    return value


_StatisticsBase = namedtuple("Statistics", "count mean min max deviation confidence sum")
_StatisticsDiscreteBase = namedtuple("StatisticsDiscrete", "count mean min max deviation confidence sum")
_StatisticsContinuousBase = namedtuple("StatisticsContinuous", "count mean min max deviation confidence integral")
_DataSetBase = namedtuple("DataSet", "xmin xmean xmedian xmax ymin ymean ymedian ymax plainDataTable")
_HistogramSmartDataBase = namedtuple("HistogramSmartData", "count lowerBound intervalWidth hits statistics")
_Histogram2DDataBase = namedtuple("Histogram2DData", "hits hitsOutLow hitsOutHigh xMin xMax yMin yMax")


class Statistics(_StatisticsBase):
    def __new__(cls, count, mean, min, max, deviation):
        min = parse_number(min)
        max = parse_number(max)
        return super(Statistics, cls).__new__(cls, count, mean, min, max, deviation)


class StatisticsDiscrete(_StatisticsDiscreteBase):
    def __new__(cls, count, mean, min, max, deviation, confidence, sum):
        min = parse_number(min)
        max = parse_number(max)
        confidence = parse_number(confidence)
        return super(StatisticsDiscrete, cls).__new__(cls, count, mean, min, max, deviation, confidence, sum)


class StatisticsContinuous(_StatisticsContinuousBase):
    def __new__(cls, count, mean, min, max, deviation, confidence, integral):
        min = parse_number(min)
        max = parse_number(max)
        confidence = parse_number(confidence)
        return super(StatisticsContinuous, cls).__new__(cls, count, mean, min, max, deviation, confidence, integral)


class DataSet(_DataSetBase):
    def __new__(cls, xmin, xmean, xmedian, xmax, ymin, ymean, ymedian, ymax, plainDataTable):
        xmin = parse_number(xmin)
        xmax = parse_number(xmax)
        ymin = parse_number(ymin)
        ymax = parse_number(ymax)
        return super(DataSet, cls).__new__(cls, xmin, xmean, xmedian, xmax, ymin, ymean, ymedian, ymax, plainDataTable)


class HistogramSmartData(_HistogramSmartDataBase):
    def __new__(cls, count, lowerBound, intervalWidth, hits, statistics):
        statistics = Statistics(**statistics)
        return super(HistogramSmartData, cls).__new__(cls, count, lowerBound, intervalWidth, hits, statistics)


class Histogram2DData(_Histogram2DDataBase):
    def __new__(cls, hits, hitsOutLow, hitsOutHigh, xMin, xMax, yMin, yMax):
        return super(Histogram2DData, cls).__new__(cls, hits, hitsOutLow, hitsOutHigh, xMin, xMax, yMin, yMax)


class UnitValue:
    def __init__(self, value: Number, units: str):
        self.value = value
        self.units = units

