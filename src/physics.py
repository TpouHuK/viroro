from math import copysign, radians
import pymunk
from pymunk.vec2d import Vec2d
import constants as cs


class PGObject():
    def _upd(self):
        """Called every simulation tick."""
        pass

    def _show(self, canvas):
        """Draw object on a tkinter canvas."""
        pass

    def _cls(self, canvas):
        """Remove object from a tkinter canvas."""
        for line in self.on_screen:
            canvas.delete(line)
        self.on_screen = []


def draw_circle(canvas, point, radius, *args, **kwargs):
    return canvas.create_oval(
            point.x - radius, point.y - radius,
    point.x + radius, point.y + radius, *args, **kwargs)


class DistanceSensor(PGObject):
    def __init__(
            self, body, v_offset, h_offset, angle, distance, width,
            shape_filter):
        self.on_screen = []
        self._to_space = []
        self._distance = distance

        start = Vec2d(h_offset, -v_offset)
        finish = start + Vec2d(0, -distance).rotated(radians(angle))
        self._shape = pymunk.Segment(body, start, finish, width)
        self._shape.sensor = True
        self._shape.filter = shape_filter
        self._to_space = [self._shape]

    def get_collision_point(self):
        p1, p2 = self._world_cords()
        q = self._shape.space.segment_query_first(
                p1, p2, self._shape.radius,
                self._shape.filter)
        if q:
            return q.point
        return None

    def read_distance(self):
        p1, p2 = self._world_cords()
        q = self._shape.space.segment_query_first(
                p1, p2, self._shape.radius,
                self._shape.filter)
        if q:
            return q.alpha * self._distance
        return float("inf")

    def _world_cords(self):
        body = self._shape.body
        p1 = self._shape.a.rotated(body.angle) + body.position
        p2 = self._shape.b.rotated(body.angle) + body.position
        return (p1, p2)

    def _show(self, canvas):
        body = self._shape.body
        p1, p2 = self._world_cords()
        p1 = cs.m_to_pd(p1)

        self._cls(canvas)
        self.on_screen = []
        point = self.get_collision_point()
        if point:
            point = cs.m_to_pd(point)
            p2 = point
            self.on_screen.append(canvas.create_line(*p1, *p2, fill="#5cffff"))
            self.on_screen.append(draw_circle(
                canvas, point, radius=3, fill="#ff5cef", width=1))
        else:
            p2 = cs.m_to_pd(p2)
            self.on_screen.append(canvas.create_line(*p1, *p2, fill="#5cffff"))


class Car(PGObject):
    def __init__(self, props, position, group=1):
        self.on_screen = []
        self._to_space = []
        self.motor_power = 0
        self.algo = None
        shape_filter = pymunk.ShapeFilter(group)

        position = Vec2d(*position)
        tw = props["tw"]
        th = props["th"]
        bw = props["bw"]
        bh = props["bh"]
        w_props = (props["wheel_radius"],
            props["wheel_width"],
            props["wheel_mass"],
            props["wheel_slipforce"],
            props["wheel_friction_force"],
            props["wheel_side_friction"],
            props["wheel_weird_forward_friction"])

        t_w_l = Wheel(*w_props, position + Vec2d(-tw, -th), shape_filter)
        t_w_r = Wheel(*w_props, position + Vec2d(+tw, -th), shape_filter)
        b_w_l = Wheel(*w_props, position + Vec2d(-bw, +th), shape_filter)
        b_w_r = Wheel(*w_props, position + Vec2d(+bw, +th), shape_filter)
        self.wheels = [t_w_l, t_w_r, b_w_l, b_w_r]
        for w in self.wheels:
            self._to_space.extend(w._to_space)

        self.width = props["car_width"]
        self.height = props["car_height"]
        self.mass = props["car_mass"]
        moment = pymunk.moment_for_box(self.mass, (self.width, self.height))
        self.body = pymunk.Body(self.mass, moment)
        self.body.position = position
        w, h = self.width, self.height
        self.shape = pymunk.Poly(
            self.body, [(-w/2, -h), (w/2, -h), (w/2, h), (-w/2, h)])
        self.shape.friction = props["hull_friction"]
        self.shape.filter = shape_filter
        self._to_space.extend((self.body, self.shape))

        def glue(b1, b2):
            """Bind two bodies together."""
            c1 = pymunk.constraints.PinJoint(
                b1, b2, (0, 0), b1.position - position)
            c2 = pymunk.constraints.GearJoint(b1, b2, 0, 1)
            c1.collide_bodies = False
            c2.collide_bodies = False
            c1.error_bias = 0
            c2.error_bias = 0
            self._to_space.extend((c1, c2))
            return c2
        glue(b_w_l.body, self.body)
        glue(b_w_r.body, self.body)
        self.lw_gearjoint = glue(t_w_l.body, self.body)
        self.rw_gearjoint = glue(t_w_r.body, self.body)

        self.sensors = []
        for s_props in props['sensors']:
            sens = DistanceSensor(
                self.body, **s_props,
                shape_filter=shape_filter)
            self.sensors.append(sens)
            self._to_space.extend(sens._to_space)


    def steer(self, deg):
        """Set angle of front wheels in degrees.

        deg -- degrees (positive -> clockwise, negative -> counterclockwise)
        """
        angle = -radians(max(min(30, deg), -30))
        self.lw_gearjoint.phase = angle
        self.rw_gearjoint.phase = angle

    def push(self, force):
        """Set force with which car is pushed forward.

        force -- newtons (F=ma)
        """
        self.motor_power = -force

    @property
    def speed(self):
        return abs(self.body.velocity)

    def get_sensor_values(self):
        return [sensor.read_distance() for sensor in self.sensors]

    def _upd(self):
        force = self.motor_power
        self.body.apply_force_at_local_point((0, force), (0, -self.height/2))

    def _show(self, canvas):
        for sensor in self.sensors:
            sensor._show(canvas)

        for wheel in self.wheels:
            wheel._show(canvas)

        self._cls(canvas)
        for line in self._lines_to_draw():
            p1, p2 = line
            self.on_screen.append(canvas.create_line(*p1, *p2))

    def _lines_to_draw(self):
        verts = []
        lines = []
        for v in self.shape.get_vertices():
            world_cords = v.rotated(self.body.angle) + self.body.position
            draw_cords = cs.m_to_pd(world_cords)
            if verts:
                lines.append((verts[-1], draw_cords))
            verts.append(cs.m_to_pd(world_cords))
        lines.append((verts[-1], verts[0]))
        return lines


