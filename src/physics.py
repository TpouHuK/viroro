from PySimpleGUI import obj_to_string as pf
import field
import pymunk
from pymunk.vec2d import Vec2d
import constants as cs
import time
from math import copysign, radians

class Car():
    def __init__(self, space, position):
        self.on_screen = []
        position = Vec2d(*position)
        tw = 0.10
        th = 0.20
        bw = 0.10
        bh = 0.20

        t_w_l = Wheel(space, position + Vec2d(-tw, -th))
        t_w_r = Wheel(space, position + Vec2d(+tw, -th))

        b_w_l = Wheel(space, position + Vec2d(-bw, +th))
        b_w_r = Wheel(space, position + Vec2d(+bw, +th))

        self.wheels = [t_w_l, t_w_r, b_w_l, b_w_r]

        self.width = 0.25
        self.height = 0.40
        self.mass = 1.4
        
        moment = pymunk.moment_for_box(self.mass, (self.width, self.height))
        self.body = pymunk.Body(self.mass, moment)
        self.body.position = position

        w = self.width
        h = self.height


        self.shape = pymunk.Poly(self.body, [(-w/2, -h), (w/2, -h), (w/2, h), (-w/2, h)])
        space.add(self.body, self.shape)

        def glue(b1, b2):
            #c1 = pymunk.constraints.PivotJoint(b1, b2, b2.position, b1.position)
            #c1 = pymunk.constraints.PivotJoint(b1, b2, (0, 0))
            #c1 = pymunk.constraints.PinJoint(b1, b2, b1.position, b1.position)
            c1 = pymunk.constraints.PinJoint(b1, b2, (0, 0), b1.position - position)
            c2 = pymunk.constraints.GearJoint(b1, b2, 0, 1)
            c1.collide_bodies = False
            c2.collide_bodies = False
            c1.error_bias = 0.1
            c2.error_bias = 0.1
            space.add(c1, c2)
            return c2
            #space.add(c1)

        glue(b_w_l.body, self.body)
        glue(b_w_r.body, self.body)

        self.r1 = glue(t_w_l.body, self.body)
        self.r2 = glue(t_w_r.body, self.body)

    def turn(self, deg):
        angle = radians(deg)
        self.r1.phase = angle
        self.r2.phase = angle

    def push(self, how_much):
        self.body.apply_impulse_at_local_point((0, how_much), (0, -self.height/2))

    def show(self, canvas):
        for wheel in self.wheels:
            wheel.show(canvas)

        for line in self.on_screen:
            canvas.delete(line)
        self.on_screen = []

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


class Wheel():
    def __init__(self, space, position):
        r = 0.05 # 3cm
        w = 0.03 # 2cm
        m = 0.01 # 10 g
        self.radius = r
        self.width = w
        self.mass = m

        # https://en.wikipedia.org/wiki/List_of_moments_of_inertia
        moment = 1/12 * m * (3*r**2 + w**2) 

        self.slip_force = float("inf")
        self.friction_force = 1

        self.body = pymunk.Body(m, moment)
        self.body.position = position
        #self.body.angle = 0.3
        #self.body.velocity = (40, 0.5)
        #self.body.angular_velocity = 2
        self.shape = pymunk.Poly(self.body, [(-w/2, -r), (w/2, -r), (w/2, r), (-w/2, r)])
        self.shape.friction = 0.5

        def wheel_physics(body, gravity, damping, dt):
            local_velocity = body.velocity.rotated(-body.angle)
            
            sf_imp = copysign(min(self.slip_force*dt, abs(local_velocity.x*m)), -local_velocity.x)
            rf_imp = copysign(min(self.friction_force*dt, abs(local_velocity.y)*m), -local_velocity.y)
            #rf_imp = rf_imp + copysign(sf_imp, local_velocity.y)

            body.apply_impulse_at_local_point((sf_imp, rf_imp))
            #body.angular_velocity *= 0.98
            pymunk.Body.update_velocity(body, gravity, damping, dt)

        self.body.velocity_func = wheel_physics

        space.add(self.body, self.shape)
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

    def show(self, canvas):
        for line in self.on_screen:
            canvas.delete(line)
        self.on_screen = []

        for line in self._lines_to_draw():
            p1, p2 = line
            self.on_screen.append(canvas.create_line(*p1, *p2))


class PhysicalField():
    def __init__(self):
        self.space = pymunk.Space()
        self.space.iterations = cs.ITERATIONS

        for wall in field.walls:
            body = pymunk.Body(0, 0, body_type=pymunk.Body.STATIC)
            collision_shape = pymunk.Segment(body, *wall, cs.WALL_THICKNESS)
            collision_shape.elasticity = 0.999
            self.space.add(body, collision_shape)

        car = Car(self.space, (0.5, 0.5))
        self.car = car
        self.to_show = [car]

        #wheel1 = Wheel(self.space, (0.5, 0.5))
        #wheel2 = Wheel(self.space, (0.7, 0.5))
        #c1 = pymunk.constraints.PivotJoint(wheel2.body, wheel1.body,
                #(0, 0), (0.3, 0))
        #c2 = pymunk.constraints.PivotJoint(wheel2.body, wheel1.body,
                #(0, 0.2), (0.3, 0.2))
        #c3 = pymunk.constraints.GearJoint(wheel2.body, wheel1.body, 0, 1)
        #self.space.add(c1)
        #self.space.add(c3)
        #self.space.add(c2)
        
        #self.to_show.append(wheel1)
        #self.to_show.append(wheel2)

        self.create_testing_circle()


    def get_walls_to_draw(self):
        walls = []
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Segment):
                assert shape.body.body_type == pymunk.Body.STATIC
                walls.append((cs.m_to_pd(shape.a), cs.m_to_pd(shape.b)))
        return walls

    def get_circle_to_draw(self):
        pos = self.test_circle.body.position
        radius = self.test_circle.radius
        return (cs.m_to_pd(pos), cs.m_to_p(radius))

    def create_testing_circle(self):
        mass = 0.1
        radius = 0.15
        x, y = 0.5, 3.5
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        body = pymunk.Body(mass, inertia)
        body.position = x, y
        shape = pymunk.Circle(body, radius, (0, 0))
        shape.elasticity = 0.999
        shape.friction = 0.5
        
        body.apply_impulse_at_local_point((0.3, 1))
        self.test_circle = shape

        self.space.add(body, shape)

    def step(self):
        for i in range(cs.MICROSTEP_AMOUNT):
            self.space.step(cs.MICROSTEP_SIZE)


if __name__ == "__main__":
    fd = PhysicalField()
    print()
