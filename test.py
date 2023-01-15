import math
from collections import defaultdict
from typing import Dict, Any

from fragile_cache import LoudVariable, FragileCache


def test() -> None:
    recalculations: Dict[CircleTestExample, int] = defaultdict(int)
    recalls: Dict[CircleTestExample, int] = defaultdict(int)
    invalidations: Dict[CircleTestExample, int] = defaultdict(int)

    def counters_in_sync(circle: CircleTestExample) -> bool:
        return circle.count_recalculations.n_called == recalculations[circle] \
               and circle.count_recalls.n_called == recalls[circle] \
               and circle.count_invalidations.n_called == invalidations[circle]

    def register_recalculation(circle: CircleTestExample) -> None:
        recalculations[circle] += 1

    def register_recall(circle: CircleTestExample) -> None:
        recalls[circle] += 1

    def register_invalidation(circle: CircleTestExample) -> None:
        invalidations[circle] += 1

    circle_first = CircleTestExample(10)
    assert counters_in_sync(circle_first)

    circle_second = CircleTestExample(15)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    print(circle_first.area)
    register_recalculation(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    print(circle_second.area)
    register_recalculation(circle_second)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    assert abs(circle_first.area - 314.1592653589793) < 0.0001
    register_recall(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    assert circle_first.area > 0
    register_recall(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    circle_first.radius = 20
    register_invalidation(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    print(circle_first.area)
    register_recalculation(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    assert abs(circle_first.area - 1256.6370614359173) < 0.0001
    register_recall(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    assert circle_first.area > 0
    register_recall(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    circle_first.radius = 21
    register_invalidation(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    assert abs(circle_first.area - math.pi * 21 ** 2) < 0.0001
    register_recalculation(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)

    print(circle_first.area)
    register_recall(circle_first)
    assert counters_in_sync(circle_first)
    assert counters_in_sync(circle_second)


class CircleTestExample:
    def __init__(self, radius: float):
        self._radius = LoudVariable(radius)
        self.count_invalidations = CountCalls()
        self.count_recalls = CountCalls()
        self.count_recalculations = CountCalls()
        self._area_fragile = \
            FragileCache(self.calc_area,
                         [self._radius],
                         on_recall=self.count_recalls,
                         on_calculation=self.count_recalculations,
                         on_invalidation=self.count_invalidations)

    @property
    def radius(self) -> float:
        return self._radius.value

    @radius.setter
    def radius(self, new_value: float) -> None:
        self._radius.value = new_value

    @property
    def area(self) -> float:
        return self._area_fragile("calculating circle area")

    def calc_area(self,
                  text: str = "Calculating area, please wait...") -> float:
        print(text)
        return math.pi * self.radius ** 2


class CountCalls:
    def __init__(self) -> None:
        self.n_called = 0

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.n_called += 1
