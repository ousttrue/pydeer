from typing import Optional, NamedTuple
import ctypes
import dataclasses
import logging
logger = logging.getLogger(__name__)


class Rect(NamedTuple):
    left: float
    top: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def bottom(self) -> float:
        return self.top - self.height

    def __contains__(self, other: 'Rect') -> bool:
        if self.right <= other.left:
            return False
        if other.right <= self.left:
            return False
        if self.top <= other.bottom:
            return False
        if other.top <= self.bottom:
            return False
        return True


class Tile(NamedTuple):
    z: int
    x: int
    y: int

    @property
    def rect(self) -> Rect:
        count = pow(2, self.z)
        # longitude 360
        x_unit = 360 / count
        l = -180 + self.x * x_unit
        # latitude 180
        y_unit = 180 / count
        t = 90 - self.y * y_unit
        return Rect(l, t, x_unit, y_unit)


MIN_HEIGHT_LATITUDE = 0.05


@dataclasses.dataclass
class View:
    longitude: float = 0  # -180 + 180
    latitude: float = 0  # -90 ~ +90
    height_latitude: float = 180
    aspect_ratio: float = 1

    def __str__(self) -> str:
        return f'{self.longitude:.2f}: {self.latitude:.2f} ({self.height_latitude}) {self.aspect_ratio}'

    @property
    def rect(self) -> Rect:
        height = self.height_latitude
        width = height * self.aspect_ratio * 2
        return Rect(self.longitude-width/2, self.latitude+height/2, width, height)

    def get_matrix(self):

        import glm
        x = self.longitude
        y = self.latitude
        h = self.height_latitude/2
        w = h * self.aspect_ratio*2
        return glm.ortho(
            x-w, x+w,
            y-h, y+h,
            0, 1)

    def wheel(self, d):
        if d < 0:
            self.height_latitude *= 1.1
            if self.height_latitude > 180:
                self.height_latitude = 180
        elif d > 0:
            self.height_latitude *= 0.9
            if self.height_latitude < MIN_HEIGHT_LATITUDE:
                self.height_latitude = MIN_HEIGHT_LATITUDE

    def drag(self, screen_height: int, dx: int, dy: int):
        self.latitude += self.height_latitude * float(dy) / screen_height
        self.longitude -= 2 * self.height_latitude * float(dx) / screen_height


MAX_LEVEL = 4


class Map:
    def __init__(self, zoom_level=0) -> None:
        self.zoom_level = (ctypes.c_int32 * 1)(2)
        self.view = View()

    def __str__(self) -> str:
        return f'zoom level: {self.zoom_level}, {self.view}'

    @property
    def count(self) -> int:
        return pow(2, self.zoom_level[0])

    def iter_visible(self):
        count = self.count
        view_rect = self.view.rect
        for x in range(count):
            for y in range(count):
                tile = Tile(self.zoom_level[0], x, y)
                if tile.rect in view_rect:
                    yield tile
