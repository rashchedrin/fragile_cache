import math
from time import sleep

from fragile_cache import LoudVariable, FragileCache


class Circle:
    def __init__(self, radius: float):
        # LoudVariable is a wrapper, that allows attachment of callbacks
        # on events of value reassignment and access. This is necessary to
        # invoke cache invalidation on change
        self._radius = LoudVariable(radius)
        # FragileCache is a class that can be called just like a function,
        # but also keeps the cached value. Cached value will be invalidated if
        # any of the variables in list of dependencies will change.
        # on_recall event is added for illustration.
        self._area_fragile = FragileCache(self.calc_area,
                                          dependencies=[self._radius],
                                          on_recall=lambda: print("recalled"))

    # Although this is not necessary, declaring radius as a property allows to
    # use it in code just like a normal variable.
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
        sleep(0.5)
        return math.pi * self.radius ** 2


def main() -> None:
    circle = Circle(10)
    print(circle.area)  # calculated
    assert circle.area > 0  # recalled
    assert abs(circle.area - 314.1592653589793) < 1e-3  # recalled
    circle.radius = 15
    print(circle.area)  # recalculated
    assert circle.area > 0  # recalled
    assert abs(circle.area - 706.8583470577034) < 1e-3  # recalled


if __name__ == "__main__":
    main()