class Wheel(PGObject):
    def __init__(
            self, radius, width,
            mass, slip_force, friction_force,
            side_friction, weird_forward_friction,
            position,
            shape_filter=pymunk.ShapeFilter()):
        r = radius
        w = width
        m = mass
        self.radius = r
        self.width = w
        self.mass = m

        moment = 1/12 * m * (3*r**2 + w**2) 

        self.slip_force = slip_force
        self.friction_force = friction_force

        self.body = pymunk.Body(m, moment)
        self.body.position = position
        self.shape = pymunk.Poly(self.body, [
            (-w/2, -r),
            (w/2, -r),
            (w/2, r),
            (-w/2, r)])
        self.shape.friction = side_friction
        self.shape.filter = shape_filter

        def wheel_physics(body, gravity, damping, dt):
            local_velocity = body.velocity.rotated(-body.angle)
            
            horz_imp = copysign(
                min(self.slip_force*dt, abs(local_velocity.x*m)),
                -local_velocity.x)
            vert_imp = copysign(
                min(
                    self.friction_force*dt,
                    abs(local_velocity.y)*m*weird_forward_friction),
                -local_velocity.y)

            body.apply_impulse_at_local_point((horz_imp, vert_imp))
            pymunk.Body.update_velocity(body, gravity, damping, dt)

        self.body.velocity_func = wheel_physics

        self._to_space = [self.body, self.shape]
        self.on_screen = []

    def _lines_to_draw(self):
        verts = []
        lines = []
        for v in self.shape.get_vertices():
            world_cords = v.rotated(self.body.angle) + self.body.position
            draw_cords = cs.m_to_pd(world_cords)
            if verts:
                lines.append((verts[-1], draw_cords))
            verts.append(cs.m_to_pd(world_cords))
        lines.append((verts[-1], verts[0]))
        return lines

    def _show(self, canvas):
        self._cls(canvas)
        for line in self._lines_to_draw():
            p1, p2 = line
            self.on_screen.append(canvas.create_line(*p1, *p2))


class Circle(PGObject):
    def __init__(
            self, position, mass,
            radius, elasticity):
        self.mass = mass
        self.radius = radius
        moment = pymunk.moment_for_circle(mass, 0, radius, (0, 0)) 
        body = pymunk.Body(self.mass, moment)
                
        body.position = position

        self.shape = pymunk.Circle(body, self.radius, (0, 0))
        self.shape.elasticity = elasticity

        self._to_space = [body, self.shape]
        self.on_screen = []

    def bump(self, force):
        """Apply impulse to circle."""
        self.shape.body.apply_impulse_at_local_point(force)

    def _show(self, canvas):
        self._cls(canvas)
        pos = cs.m_to_pd(self.shape.body.position)
        rad = cs.m_to_p(self.radius)
        self.on_screen = [
                canvas.create_oval(pos.x - rad, pos.y - rad,
                pos.x + rad, pos.y + rad, fill="#63ff92", width=1)]


class Walls(PGObject):
    """Non-movable(static) thin field walls.

    walls -- list of point pairs [((0, 0), (1, 1)), ...]
             each pair represents a wall
    thickness -- thickness of a walls, mostly to prevent pymunk bugs
    elasticity -- elasticity of collisions with a walls
    """
    def __init__(self, walls, thickness, elasticity):
        self._to_space = []
        self.on_screen = []

        self.s_walls = []
        for wall in walls:
            body = pymunk.Body(
                    mass=0, moment=0,
                    body_type=pymunk.Body.STATIC)
            collision_shape = pymunk.Segment(body, *wall, thickness)
            collision_shape.elasticity = elasticity
            self._to_space.extend((body, collision_shape))

            self.s_walls.append(collision_shape)

    def _show(self, canvas):
        if self.on_screen:
            return
        for shape in self.s_walls:
            self.on_screen.append(
                    canvas.create_line(
                        *cs.m_to_pd(shape.a),
                        *cs.m_to_pd(shape.b),
                        fill="black", width=3))


class PymunkField():
    def __init__(self):
        self.space = pymunk.Space()
        self.space.iterations = cs.ITERATIONS
        self._to_upd = []

    def add(self, *items):
        for item in items:
            self.space.add(*item._to_space)
            self._to_upd.append(item)

    def step(self):
        for i in range(cs.MICROSTEP_AMOUNT):
            for item in self._to_upd:
                item._upd()
            self.space.step(cs.MICROSTEP_SIZE)


if __name__ == "__main__":
    fd = PymunkField()
    print()
