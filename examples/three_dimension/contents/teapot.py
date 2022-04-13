from typing import Optional
from OpenGL import GL
from pydear.utils.item import Item
from pydear.scene.camera import Camera
from pydear import glo


class TeaPot(Item):
    def __init__(self) -> None:
        super().__init__('teapot')
        self.camera = Camera()
        self.drawable: Optional[glo.Drawable] = None

    def input(self, x, y, dx, dy, left, right, middle, wheel):
        self.camera.update(
            x, y,
            dx, dy,
            left, right, middle,
            wheel)

    def render(self, w, h):
        self.camera.onResize(w, h)
        # GL.glEnable(GL.GL_CULL_FACE)
        # GL.glCullFace(GL.GL_BACK)
        # GL.glFrontFace(GL.GL_CCW)
        GL.glEnable(GL.GL_DEPTH_TEST)

        if not self.drawable:
            # shader
            shader = glo.Shader.load_from_pkg('pydear', 'assets/mesh')
            assert isinstance(shader, glo.Shader)

            props = shader.create_props(self.camera)

            # mesh
            from pydear.scene import teapot
            self.drawable = teapot.create(shader, props)

        self.drawable.draw()
