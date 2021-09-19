import math
from random import random

import pyglet
from pyglet.window import Window
from pyglet import clock
from pyglet.window import key

import rabbyt
from rabbyt.collisions import collide_groups, collide_single

from planar import Vec2

from cinc.controllers import BulletController, EnemyController
from cinc.dropout import Dropout
from cinc.rules import rules
from cinc.levels import levels
from cinc import sounds


class GameWindow(Window):

    REAL_DIM = 708
    STAGE_DIM = 760 # For padding
    PLAYER_PADDING = 25
    KILLER_RADIUS = 250

    STATE_START = 1
    STATE_STOP = 2
    STATE_PLAYING = 3

    def __init__(self):
        args = {'width': 800,
                'height': 600}
        #args = {'fullscreen': True}
        super(GameWindow, self).__init__(**args)
        self.radius_length = self.get_radius_length()

        self.start_screen = self.create_sprite("start_screen")
        self.end_screen = self.create_sprite("end_screen")
        self.back = self.create_sprite("back")
        self.back_shadow = self.create_sprite("back_shadow")
        self.player = self.create_sprite("player")
        self.player_bounds = self.create_sprite("player_bounds")
        self.head = self.create_sprite("head")

        self.prepare_text = self.create_sprite("prepare_text")
        self.prepare_text.alpha = 0.0
        self.prepare_text.y += self.get_global_scale() * 60

        #self.fps = clock.ClockDisplay()

        self.bullets = BulletController(self)
        self.enemies = EnemyController(self)

        self.is_in_killer = False
        self.killer_disc = self.create_sprite("killer_disc")
        self.killer_disc.alpha = 0.0

        self.disc_count = 0

        self.motionl = False
        self.motionr = False
        self.motionu = False
        self.motiond = False

        self.dropouts = []

        self.timer_text = pyglet.text.Label('Time: 0.0 s.',
                                            x=self.width - 20,
                                            y=self.height - 20,
                                            anchor_x='right',
                                            anchor_y='top',
                                            color=(255, 255, 255, 180),
                                            font_size=14 * self.get_global_scale(),
                                            font_name="Liberation Mono")
        self.end_text = pyglet.text.Label('Your time is: 0.0 s.',
                                          x=self.width / 2,
                                          y=self.height / 2,
                                          anchor_x='center',
                                          anchor_y='center',
                                          color=(255, 255, 255, 180),
                                          font_size=24 * self.get_global_scale(),
                                          font_name="Liberation Mono")

        self.mouse_pos = Vec2(0, 0)
        self.hider = self.create_sprite("hider")
        self.current_level_index = 0
        self.init_level()

        self.state = self.STATE_START

        self.start_time = rabbyt.get_time()


    def init_level(self):
        if self.current_level_index != 0:
            self.prepare_text.alpha = rabbyt.chain(rabbyt.lerp(0.0, 0.3, dt=0.8),
                                                   rabbyt.ease_in(0.3, 0.0, dt=0.8))
        self.get_level().start()

    def get_level(self):
        len_levels = len(levels)
        if len_levels <= self.current_level_index:
            for i in xrange(self.current_level_index - len_levels + 1):
                levels.append(levels[-1].next_std_level())
        return levels[self.current_level_index]

    def init_schedulers(self):
        def enemy_gen(dt):
            if self.state == self.STATE_PLAYING:
                clock.schedule_interval(self.on_generate_enemy,
                                        rules.enemy_generation_speed) # TODO: real timer
        clock.schedule_once(enemy_gen, 2.0)
        clock.schedule(self.on_clock)
        clock.schedule_interval(self.clear_out_of_bounds, 3.0)
        clock.schedule_once(self.on_generate_dropout,
                            self.get_dropout_delta())
        clock.schedule_once(self.on_next_level, 11.0)

    def on_next_level(self, dt):
        self.current_level_index += 1
        self.init_level()
        #self.enemies.die_all()
        self.stop_schedulers()
        self.init_schedulers()

    def get_dropout_delta(self):
        return rules.dropout_generation_cons_pause + random() * rules.dropout_generation_rand_pause

    def on_generate_dropout(self, dt):
        self.dropouts.append(Dropout(self))
        sounds.play('drop', 0.4)
        clock.schedule_once(self.on_generate_dropout,
                            self.get_dropout_delta())


    def stop_schedulers(self):
        clock.unschedule(self.on_generate_enemy)
        clock.unschedule(self.on_clock)
        clock.unschedule(self.clear_out_of_bounds)
        clock.unschedule(self.on_generate_dropout)
        clock.unschedule(self.on_next_level)

    def create_sprite(self, name, pos=None):
        sprite = rabbyt.Sprite("data/images/{0}.png".format(name))
        if pos is None:
            sprite.xy = self.cxy
        else:
            sprite.xy = pos
        sprite.scale = self.get_global_scale()
        return sprite

    def get_point_on_edge(self, angle):
        return self.cxy + Vec2(0.0, 1.0).rotated(angle) * self.radius_length

    def get_center(self):
        return Vec2(self.get_center_x(), self.get_center_y())
    cxy = property(get_center)

    def get_center_x(self):
        return self.width / 2
    cx = property(get_center_x)

    def get_radius_length(self):
        return self.REAL_DIM * self.get_global_scale() * 0.5

    def get_center_y(self):
        return self.height / 2
    cy = property(get_center_y)

    def get_global_scale(self):
        sw = self.width / float(self.STAGE_DIM)
        sh = self.height / float(self.STAGE_DIM)
        return min(sw, sh)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_pos = Vec2(x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_pos = Vec2(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == self.STATE_START:
            self.start_playing()
            return
        if self.state == self.STATE_PLAYING:
            clock.schedule_interval(self.on_shoot_bullet,
                                    rules.bullet_shooting_speed)

    def on_mouse_release(self, x, y, button, modifiers):
        clock.unschedule(self.on_shoot_bullet)

    def on_key_press(self, symbol, modifiers):
        if self.state == self.STATE_START:
            self.start_playing()
            return

        if symbol == key.ENTER and self.state == self.STATE_STOP:
            self.start_playing()
            return

        if symbol == key.A:
            self.motionl = True
        elif symbol == key.D:
            self.motionr = True
        elif symbol == key.W:
            self.motionu = True
        elif symbol == key.S:
            self.motiond = True
        elif symbol == key.SPACE and self.disc_count > 0:
            self.disc_count -= 1

            self.is_in_killer = True
            sounds.play('disc')
            self.killer_disc.scale = rabbyt.ease_out(start=0.0,
                                                     end=self.get_global_scale(), dt=0.06)
            self.killer_disc.alpha = rabbyt.ease_in(start=1.0, end=0.0,
                                                    startt=rabbyt.get_time() + 0.2,
                                                    endt=rabbyt.get_time() + 0.4)
            def callback(dt):
                self.is_in_killer = False
            clock.schedule_once(callback, 0.1)

        return super(GameWindow, self).on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.A:
            self.motionl = False
        elif symbol == key.D:
            self.motionr = False
        elif symbol == key.W:
            self.motionu = False
        elif symbol == key.S:
            self.motiond = False

    def start_playing(self):
        self.state = self.STATE_PLAYING
        self.start_time = rabbyt.get_time()
        self.player.xy = self.cxy
        self.player.alpha = 1.0
        self.disc_count = 0
        self.dropouts = []
        self.current_level_index = 0
        self.init_level()
        self.init_schedulers()

    def rotate_player(self):
        delta = self.mouse_pos - self.player.xy
        angle = math.degrees(math.atan2(-delta[0], delta[1]))
        self.player.rot = angle

    def on_draw(self):
        if self.state == self.STATE_START:
            self.draw_state_start()
            return

        self.draw_state_playing()
        if self.state == self.STATE_STOP:
            self.draw_state_stop()

    def draw_state_stop(self):
        self.end_screen.render()
        self.end_text.draw()

    def draw_state_start(self):
        self.start_screen.render()

    def draw_state_playing(self):
        rabbyt.clear((0, 0, 0))
        self.back.render()
        self.draw_content()
        self.draw_hider()
        self.back_shadow.render()
        self.render_discs()

        self.prepare_text.render()
        if self.state == self.STATE_PLAYING:
            self.timer_text.draw()

        #self.fps.draw()

    def draw_hider(self):
        # Increadable peace of code
        deltax = (self.width - self.REAL_DIM * self.get_global_scale())
        deltay = (self.height - self.REAL_DIM * self.get_global_scale())

        self.hider.xy = (-deltax / 2.0 + 1, 0.0)
        self.hider.scale_x = deltax
        self.hider.scale_y = self.height
        self.hider.render()

        self.hider.x = 1.5 * deltax + self.REAL_DIM * self.get_global_scale() - 1.0
        self.hider.render()

        self.hider.xy = (0.0, -deltay / 2.0 + 1)
        self.hider.scale_x = self.width
        self.hider.scale_y = deltay
        self.hider.render()

        self.hider.y = 1.5 * deltay + self.REAL_DIM * self.get_global_scale() - 1.0
        self.hider.render()


    def render_discs(self):
        rot_backup = self.head.rot
        for i in xrange(self.disc_count):
            self.head.render()
            self.head.rot -= 10.0
        self.head.rot = rot_backup

    def on_shoot_bullet(self, dt):
        self.bullets.shoot()

    def draw_content(self):
        for d in self.dropouts:
            d.render()
        rabbyt.render_unsorted(self.bullets.active)
        rabbyt.render_unsorted(self.enemies.active)
        rabbyt.render_unsorted(self.enemies.dying)
        self.player.render()
        self.killer_disc.render()
        for d in self.dropouts:
            d.render_hint()

    def on_generate_enemy(self, dt):
        self.enemies.generate()

    def on_clock(self, dt):
        direction = Vec2(0.0, 0.0)
        if self.motionl:
            direction += Vec2(-1.0, 0.0)
        if self.motionr:
            direction += Vec2(1.0, 0.0)
        if self.motionu:
            direction += Vec2(0.0, 1.0)
        if self.motiond:
            direction += Vec2(0.0, -1.0)

        prevpos = self.player.xy
        speed = rules.player_speed * self.get_global_scale() * dt
        deltaxy = direction * speed
        self.player.x += deltaxy.x
        self.player.y += deltaxy.y

        padding = self.PLAYER_PADDING * self.get_global_scale()
        if Vec2(*(-self.cxy + self.player.xy)).length > self.radius_length - padding:
            self.player.xy = prevpos

        self.player_bounds.xy = self.player.xy
        self.killer_disc.xy = self.player.xy
        self.head.rot += dt * 10.0

        self.timer_text.text = 'Time: {0:.1f} s.'.format(rabbyt.get_time() - self.start_time)

        for d in self.dropouts:
            d.act(dt)

        self.rotate_player()
        self.clear_enemies()
        if self.is_in_killer:
            self.kill_with_disc()
        self.check_for_dropout()
        self.check_for_end()

    def remove_dropout(self, dropout):
        try:
            self.dropouts.remove(dropout)
        except ValueError:
            pass # It has been deleted at the end of game

    def clear_enemies(self):
        collided = collide_groups(self.bullets.active, self.enemies.active)
        self.enemies.destroy(collided)

    def clear_out_of_bounds(self, dt):
        self.enemies.proccess_out_of_bounds()

    def check_for_end(self):
        collided = collide_single(self.player_bounds, self.enemies.active)
        if not collided:
            return

        self.stop_schedulers()
        self.enemies.die_all()
        self.player.alpha = 0.4
        self.state = self.STATE_STOP

        end_time = rabbyt.get_time()
        delta_time = end_time - self.start_time
        self.end_text.text = 'Your time is: {0:.1f} s.'.format(delta_time)
        sounds.play('end', 1.2)

    def check_for_dropout(self):
        check_with = (d.dropout for d in self.dropouts)
        collided = collide_single(self.player_bounds, check_with)
        if not collided:
            return

        # Yeah -- this is plain stupid, but I do not care
        to_remove = []
        for col in collided:
            for d in self.dropouts:
                if col == d.dropout:
                    to_remove.append(d)
        for d in to_remove:
            d.stop()
            self.dropouts.remove(d)
            self.add_disc()

    def add_disc(self):
        self.disc_count += 1

    def kill_with_disc(self):
        kl = self.killer_disc
        radius = self.KILLER_RADIUS * self.get_global_scale()
        self.enemies.disc_destroy(Vec2(*kl.xy), radius)
