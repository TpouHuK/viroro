from pymunk.vec2d import Vec2d
import PySimpleGUI as sg


def tk_draw_circle(canvas, point, radius, *args, **kwargs):
    """Draw circle on tkinter canvas."""
    return canvas.create_oval(
            point.x - radius, point.y - radius,
    point.x + radius, point.y + radius, *args, **kwargs)


class DrawOptions():
    def __init__(self, canvas, zoom, size, offset=Vec2d(0, 0)):
        self.canvas = canvas
        self.offset = Vec2d(*offset)
        self.zoom = zoom
        self.angle = 0
        self.size = Vec2d(*size)

    def scale_screen(self, v):
        return v * self.zoom

    def to_screen(self, v):
        on_screen = v * self.zoom + self.offset 
        rotated = (on_screen - self.size/2).rotated(-self.angle) + self.size/2
        return rotated

    def clear(self):
        self.canvas.delete("all")


class Viewport():
    def __init__(self, size, key="-VIEWPORT-"):
        self.sg_graph = sg.Graph(size, (0, 0), size, key="-VIEWPORT-")
        self.size = size

    def create_draw_options(self, zoom, offset):
        """Must be called afer `sg.Window.Finalize`."""
        self.draw_options = DrawOptions(
                self.sg_graph.TKCanvas,
                zoom,
                self.size,
                offset,
                )

    def set_view(self, zoom, offset, angle=0):
        self.draw_options.zoom = zoom
        self.draw_options.offset = offset
        self.draw_options.angle = angle

    def show(self, field):
        self.draw_options.clear()
        draw_car(field.car, self.draw_options)
        draw_walls(field.walls, self.draw_options)
        draw_checkpoints(field.checkpoints, self.draw_options)


def draw_distance_sensor(ds, draw_options):
    canvas = draw_options.canvas
    p1, p2 = ds._world_cords()
    p1 = draw_options.to_screen(p1)

    point = ds.get_collision_point()
    if point:
        point = draw_options.to_screen(point)
        p2 = point
        canvas.create_line(*p1, *p2, fill="#5cffff")
        tk_draw_circle(canvas, point, radius=3, fill="#ff5cef", width=1)
    else:
        p2 = draw_options.to_screen(p2)
        canvas.create_line(*p1, *p2, fill="#5cffff")


def draw_wheel(wheel, draw_options):
    canvas = draw_options.canvas
    for line in wheel._lines_to_draw():
        p1, p2 = line
        p1 = draw_options.to_screen(p1)
        p2 = draw_options.to_screen(p2)
        wheel.on_screen.append(canvas.create_line(*p1, *p2))


def draw_car(car, draw_options):
    canvas = draw_options.canvas
    for sensor in car.sensors:
        draw_distance_sensor(sensor, draw_options)
    for wheel in car._wheels:
        draw_wheel(wheel, draw_options)

    for line in car._lines_to_draw():
        p1, p2 = line
        p1 = draw_options.to_screen(p1)
        p2 = draw_options.to_screen(p2)
        canvas.create_line(*p1, *p2)

    SIZE = 4
    p = draw_options.to_screen(car.body.position)
    canvas.create_line(
            p-Vec2d(0, SIZE), p+Vec2d(0, SIZE),
            fill="#db91c5", width=2
            )
    canvas.create_line(
            p-Vec2d(SIZE, 0), p+Vec2d(SIZE, 0),
            fill="#db91c5", width=2
            )


def draw_walls(walls, draw_options):
    canvas = draw_options.canvas
    for shape in walls.s_walls:
            canvas.create_line(
                *draw_options.to_screen(shape.a),
                *draw_options.to_screen(shape.b),
                fill="black", width=3)


def draw_checkpoints(cps, draw_options):
    canvas = draw_options.canvas
    CROSS_SIZE = 4
    for p in cps.checkpoints:
        p = draw_options.to_screen(p)
        canvas.create_line(
            p-Vec2d(0, CROSS_SIZE), p+Vec2d(0, CROSS_SIZE),
            fill="#9ede92", width=2
            )
        canvas.create_line(
            p-Vec2d(CROSS_SIZE, 0), p+Vec2d(CROSS_SIZE, 0),
            fill="#9ede92", width=2
            )
        tk_draw_circle(
            canvas, p,
            draw_options.scale_screen(cps.detection_radius))

    for num, car in enumerate(cps.cars):
        p1 = draw_options.to_screen(car.position)
        p2 = draw_options.to_screen(cps.checkpoints[cps.car_checkpoint[num]])
        canvas.create_line(p1, p2, fill="#a880ff")


def draw_test_circle(circle, draw_options):
    canvas = draw_options.canvas
    pos = draw_options.to_screen(circle.shape.body.position)
    rad = draw_options.scale_screen(circle.radius)
    tk_draw_circle(canvas, pos, rad, fill="#63ff92", width=1)


def draw_field(field, draw_options):
    draw_car(field.car, draw_options)
    draw_walls(field.walls, draw_options)
    draw_checkpoints(field.checkpoints, draw_options)
