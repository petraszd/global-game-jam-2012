from random import random

from pyglet import clock

import rabbyt


class Dropout(object):
    def __init__(self, window):
        self.end_callback = window.remove_dropout
        self.center = window.cxy
        self.max_delta = window.radius_length
        self.dropout = window.create_sprite("drop")
        self.dropout.scale = rabbyt.lerp(start=0.0,
                                         end=window.get_global_scale(),
                                         dt=0.2)
        self.dropout_deco = window.create_sprite("drop_round")
        self.dropout_deco.scale = rabbyt.ease_out(start=100.0,
                                                  end=window.get_global_scale(),
                                                  dt=0.8)
        pos = self.get_random_pos()
        self.dropout.xy = pos
        self.dropout_deco.xy = pos

        self.prepare_for_end()

    def act(self, dt):
        self.dropout_deco.rot += 60.0 * dt

    def render(self):
        self.dropout.render()

    def render_hint(self):
        self.dropout_deco.render()

    def get_random_pos(self):
        x = (-0.5 + random()) * self.max_delta
        y = (-0.5 + random()) * self.max_delta
        return self.center + (x, y)

    def prepare_for_end(self):
        clock.schedule_once(self.dissapear, 2.0)

    def stop(self):
        clock.unschedule(self.remove_callback)
        clock.unschedule(self.dissapear)

    def remove_callback(self, dt):
        self.end_callback(self)

    def dissapear(self, dt):
        now = rabbyt.get_time()
        self.dropout.alpha = rabbyt.chain(rabbyt.ease_in(1.0, 0.0, dt=0.4),
                                          rabbyt.ease_in(0.0, 1.0, dt=0.4),
                                          rabbyt.ease_in(1.0, 0.0, dt=0.4),
                                          rabbyt.ease_in(0.0, 1.0, dt=0.4),
                                          rabbyt.ease_in(1.0, 0.0, dt=0.4))
        self.dropout_deco.alpha = rabbyt.ease_in(1.0, 0.0, startt=now + 1.6,
                                                 endt=now + 2.0)
        clock.schedule_once(self.remove_callback, 2.0)
