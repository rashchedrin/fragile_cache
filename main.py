import math
from collections import defaultdict
from functools import wraps
from typing import List, Callable, TypeVar, Generic, Any, Dict

ValueType = TypeVar('ValueType')


class LoudVariable(Generic[ValueType]):
    def __init__(self, value: ValueType):
        self._value: ValueType = value
        self._setter_callbacks: List[Callable[[ValueType], None]] = []
        self._getter_callbacks: List[Callable[[ValueType], None]] = []

    @property
    def value(self) -> ValueType:
        for callback in self._getter_callbacks:
            callback(self._value)
        return self._value

    @value.setter
    def value(self, new_value: ValueType) -> None:
        for callback in self._setter_callbacks:
            callback(new_value)
        self._value = new_value

    @property
    def value_attr(self) -> ValueType:
        return getattr(self, "value")

    def add_setter_callback(self,
                            callback: Callable[[ValueType], None]) -> None:
        self._setter_callbacks.append(callback)

    def add_getter_callback(self,
                            callback: Callable[[ValueType], None]) -> None:
        self._getter_callbacks.append(callback)


ResultType = TypeVar('ResultType')


def make_fragile(func: Callable[..., ResultType],
                 dependencies: List[LoudVariable[ValueType]]) \
        -> Callable[..., ResultType]:
    result_is_calculated = False
    cached_result: ResultType

    @wraps(func)
    def return_cached_result_or_calculate(*args: Any,
                                          **kwargs: Any) -> ResultType:
        nonlocal cached_result
        nonlocal result_is_calculated
        if not result_is_calculated:
            cached_result = func(*args, **kwargs)
            result_is_calculated = True
        else:
            print("cache used")
        return cached_result

    def invalidate_cached_result(_: Any) -> None:
        nonlocal result_is_calculated
        result_is_calculated = False

    for dependency in dependencies:
        dependency.add_setter_callback(invalidate_cached_result)
    return return_cached_result_or_calculate


def nop(*args: Any, **kwargs: Any) -> None:
    pass


class FragileCache(Generic[ResultType]):
    def __init__(self,
                 func: Callable[..., ResultType],
                 dependencies: List[LoudVariable[Any]],
                 on_recall: Callable[[], None] = nop,
                 on_calculation: Callable[[], None] = nop,
                 on_invalidation: Callable[[], None] = nop):
        self.is_calculated = False
        self.cached_result: ResultType
        self._func = func
        self.on_recall = on_recall
        self.on_calculation = on_calculation
        self.on_invalidation = on_invalidation
        for dependency in dependencies:
            dependency.add_setter_callback(self.invalidate)

    def invalidate(self, _: Any) -> None:
        self.is_calculated = False
        self.on_invalidation()

    def __call__(self, *args: Any, **kwargs: Any) -> ResultType:
        if not self.is_calculated:
            self.on_calculation()
            self.cached_result = self._func(*args, **kwargs)
            self.is_calculated = True
        else:
            self.on_recall()
        return self.cached_result


class CountCalls:
    def __init__(self) -> None:
        self.n_called = 0

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.n_called += 1


class Circle:
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


def main() -> None:
    test()


def test() -> None:
    recalculations: Dict[Circle, int] = defaultdict(int)
    recalls: Dict[Circle, int] = defaultdict(int)
    invalidations: Dict[Circle, int] = defaultdict(int)

    def counters_in_sync(circle: Circle) -> bool:
        return circle.count_recalculations.n_called == recalculations[circle] \
               and circle.count_recalls.n_called == recalls[circle] \
               and circle.count_invalidations.n_called == invalidations[circle]

    def register_recalculation(circle: Circle) -> None:
        recalculations[circle] += 1

    def register_recall(circle: Circle) -> None:
        recalls[circle] += 1

    def register_invalidation(circle: Circle) -> None:
        invalidations[circle] += 1

    circle_first = Circle(10)
    assert counters_in_sync(circle_first)

    circle_second = Circle(15)
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


if __name__ == '__main__':
    main()
