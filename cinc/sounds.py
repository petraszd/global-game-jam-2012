import pyglet


def play(name, volume=1.0):
    if pyglet.media.have_avbin:
        fullname = 'data/sounds/{0}.ogg'.format(name)
        pyglet.resource.media(fullname).play().volume = volume
