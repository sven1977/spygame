from spygame.sprites.sprite import Sprite
from spygame.tmx.autobuild import Autobuild


class Ladder(Sprite, Autobuild):
    """
    A Ladder object that actors can climb on.
    One-way-platform type: one cannot fall through the top of the ladder but does not collide with the rest (e.g. from below) of the ladder.
    A Ladder object does not have an image and is thus not(!) being rendered; the image of the ladder has to be integrated into a rendered TiledTileLayer.
    TiledTileLayers have the possibility to generate Ladder objects automatically from those tiles that are flagged with the type='ladder' property. In that
    case, the TiledTileLayer property 'build_ladders' (bool) has to be set to true.
    """

    def __init__(self, x, y, w, h, tile_w, tile_h):
        """
        :param int x: the x position of the Ladder in tile units
        :param int y: the y position of the Ladder in tile units
        :param int w: the width of the Ladder in tile units
        :param int h: the height of the Ladder in tile units
        :param int tile_w: the tile width of the layer
        :param int tile_h: the tile height of the layer
        """
        Autobuild.__init__(self, x, y, w, h, tile_w, tile_h)
        # Transform values here to make collision with ladder to only trigger when
        # player is relatively close to the x-center of the ladder.
        # - Make this a 2px wide vertical axis in the center of the ladder.
        x_px = (
            self.x_in_tiles * self.tile_w + int(self.w_in_tiles * self.tile_w / 2) - 1
        )
        y_px = self.y_in_tiles * self.tile_h

        # Call the Sprite ctor (now everything is in px).
        Sprite.__init__(
            self, x_px, y_px, width_height=(2, self.h_in_tiles * self.tile_h)
        )

        # Collision types.
        self.type = Sprite.get_type("ladder,dockable,one_way_platform")
        # Do not do any collisions.
        self.collision_mask = 0
