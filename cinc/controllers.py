import math
from random import random

import pyglet
from pyglet import clock

import rabbyt

from planar import Vec2

from cinc.rules import rules
from cinc import sounds


class BaseController(object):
    def __init__(self, window):
        self.free = []
        self.active = []
        self.window = window

        for i in xrange(self.get_count()):
            self.free.append(self.create())

    def create(self):
        raise NotImplementedError

    def get_count(self):
        raise NotImplementedError


class EnemyController(BaseController):

    def __init__(self, window):
        super(EnemyController, self).__init__(window)
        self.dying = []

    def create(self):
        en = self.window.create_sprite("enemy")
        return en

    def get_count(self):
        return 1200

    def die_all(self):
        for enemy in self.active:
            self.die(enemy)
        self.active = []

    def destroy(self, collided):
        if not collided:
            return
        for groups in collided:
            for item in groups:
                try: # TODO: maybe too slow, but works for now
                    self.active.remove(item) # throws ValueError if not from this controller
                    self.die(item)
                except ValueError:
                    pass

    def disc_destroy(self, pos, radius):
        radius2 = radius * radius
        to_remove = []
        for enemy in self.active:
            dist2 = (Vec2(*enemy.xy) - pos).length2
            if dist2 < radius2:
                to_remove.append(enemy)
        for enemy in to_remove:
            self.active.remove(enemy)
            self.die(enemy)

    def die(self, enemy):
        enemy.xy = list(enemy.xy) # Cheat to stop moving animation
        enemy.alpha = rabbyt.ease_out(0.8, 0.0, dt=1.5)
        enemy.red = rabbyt.ease_out(1.0, 0.0, dt=0.5)
        enemy.scale = rabbyt.lerp(end=enemy.scale * 2.0, dt=1.5)
        self.dying.append(enemy)
        on_end = lambda dt: self.finish_with(enemy)
        clock.schedule_once(on_end, 1.5)

    def finish_with(self, enemy):
        self.dying.remove(enemy)
        self.free.append(enemy)

    def generate(self):
        if not self.free:
            return

        angle = math.degrees(random() * math.pi * 2.0)

        start = self.window.get_point_on_edge(angle)
        player = Vec2(*self.window.player.xy)

        enemy = self.free.pop()
        enemy.alpha = 1.0
        enemy.red = 1.0
        enemy.scale = self.window.get_global_scale()
        norm = (player - start).normalized()
        end = start + norm * self.window.radius_length * 2.5
        enemy.xy = rabbyt.anims.lerp(start, end, dt=rules.enemy_speed)
        self.active.append(enemy)

    def proccess_out_of_bounds(self):
        center = self.window.cxy
        r2 = self.window.radius_length ** 2
        to_remove = []
        for enemy in self.active:
            pos = Vec2(*enemy.xy)
            if (center - pos).length2 > r2 + 20: # TODO: check if this number is good enougth
                to_remove.append(enemy)

        for enemy in to_remove:
            self.active.remove(enemy)
            self.free.append(enemy)


class BulletController(BaseController):

    def create(self):
        return self.window.create_sprite("bullet")

    def get_count(self):
        return 40

    def shoot(self):
        if not self.free:
            return

        player = self.window.player

        start = player.xy
        end = Vec2(0.0, self.window.radius_length * 2.0).rotated(player.rot) + start

        bullet = self.free.pop()
        bullet.xy = rabbyt.anims.lerp(start, end, dt=rules.bullet_speed)
        on_end = lambda dt: self.finish_with(bullet)
        clock.schedule_once(on_end, rules.bullet_speed)
        self.active.append(bullet)

        sounds.play('shoot', 0.6)

    def finish_with(self, bullet):
        self.active.remove(bullet)
        self.free.append(bullet)
