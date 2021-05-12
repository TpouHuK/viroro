from math import copysign, radians, sqrt
import pymunk
from pymunk.vec2d import Vec2d

class DrawOptions():
    def __init__(self, canvas, zoom, offset=Vec2d(0, 0)):
        self.canvas = canvas
        self.offset = offset
        self.zoom = zoom

    def scale_screen(self, v):
        return v * self.zoom

    def to_screen(self, v):
        return v * self.zoom + self.offset


class PGObject():
    """Base class for all physical objects.
    
    PGObject stands for Physics and Graphics object.
    They should provide following properties/functions:
    
    self.show(draw_options) -- function that draws object using draw_options
    self.cls(draw_options) -- function that removes object using draw_options

    self._upd() -- function that is called before every simulation tick
    self._to_space -- list of items that are added to pymunk.Space
    """
    def _upd(self):
        """Called every simulation tick."""
        pass

    def show(self, draw_options):
        """Draw object on a tkinter canvas."""
        pass

    def cls(self, draw_options):
        """Remove object from a tkinter canvas."""
        canvas = draw_options.canvas
        for item in self.on_screen:
            canvas.delete(item)
        self.on_screen = []


def draw_circle(canvas, point, radius, *args, **kwargs):
    """Draw circle on tkinter canvas."""
    return canvas.create_oval(
            point.x - radius, point.y - radius,
    point.x + radius, point.y + radius, *args, **kwargs)


class DistanceSensor(PGObject):
    """Distance sensor that simulates IR/US sensor.

    body -- pymunk.Body() to attach sensor to
    x -- x position from (0, 0) of car
    y -- y position from (0, 0) of car
    angle -- beam angle, -90=LEFT, 0=UP, 90=RIGHT
    range_ -- maximum measurement distance
    beam_width -- width of a beam
    shape_filter -- pymunk.ShapeFilter that is applied to a shape
    """
    def __init__(
            self, body, x, y, angle, range_, beam_width,
            shape_filter):
        self.on_screen = []
        self._to_space = []
        self._range_ = range_

        start = Vec2d(x, -y)
        finish = start + Vec2d(0, -range_).rotated(radians(angle))

        self._shape = pymunk.Segment(body, start, finish, beam_width)
        self._shape.sensor = True
        self._shape.filter = shape_filter
        self._to_space = [self._shape]

    def get_collision_point(self):
        """Return point in pymunk world coords where sensor detects something or None."""
        p1, p2 = self._world_cords()
        q = self._shape.space.segment_query_first(
                p1, p2, self._shape.radius,
                self._shape.filter)
        if q:
            return q.point
        return None

    def read_distance(self):
        """Return current sensor value (colliding distance), or inf if no collision."""
        p1, p2 = self._world_cords()
        q = self._shape.space.segment_query_first(
                p1, p2, self._shape.radius,
                self._shape.filter)
        if q:
            return q.alpha * self._range_
        return float("inf")

    def _world_cords(self):
        """Start and end points of sensor ray in pymunk world cords."""
        body = self._shape.body
        p1 = self._shape.a.rotated(body.angle) + body.position
        p2 = self._shape.b.rotated(body.angle) + body.position
        return (p1, p2)

    def show(self, draw_options):
        canvas = draw_options.canvas
        body = self._shape.body
        p1, p2 = self._world_cords()
        p1 = cs.m_to_pd(p1)

        self.cls(draw_options)
        self.on_screen = []
        point = self.get_collision_point()
        if point:
            point = draw_options.to_screen(point)
            p2 = point
            self.on_screen.append(canvas.create_line(*p1, *p2, fill="#5cffff"))
            self.on_screen.append(draw_circle(
                canvas, point, radius=3, fill="#ff5cef", width=1))
        else:
            p2 = draw_options.to_screen(p2)
            self.on_screen.append(canvas.create_line(*p1, *p2, fill="#5cffff"))


