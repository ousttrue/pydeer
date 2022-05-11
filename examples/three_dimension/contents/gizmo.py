'''
simple triangle sample
'''
import logging
import math
import glm
from pydear.utils.selector import Item
from pydear.scene.camera import Camera, MouseEvent
from pydear.gizmo.gizmo import Gizmo, CubeShape, RingShape

LOGGER = logging.getLogger(__name__)


class GizmoScene(Item):
    def __init__(self, mouse_event: MouseEvent) -> None:
        super().__init__('gizmo')
        self.camera = Camera()
        self.mouse_event = mouse_event
        self.camera.bind_mouse_event(self.mouse_event)
        self.gizmo = Gizmo()
        self.gizmo.bind_mouse_event(self.mouse_event)

        # selectable
        for i in range(-2, 3, 1):
            for j in range(-2, 3, 1):
                cube = CubeShape(0.5, 0.5, 0.5,
                                 position=glm.vec3(i, j, 0))
                key = self.gizmo.add_shape(cube)
                # LOGGER.debug(f'{i}, {j} => {key}')

        # draggable
        ring = RingShape(math.pi * 2, 0.4, 0.5, color=glm.vec4(0.3, 1, 1, 1))
        self.gizmo.add_shape(ring, draggable=True)

    def render(self, w, h):
        self.camera.projection.resize(w, h)
        input = self.mouse_event.last_input
        assert(input)
        self.gizmo.process(self.camera, input.x, input.y)

    def show(self):
        pass
