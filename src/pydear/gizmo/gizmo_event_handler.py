from typing import Optional
import abc
from enum import Enum, auto
import glm
from pydear.utils.eventproperty import EventProperty
from pydear.utils.mouse_event import MouseEvent
from pydear.scene.camera import Camera
from .shapes.shape import Shape, ShapeState
from .gizmo import Gizmo, RayHit

IDENTITY = glm.mat4()


class Axis(Enum):
    X = 0
    Y = 1
    Z = 2


class GizmoEventHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def drag_begin(self, hit: RayHit):
        pass

    @abc.abstractmethod
    def drag(self, x, y, dx, dy):
        pass

    @abc.abstractmethod
    def drag_end(self, x, y):
        pass

    def bind_mouse_event_with_gizmo(self, mouse_event: MouseEvent, gizmo: Gizmo):
        def drag_begin(x, y):
            self.drag_begin(gizmo.hit)
        mouse_event.left_pressed.append(drag_begin)
        mouse_event.left_drag.append(self.drag)
        mouse_event.left_released.append(self.drag_end)


class GizmoSelectHandler(GizmoEventHandler):
    def __init__(self) -> None:
        self.selected = EventProperty[Optional[Shape]](None)

    def drag_begin(self, hit: RayHit):
        self.select(hit)

    def drag(self, x, y, dx, dy):
        pass

    def drag_end(self, x, y):
        pass

    def select(self, hit: RayHit):
        shape = hit.shape
        if shape != self.selected.value:
            # clear
            if self.selected.value:
                self.selected.value.remove_state(ShapeState.SELECT)
            # select
            self.selected.set(shape)
            if shape:
                shape.add_state(ShapeState.SELECT)


class DragContext:
    def __init__(self, start_screen_pos: glm.vec2, *, manipulator: Shape, axis: Axis, target: Shape):
        self.start_screen_pos = start_screen_pos
        assert(manipulator)
        self.manipulator = manipulator
        self.manipulator.add_state(ShapeState.DRAG)
        self.axis = axis
        assert target
        self.target = target
        self.init_matrix = target.matrix.value

    def drag(self, cursor_pos: glm.vec2, camera: Camera):
        # p = Plane(self.init_matrix[self.axis].xyz, self.init_matrix[3].xyz).project()
        # hit_center = glm.vec3(self.center_screen_pos -
        #                       self.start_screen_pos, 0)
        # hit_cursor = glm.vec3(cursor_pos-self.start_screen_pos, 0)
        # n = glm.cross(hit_center, hit_cursor)
        # plus_minus = 1 if n.z > 0 else -1
        # d = glm.length(self.start_screen_pos - cursor_pos)
        d = cursor_pos.y - self.start_screen_pos.y
        angle = d * 0.02

        m = self.init_matrix * glm.rotate(angle, IDENTITY[self.axis.value].xyz)
        self.target.matrix.set(m)
        return m

    def end(self):
        self.manipulator.remove_state(ShapeState.DRAG)
        self.manipulator = None


class DragEventHandler(GizmoEventHandler):
    def __init__(self, gizmo: Gizmo, camera) -> None:
        super().__init__()
        self.camera = camera
        self.selected = EventProperty[Optional[Shape]](None)

        # draggable
        from pydear.gizmo.shapes.ring_shape import XRingShape, YRingShape, ZRingShape
        self.x_ring = XRingShape(inner=0.4, outer=0.6, depth=0.02,
                                 color=glm.vec4(1, 0.3, 0.3, 1))
        gizmo.add_shape(self.x_ring)
        self.y_ring = YRingShape(inner=0.4, outer=0.6, depth=0.02,
                                 color=glm.vec4(0.3, 1, 0.3, 1))
        gizmo.add_shape(self.y_ring)
        self.z_ring = ZRingShape(inner=0.4, outer=0.6, depth=0.02,
                                 color=glm.vec4(0.3, 0.3, 1, 1))
        gizmo.add_shape(self.z_ring)

        self.context = None

    def drag_begin(self, hit: RayHit):
        match hit.shape:
            case self.x_ring:
                # ring is not selectable
                self.context = DragContext(
                    hit.cursor_pos, manipulator=hit.shape, axis=Axis.X,
                    target=self.selected.value)
            case self.y_ring:
                # ring is not selectable
                self.context = DragContext(
                    hit.cursor_pos, manipulator=hit.shape, axis=Axis.Y,
                    target=self.selected.value)
            case self.z_ring:
                # ring is not selectable
                self.context = DragContext(
                    hit.cursor_pos, manipulator=hit.shape, axis=Axis.Z,
                    target=self.selected.value)
            case _:
                self.select(hit)

    def drag(self, x, y, dx, dy):
        if self.context:
            m = self.context.drag(glm.vec2(x, y), self.camera)
            self.x_ring.matrix.set(m)
            self.y_ring.matrix.set(m)
            self.z_ring.matrix.set(m)

    def drag_end(self, x, y):
        if self.context:
            self.context.end()
            self.context = None

    def select(self, hit: RayHit):
        shape = hit.shape
        if shape != self.selected.value:
            # clear
            if self.selected.value:
                self.selected.value.remove_state(ShapeState.SELECT)
            # select
            self.selected.set(shape)
            if shape:
                shape.add_state(ShapeState.SELECT)
                self.x_ring.matrix.set(shape.matrix.value)
                self.x_ring.remove_state(ShapeState.HIDE)
                self.y_ring.matrix.set(shape.matrix.value)
                self.y_ring.remove_state(ShapeState.HIDE)
                self.z_ring.matrix.set(shape.matrix.value)
                self.z_ring.remove_state(ShapeState.HIDE)
            else:
                self.x_ring.add_state(ShapeState.HIDE)
                self.y_ring.add_state(ShapeState.HIDE)
                self.z_ring.add_state(ShapeState.HIDE)