class Car(PGObject):
    """Car object with wheels and ??? FIXME"""

    def __init__(self, config, position, group=1):
        """Create a car.

        config -- car properties, big dictionary, big mess
        position -- position in pymunk world coords
        group -- car collision group, every car should 
        """
        self.on_screen = []
        self._to_space = []
        self.motor_power = 0

        shape_filter = pymunk.ShapeFilter(group)
        position = Vec2d(*position)

        tw = config["front_wheels_x"]
        th = config["front_wheels_y"]
        bw = config["back_wheels_x"]
        bh = config["back_wheels_y"]
        wheel_c = (
            config["wheel_radius"],
            config["wheel_width"],
            config["wheel_mass"],
            config["wheel_slipforce"],
            config["wheel_friction_force"],
            config["wheel_side_friction"],
            config["wheel_weird_forward_friction"])
        self._wheels = [
            Wheel(*wheel_c, position + Vec2d(-tw, -th), shape_filter),
            Wheel(*wheel_c, position + Vec2d(+tw, -th), shape_filter),
            Wheel(*wheel_c, position + Vec2d(-bw, +bh), shape_filter),
            Wheel(*wheel_c, position + Vec2d(+bw, +bh), shape_filter),
            ]
        for wheel in self._wheels:
            self._to_space.extend(wheel._to_space)

        self.width = config["car_width"]
        self.height = config["car_height"]
        self.mass = config["car_mass"]
        self.max_steer_angle = config["max_steer_angle"]
        self.max_speed = config["max_speed"]
        self.max_power = config["max_power"]

        moment = pymunk.moment_for_box(self.mass, (self.width, self.height))
        self.body = pymunk.Body(self.mass, moment)
        self.body.position = position
        w, h = self.width, self.height
        self.shape = pymunk.Poly(
            self.body,
            [
                (-self.width/2, -self.height),
                (self.width/2, -self.height),
                (self.width/2, self.height),
                (-self.width/2, self.height)
                ])
        self.shape.friction = config["hull_friction"]
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
            c2.error_bias = 0.00001
            self._to_space.extend((c1, c2))
            return c2

        self.lw_gearjoint = glue(self._wheels[0].body, self.body)
        self.rw_gearjoint = glue(self._wheels[1].body, self.body)
        glue(self._wheels[2].body, self.body)
        glue(self._wheels[3].body, self.body)

        self.sensors = []
        for sensor_config in config["sensors"]:
            sensor_config["range_"] = sensor_config["range"]
            del sensor_config["range"]
            sens = DistanceSensor(
                self.body, **sensor_config,
                shape_filter=shape_filter)
            self.sensors.append(sens)
            self._to_space.extend(sens._to_space)

    def steer(self, deg):
        """Set angle of front wheels in degrees.

        deg -- degrees (positive -> clockwise, negative -> counterclockwise)
        """
        angle = -radians(max(min(self.max_steer_angle, deg), -self.max_steer_angle))
        self.lw_gearjoint.phase = angle
        self.rw_gearjoint.phase = angle

    def push(self, power):
        """Set power with which car is pushed forward.

        power -- 0-100
        """
        self.motor_power = power/100

    @property
    def position(self):
        """Center of a car in pymunk world cords."""
        return self.body.position

    @property
    def speed(self):
        """Speed in pymunk units."""
        return abs(self.body.velocity)

    def get_sensor_values(self):
        """Return list of floats, representing value of each sensor."""
        return [sensor.read_distance() for sensor in self.sensors]

    def _upd(self):
        #fixme, speed should be taken from wheels not from the car
        cur_speed = self.speed
        
        x = min(1, max(cur_speed, 0)/self.max_speed)
        assert 0 <= x <= 1

        force_percent = (1-x)**0.07
        force = self.max_power*self.motor_power*force_percent
        wheel_force = -force/4

        for wheel in self._wheels:
            wheel.body.apply_force_at_local_point((0, wheel_force))

    def _lines_to_draw(self):
        verts = []
        lines = []
        for v in self.shape.get_vertices():
            world_cords = v.rotated(self.body.angle) + self.body.position
            draw_cords = world_cords
            if verts:
                lines.append((verts[-1], draw_cords))
            verts.append(world_cords)
        lines.append((verts[-1], verts[0]))
        return lines

    def show(self, draw_options):
        canvas = draw_options.canvas
        self.cls(canvas)
        for sensor in self.sensors:
            sensor._show(canvas)

        for wheel in self._wheels:
            wheel._show(canvas)

        for line in self._lines_to_draw():
            p1, p2 = line
            p1 = draw_options.to_screen(p1)
            p2 = draw_options.to_screen(p2)
            self.on_screen.append(canvas.create_line(*p1, *p2))

        SIZE = 4
        p = self.body.position
        p = draw_option.to_screen(p)
        a = canvas.create_line(
                p-Vec2d(0, SIZE), p+Vec2d(0, SIZE),
                fill="#db91c5", width=2
                )
        b = canvas.create_line(
                p-Vec2d(SIZE, 0), p+Vec2d(SIZE, 0),
                fill="#db91c5", width=2
                )
        self.on_screen.append(a)
        self.on_screen.append(b)

    def cls(self, draw_options):
        """Remove object from a tkinter canvas."""
        canvas = draw_options.canvas
        for item in self.on_screen:
            canvas.delete(item)
        self.on_screen = []
        for wheel in self._wheels:
            wheel.cls(draw_options)
        for sensor in self.sensors:
            sensor.cls(draw_options)


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
            horz_imp *= 0.99 # FIXME what is me
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
            draw_cords = world_cords
            if verts:
                lines.append((verts[-1], draw_cords))
            verts.append(world_cords)
        lines.append((verts[-1], verts[0]))
        return lines

    def show(self, draw_options):
        canvas = draw_options.canvas
        self.cls(draw_options)
        for line in self._lines_to_draw():
            p1, p2 = line
            p1 = draw_options.to_screen(p1)
            p2 = draw_options.to_screen(p2)
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

    def show(self, draw_options):
        canvas = draw_options.canvas
        self.cls(draw_options)
        pos = draw_options.to_screen(self.shape.body.position)
        rad = draw_options.scale_screen(self.radius)
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

    def show(self, draw_options):
        if self.on_screen:
            return
        canvas = draw_options
        for shape in self.s_walls:
            self.on_screen.append(
                    canvas.create_line(
                        *cs.m_to_pd(shape.a),
                        *cs.m_to_pd(shape.b),
                        fill="black", width=3))


