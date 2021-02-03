class Autobuild(object):
    """
    Mix-in class to force x, y, width, height structure of ctors. All Autobuild
    instances (objects that are built automatically by a TiledTileLayer with
    the property autobuild_objects=true) will have to abide to this ctor parameter
    structure.
    """

    def __init__(self, x, y, w, h, tile_w, tile_h):
        """
        :param int x: the x position of the Autobuild in tile units
        :param int y: the y position of the Autobuild in tile units
        :param int w: the width of the Autobuild in tile units
        :param int h: the height of the Autobuild in tile units
        :param int tile_w: the tile width of the layer
        :param int tile_h: the tile height of the layer
        """
        self.x_in_tiles = x
        self.y_in_tiles = y
        self.w_in_tiles = w
        self.h_in_tiles = h
        self.tile_w = tile_w
        self.tile_h = tile_h
