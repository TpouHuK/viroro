from PySimpleGUI import obj_to_string as pf
import field
import pymunk
from pymunk.vec2d import Vec2d
import constants as cs
import time
from math import copysign, radians

class PGObject():
    def _upd(self):
        pass

    def _show(self):
        pass

    def _cls(self, canvas):
        for line in self.on_screen:
            canvas.delete(line)
        self.on_screen = []

class Car(PGObject):
    def __init__(self, props, position):
        self.on_screen = []
        self._to_space = []

        position = Vec2d(*position)

        tw = props["tw"]
        th = props["th"]
        bw = props["bw"]
        bh = props["bh"]

        w_r = props["wheel_radius"]
        w_w = props["wheel_width"]
        w_m = props["wheel_mass"]

        t_w_l = Wheel(w_r, w_w, w_m, position + Vec2d(-tw, -th))
        t_w_r = Wheel(w_r, w_w, w_m, position + Vec2d(+tw, -th))

        b_w_l = Wheel(w_r, w_w, w_m, position + Vec2d(-bw, +th))
        b_w_r = Wheel(w_r, w_w, w_m, position + Vec2d(+bw, +th))

        self.wheels = [t_w_l, t_w_r, b_w_l, b_w_r]

        for w in self.wheels:
            self._to_space.extend(w._to_space)

        self.width = props["car_width"]
        self.height = props["car_height"]
        self.mass = props["car_mass"]
        
        moment = pymunk.moment_for_box(self.mass, (self.width, self.height))
        self.body = pymunk.Body(self.mass, moment)
        self.body.position = position

        w = self.width
        h = self.height
        self.shape = pymunk.Poly(self.body, [(-w/2, -h), (w/2, -h), (w/2, h), (-w/2, h)])
        self.shape.friction = props["hull_friction"]
        self._to_space.extend((self.body, self.shape))

        self.motor_power = 0

        def glue(b1, b2):
            #c1 = pymunk.constraints.PivotJoint(b1, b2, b2.position, b1.position)
            #c1 = pymunk.constraints.PivotJoint(b1, b2, (0, 0))
            #c1 = pymunk.constraints.PinJoint(b1, b2, b1.position, b1.position)
            c1 = pymunk.constraints.PinJoint(b1, b2, (0, 0), b1.position - position)
            c2 = pymunk.constraints.GearJoint(b1, b2, 0, 1)
            c1.collide_bodies = False
            c2.collide_bodies = False
            c1.error_bias = 0
            c2.error_bias = 0
            self._to_space.extend((c1, c2))
            return c2

        glue(b_w_l.body, self.body)
        glue(b_w_r.body, self.body)

        self.r1 = glue(t_w_l.body, self.body)
        self.r2 = glue(t_w_r.body, self.body)

    def turn(self, deg):
        angle = radians(deg)
        self.r1.phase = angle
        self.r2.phase = angle

    def push(self, x):
        self.motor_power = x

    def _upd(self):
        force = self.motor_power
        self.body.apply_force_at_local_point((0, force), (0, -self.height/2))

    def _show(self, canvas):
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
    def __init__(self, radius, width, mass, position):
        r = radius # 0.05 # 3cm
        w = width # 0.03 # 2cm
        m = mass # 0.01 # 10 g
        self.radius = r
        self.width = w
        self.mass = m

        moment = 1/12 * m * (3*r**2 + w**2) 

        #self.slip_force = float("inf")
        self.slip_force = 60
        self.friction_force = 30

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
            rf_imp = copysign(min(self.friction_force*dt, abs(local_velocity.y)*0.01*m), -local_velocity.y)
            #wf_imp = rf_imp + copysign(sf_imp*0.1, local_velocity.y)

            body.apply_impulse_at_local_point((sf_imp, rf_imp))
            #body.angular_velocity *= 0.98
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
    def __init__(self, position,
            mass, radius, elasticity):
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
        self.shape.body.apply_impulse_at_local_point(force)

    def _show(self, canvas):
        self._cls(canvas)
        pos = cs.m_to_pd(self.shape.body.position)
        rad = cs.m_to_p(self.radius)
        self.on_screen = [canvas.create_oval(pos.x - rad, pos.y - rad,
                pos.x + rad, pos.y + rad, fill="green", width=2)]


class Walls(PGObject):
    def __init__(self, walls, thickness, elasticity):
        self._to_space = []
        self.on_screen = []

        self.s_walls = []
        for wall in walls:
            body = pymunk.Body(mass=0, moment=0,
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
                    canvas.create_line(*cs.m_to_pd(shape.a),
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
