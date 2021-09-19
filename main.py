#!/usr/bin/env python
import rabbyt
import pyglet
from pyglet import clock
import os.path

from cinc.windows import GameWindow

rabbyt.data_directory = os.path.dirname('.')



player = pyglet.media.Player()
player.volume = 0.5
player.eos_action = pyglet.media.Player.EOS_LOOP


def main():
    clock.schedule(rabbyt.add_time)
    GameWindow()
    rabbyt.set_default_attribs()
    if pyglet.media.have_avbin:
        music = pyglet.resource.media('data/music/m.ogg')
        player.queue(music)
        player.play()
    pyglet.app.run()


main()
