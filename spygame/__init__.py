# --------------------------------------------------------------
#
# spygame (pygame based 2D game engine)
#
# created: 2017/04/04 in PyCharm
# (c) 2017-2021 Sven Mika
#
# --------------------------------------------------------------

import pygame

VERSION_ = "0.2"
RELEASE_ = "0.2a0"

# Some debug flags that we can set to switch on debug rendering, collision
# handling, etc..
DEBUG_NONE = 0x0  # no debugging
DEBUG_ALL = 0xffff  # full debugging
# Will not render TiledTileLayers that are marked as 'do_render'==true in the
# tmx files.
DEBUG_DONT_RENDER_TILED_TILE_LAYERS = 0x1
# Will render all collision tiles (those layers that have a type) with a square
# frame and - when being considered - filled green.
DEBUG_RENDER_COLLISION_TILES = 0x2
DEBUG_RENDER_COLLISION_TILES_COLOR_DEFAULT = pygame.Color("red")
DEBUG_RENDER_COLLISION_TILES_COLOR_OTHER = pygame.Color("cyan")
# Render the tiles currently under consideration for colliding with a sprite.
DEBUG_RENDER_ACTIVE_COLLISION_TILES = 0x4
DEBUG_RENDER_ACTIVE_COLLISION_TILES_COLOR = pygame.Color("green")
DEBUG_RENDER_ACTIVE_COLLISION_TILES_COLOR_GREYED_OUT = pygame.Color("grey")
# Will render all Sprites (even those without an image (e.g. when blinking)
# with a rectangular frame representing the Sprite's .rect property
DEBUG_RENDER_SPRITES_RECTS = 0x8
DEBUG_RENDER_SPRITES_RECTS_COLOR = pygame.Color("orange")
# Will render every Sprite before the Sprite's tick method was called.
DEBUG_RENDER_SPRITES_BEFORE_EACH_TICK = 0x10
DEBUG_RENDER_SPRITES_AFTER_EACH_TICK = 0x20
# Will render every Sprite before the Sprite's collision detection algo runs.
DEBUG_RENDER_SPRITES_BEFORE_COLLISION_DETECTION = 0x40

# By default, no debugging (you can set this through a Game's c'tor using the
# debug_flags kwarg).
DEBUG_FLAGS = DEBUG_NONE
