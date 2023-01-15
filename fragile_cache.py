from typing import List, Callable, TypeVar, Generic, Any

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