class PymunkField():
    def __init__(self, dt, microsteps=1, iterations=15):
        self.space = pymunk.Space()
        self.space.iterations = iterations

        self.microsteps = microsteps
        self.microstep_size = dt/microsteps

        self._to_upd = []

    def add(self, *items):
        for item in items:
            self.space.add(*item._to_space)
            self._to_upd.append(item)

    def step(self):
        for i in range(self.microsteps):
            for item in self._to_upd:
                item._upd()
            self.space.step(self.microstep_size)


class CheckPoints(PGObject):
    def __init__(self, checkpoints, detection_radius):
        """CheckPoints.

        checkpoints - list of pymunk world points [(0, 0), (0, 1), ...]
        """
        self.f_on_screen = []
        self.on_screen = []
        self._to_space = []
        
        self.checkpoints = [Vec2d(*p) for p in checkpoints]
        self.distances = [
            self.checkpoints[i].get_distance(self.checkpoints[i-1])
            for i in range(len(self.checkpoints))]

        self.cars = []
        self.car_checkpoint = []
        self.car_score = []
        self.detection_radius = detection_radius
        self.rad2 = detection_radius**2

    def add_car(self, car):
        self.cars.append(car)
        self.car_checkpoint.append(0)
        self.car_score.append(0)

    def get_car_score(self, idx):
        cur_cp = self.car_checkpoint[idx]
        nxt = self.checkpoints[cur_cp]

        dist_to_next = self.cars[idx].position.get_distance(
                self.checkpoints[cur_cp])

        diff = self.distances[cur_cp] - dist_to_next
        return self.car_score[idx] + diff

    def _upd(self):
        for num, car in enumerate(self.cars):
            cur_cp = self.car_checkpoint[num]
            car_pos = car.position
            nxt = self.checkpoints[cur_cp]
            prv2 = self.checkpoints[(cur_cp-2)%len(self.checkpoints)]
            
            if car_pos.get_dist_sqrd(prv2) < self.rad2:
                self.car_checkpoint[num] -= 1
                self.car_checkpoint[num] %= len(self.checkpoints)
                self.car_score[num] -= self.distances[cur_cp-1]

            if car_pos.get_dist_sqrd(nxt) < self.rad2:
                self.car_score[num] += self.distances[cur_cp]
                self.car_checkpoint[num] += 1
                self.car_checkpoint[num] %= len(self.checkpoints)

    def show(self, draw_options):
        canvas = draw_options
        CROSS_SIZE = 4
        self.cls(draw_options, full=False)
        if not self.f_on_screen:
            for p in self.checkpoints:
                p = draw_options.to_screen(p)
                a = canvas.create_line(
                        p-Vec2d(0, CROSS_SIZE), p+Vec2d(0, CROSS_SIZE),
                        fill="#9ede92", width=2
                        )
                b = canvas.create_line(
                        p-Vec2d(CROSS_SIZE, 0), p+Vec2d(CROSS_SIZE, 0),
                        fill="#9ede92", width=2
                        )
                c = draw_circle(
                        canvas, p,
                        draw_options.scale_screen(self.detection_radius))
                self.f_on_screen.append(a)
                self.f_on_screen.append(b)
                self.f_on_screen.append(c)

        for num, car in enumerate(self.cars):
            p1 = draw_options.to_screen(car.position)
            p2 = draw_options.to_screen(
                    self.checkpoints[self.car_checkpoint[num]]
                    )
            a = canvas.create_line(p1, p2, fill="#a880ff")
            self.on_screen.append(a)

    def cls(self, draw_options, full=True):
        for item in self.on_screen:
            canvas.delete(item)
        if full:
            for item in self.f_on_screen:
                canvas.delete(item)
        self.on_screen = []
