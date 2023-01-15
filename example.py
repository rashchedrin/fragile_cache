import math
from time import sleep

from fragile_cache import LoudVariable, FragileCache


class Circle:
    def __init__(self, radius: float):
        self._radius = LoudVariable(radius)
        self._area_fragile = FragileCache(self.calc_area,
                                          dependencies=[self._radius],
                                          on_recall=lambda: print("recalled"))

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
    print(circle.area)  # crealculated
    assert circle.area > 0  # recalled
    assert abs(circle.area - 706.8583470577034) < 1e-3  # recalled


if __name__ == "__main__":
    main()
