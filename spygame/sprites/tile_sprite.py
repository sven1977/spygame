from spygame.sprites.sprite import Sprite


class TileSprite(Sprite):
    """
    Class used by TiledTileLayer objects to have a means of representing single tiles in terms of Sprite objects
    (used for collision detector function).
    """

    def __init__(self, layer, pytmx_tiled_map, id_, tile_props, rect):
        """
        :param TiledTileLayer layer: the TiledTileLayer object to which this tile belongs
        :param pytmx.pytmx.TiledMap pytmx_tiled_map: the tmx tiled-map object to which this tile belongs
                                                     (useful to have to look up certain map-side properties, e.g. tilewidth/height)
        :param int id_: tthe ID of the tile in the layer
        :param dict tile_props: the properties dict of this tile (values already translated into python types)
        :param Union[pygame.Rect,None] rect: the pygame.Rect representing the position and size of the tile
        """
        super().__init__(rect.x, rect.y, width_height=(rect.width, rect.height))
        self.tiled_tile_layer = layer
        self.pytmx_tiled_map = pytmx_tiled_map
        self.tile = id_
        self.tile_x = self.rect.x // self.pytmx_tiled_map.tilewidth
        self.tile_y = self.rect.y // self.pytmx_tiled_map.tileheight
        self.tile_props = tile_props
        # add the `dockable` type to all tiles
        self.type |= Sprite.get_type("dockable")


class SlopedTileSprite(TileSprite):
    """
    a TileSprite that supports storing some temporary calculations about a slope in the tile and its relation to a Sprite that's currently colliding
    with the TileSprite
    - used by the PlatformerPhysics Component when detecting and handling slope collisions
    """

    def __init__(self, layer, pytmx_tiled_map, id_, tile_props, rect):
        """
        :param TiledTileLayer layer: the TiledTileLayer object to which this tile belongs
        :param pytmx.pytmx.TiledMap pytmx_tiled_map: the tmx tiled-map object to which this tile belongs
                                                     (useful to have to look up certain map-side properties, e.g. tilewidth/height)
        :param int id_: tthe ID of the tile in the layer
        :param dict tile_props: the properties dict of this tile (values already translated into python types)
        :param Union[pygame.Rect,None] rect: the pygame.Rect representing the position and size of the tile
        """
        super().__init__(layer, pytmx_tiled_map, id_, tile_props, rect)
        # slope properties of the tile
        self.slope = tile_props.get(
            "slope", None
        )  # the slope property of the tile in the tmx file (inverse steepness (1/m in y=mx+b) of the line that defines the slope)
        self.offset = tile_props.get(
            "offset", None
        )  # the offset property of the tile in the tmx file (in px (b in y=mx+b))
        self.is_full = (
            self.slope == 0.0 and self.offset == 1.0
        )  # is this a full collision tile?
        self.max_x = self.pytmx_tiled_map.tilewidth
        self.max_y = max(
            self.get_y(0), self.get_y(self.rect.width)
        )  # store our highest y-value (height of this tile)

    def get_y(self, x):
        """
        Calculates the y value (in normal cartesian y-direction (positive values on up axis)) for a given x-value.

        :param int x: the x-value (x=0 for left edge of tile x=tilewidth for right edge of tile)
        :return: the calculated y-value
        :rtype: int
        """
        # y = mx + b
        if self.slope is None or self.offset is None:
            return 0
        return self.slope * min(x, self.max_x) + self.offset * self.rect.height

    def sloped_xy_pull(self, sprite):
        """
        Applies a so-called xy-pull on a Sprite object moving in x-direction in this sloped tile.
        An xy-pull is a change in the y-coordinate because of the x-movement (sliding up/down a slope while moving left/right).

        :param Sprite sprite: the Sprite object that's moving on the slope
        """
        if self.slope == 0 or not self.slope:
            return
        # the local x value for the Sprite on the tile's internal x-axis (0=left edge of tile)
        x_local = max(
            0,
            (sprite.rect.left if self.slope < 0 else sprite.rect.right)
            - self.rect.left,
        )
        # the absolute y-position that we will force the sprite into
        y = self.rect.bottom - self.get_y(x_local) - sprite.rect.height
        sprite.move(None, y, True)
