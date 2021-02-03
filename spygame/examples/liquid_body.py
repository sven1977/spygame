from spygame.sprites.sprite import Sprite
from spygame.tmx.autobuild import Autobuild


class LiquidBody(Sprite, Autobuild):
    """
    A LiquidBody object (quicksand, water, etc..) that an actor will sink into and die. The AIBrain of enemies will avoid stepping into such an object.
    """

    def __init__(self, x, y, w, h, tile_w, tile_h, description="quicksand"):
        """
        :param int x: the x position of the Ladder in tile units
        :param int y: the y position of the Ladder in tile units
        :param int w: the width of the Ladder in tile units
        :param int h: the height of the Ladder in tile units
        :param int tile_w: the tile width of the layer
        :param int tile_h: the tile height of the layer
        """
        Autobuild.__init__(self, x, y, w, h, tile_w, tile_h)
        # make the liquid object a little lower than the actual tiles (especially at the top assuming that the top is done with tiles only showing
        # the very shallow surface of the liquid body)
        x_px = self.x_in_tiles * self.tile_w
        y_px = self.y_in_tiles * self.tile_h + int(self.tile_h * 0.9)

        # call the Sprite ctor (now everything is in px)
        Sprite.__init__(
            self,
            x_px,
            y_px,
            width_height=(
                self.w_in_tiles * self.tile_w,
                self.h_in_tiles * self.tile_h - int(self.tile_h * 0.9),
            ),
        )

        # can be used to distinguish between different types of liquids (water, quicksand, lava, etc..)
        self.description = description

        # collision types
        self.type = Sprite.get_type("liquid")
        self.collision_mask = 0  # do not do any collisions
