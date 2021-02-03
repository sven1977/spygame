import pygame

from spygame import (
    DEBUG_FLAGS,
    DEBUG_DONT_RENDER_TILED_TILE_LAYERS,
    DEBUG_RENDER_COLLISION_TILES,
    DEBUG_RENDER_COLLISION_TILES_COLOR_DEFAULT,
)
from spygame.stage import Stage
from spygame.sprites.sprite import Sprite
from spygame.tmx.tmx_layer import TmxLayer


class TiledTileLayer(TmxLayer):
    """
    A wrapper class for pytmx.pytmx.TiledTileLayer, which represents a 'normal' tile layer in a tmx file.
    Reads in all tiles' images into one Surface object so we can render the entire layer at once.
    Implements `render`.
    """

    def __init__(self, pytmx_layer, pytmx_tiled_map, tile_sprite_handler):
        """
        :param pytmx.pytmx.TiledTileLayer pytmx_layer: the underlying pytmx TiledTileLayer
        :param pytmx.pytmx.TiledMap pytmx_tiled_map: the underlying pytmx TiledMap object (representing the tmx file)
        :param callable tile_sprite_handler: the callable that returns an ndarray, populated with TileSprite objects for storage in this layer
        """
        super().__init__(pytmx_layer, pytmx_tiled_map)

        self.type_str = self.properties.get("type", "none")
        self.type = 0
        # get type mask of this layer from `type` property
        for t in self.type_str.split(","):
            self.type |= Sprite.get_type(t)

        # an ndarray holding all single tiles (by x/y position) from this layer
        # non-existing tiles are not(!) stored in this ndarray and return None at the respective x/y position
        self.tile_sprites = tile_sprite_handler(self)

        # update do_render indicator depending on some debug settings
        self.do_render = (
            self.properties["do_render"] == "true"
            and not (DEBUG_FLAGS & DEBUG_DONT_RENDER_TILED_TILE_LAYERS)
        ) or (
            self.type != Sprite.get_type("none")
            and (DEBUG_FLAGS & DEBUG_RENDER_COLLISION_TILES)
        )
        self.render_order = int(self.properties["render_order"])

        # put this layer in one single Sprite that we can then blit on the display (with 'area=[some rect]' to avoid drawing the entire layer each time)
        self.pygame_sprite = None
        # we are rendering this layer, need to store entire image in this structure
        if self.do_render:
            self.pygame_sprite = self.build_sprite_surface()

    def build_sprite_surface(self):
        """
        Builds the image (pygame.Surface) for this tile layer based on all found tiles in the layer.
        """
        surf = pygame.Surface(
            (
                self.pytmx_layer.width * self.pytmx_tiled_map.tilewidth,
                self.pytmx_layer.height * self.pytmx_tiled_map.tileheight,
            ),
            flags=pygame.SRCALPHA,
        )
        # rendered collision layer
        if self.type != Sprite.get_type("none") and (
            DEBUG_FLAGS & DEBUG_RENDER_COLLISION_TILES
        ):
            # red for normal collisions, light-blue for touch collisions
            color = (
                DEBUG_RENDER_COLLISION_TILES_COLOR_DEFAULT
                if self.type & Sprite.get_type("default")
                else DEBUG_RENDER_COLLISION_TILES_COLOR_OTHER
            )
            for (x, y, image), (_, _, gid) in zip(
                self.pytmx_layer.tiles(), self.pytmx_layer.iter_data()
            ):
                surf.blit(
                    image.convert_alpha(),
                    (
                        x * self.pytmx_tiled_map.tilewidth,
                        y * self.pytmx_tiled_map.tileheight,
                    ),
                )
                tile_props = self.pytmx_tiled_map.get_tile_properties_by_gid(gid) or {}
                # normal collision tiles
                if not tile_props.get("no_collision"):
                    pygame.draw.rect(
                        surf,
                        color,
                        pygame.Rect(
                            (
                                x * self.pytmx_tiled_map.tilewidth,
                                y * self.pytmx_tiled_map.tileheight,
                            ),
                            (
                                self.pytmx_tiled_map.tilewidth,
                                self.pytmx_tiled_map.tileheight,
                            ),
                        ),
                        1,
                    )
        # "normal" layer (and no debug rendering)
        else:
            for x, y, image in self.pytmx_layer.tiles():
                surf.blit(
                    image.convert_alpha(),
                    (
                        x * self.pytmx_tiled_map.tilewidth,
                        y * self.pytmx_tiled_map.tileheight,
                    ),
                )

        pygame_sprite = pygame.sprite.Sprite()
        pygame_sprite.image = surf
        pygame_sprite.rect = surf.get_rect()
        return pygame_sprite

    def render(self, display):
        """
        Blits a part of our Sprite's image onto the Display's Surface using the Display's offset attributes.

        :param Display display: the Display object to render on
        """
        assert (
            self.do_render
        ), "ERROR: TiledTileLayer.render() called but self.do_render is False!"
        assert not isinstance(
            self.pygame_sprite, Sprite
        ), "ERROR: TiledTileLayer.render() called but self.pygame_sprite is not a Sprite!"
        r = pygame.Rect(
            self.pygame_sprite.rect
        )  # make a clone so we don't change the original Rect
        # apply the display offsets (camera)
        r.x += display.offsets[0]
        r.y += display.offsets[1]
        r.width = display.width
        r.height = display.height
        display.surface.blit(self.pygame_sprite.image, dest=(0, 0), area=r)

    def capture_autobuilds(self):
        """
        Captures all autobuild objects in this layer and returns them in a list of objects.
        Once an autobuild tile is found: searches neighboring tiles (starting to move right and down) for the same property and thus measures the object's
        width and height (in tiles).

        :return: list of generated autobuild objects
        :rtype: List[object]
        """
        objects = []
        # loop through each tile and look for ladder type property
        for y in range(self.pytmx_layer.height):
            for x in range(self.pytmx_layer.width):
                tile_sprite = self.tile_sprites[(x, y)]  # type: TileSprite
                if not tile_sprite:
                    continue
                props = tile_sprite.tile_props
                # we hit the upper left corner of an autobuild object -> spread out to find more neighboring similar tiles
                ctor = props.get("autobuild_class", False)
                if ctor:
                    assert isinstance(
                        ctor, type
                    ), "ERROR: translation of tile ({},{}) property `autobuild_class` did not yield a defined class!".format(
                        x, y
                    )
                    tile_left = self.tile_sprites[(x - 1, y)]  # type: TileSprite
                    tile_top = self.tile_sprites[(x, y - 1)]  # type: TileSprite
                    if (
                        tile_left
                        and tile_left.tile_props.get("autobuild_class") == ctor
                        or tile_top
                        and tile_top.tile_props.get("autobuild_class") == ctor
                    ):
                        continue
                    # measure width and height
                    w = 1
                    h = 1
                    x2 = x + 1
                    while True and x2 < self.pytmx_layer.width:
                        ts = self.tile_sprites[(x2, y)]
                        if not (ts and ts.tile_props.get("autobuild_class") == ctor):
                            break
                        w += 1
                        x2 += 1

                    y2 = y + 1
                    while True and y2 < self.pytmx_layer.height:
                        ts = self.tile_sprites[(x, y2)]
                        if not (ts and ts.tile_props.get("autobuild_class") == ctor):
                            break
                        h += 1
                        y2 += 1

                    # insert new object (all autobuild objects need to accept x, y, w, h in their constructors)
                    objects.append(
                        ctor(
                            x,
                            y,
                            w,
                            h,
                            self.pytmx_tiled_map.tilewidth,
                            self.pytmx_tiled_map.tileheight,
                            **props.get("autobuild_kwargs", {})
                        )
                    )
        return objects

    def get_overlapping_tiles(self, sprite):
        """
        Returns the tile boundaries (which tiles does the sprite overlap with?).

        :param Sprite sprite: the sprite to test against
        :return: a tuple of (start-x. end-x, start-y, end-y) tile-coordinates to consider as overlapping with the given Sprite
        :rtype: tuple
        """
        tile_start_x = min(
            max(0, sprite.rect.left // self.pytmx_tiled_map.tilewidth),
            self.pytmx_tiled_map.width - 1,
        )
        tile_end_x = max(
            0,
            min(
                self.pytmx_tiled_map.width - 1,
                (sprite.rect.right - 1) // self.pytmx_tiled_map.tilewidth,
            ),
        )
        tile_start_y = min(
            max(0, sprite.rect.top // self.pytmx_tiled_map.tileheight),
            self.pytmx_tiled_map.height - 1,
        )
        tile_end_y = max(
            0,
            min(
                self.pytmx_tiled_map.height - 1,
                (sprite.rect.bottom - 1) // self.pytmx_tiled_map.tileheight,
            ),
        )
        return tile_start_x, tile_end_x, tile_start_y, tile_end_y

    def collide_simple_with_sprite(self, sprite, collision_detector):
        """
        Collides a Sprite (that only obeys simple physics rules) with a TiledTileLayer and solves all detected collisions.
        The Sprite needs to have the properties vx and vy, which are interpreted as the Sprite's velocity.
        Ignores slopes.

        :param Sprite sprite: the Sprite to test for collisions against a TiledTileLayer
        :param callable collision_detector: the collision detector method to use (this is set in the Sprite's Stage's options)
        """
        tile_start_x, tile_end_x, tile_start_y, tile_end_y = self.get_overlapping_tiles(
            sprite
        )

        xy, v = Stage.estimate_sprite_direction(sprite)

        # very simple algo: look through tile list (in no particular order) and return first tile that collides
        # None if no colliding tile found
        for tile_x in range(tile_start_x, tile_end_x + 1):
            for tile_y in range(tile_start_y, tile_end_y + 1):
                tile_sprite = self.tile_sprites[tile_x, tile_y]
                if not tile_sprite:
                    continue
                col = collision_detector(
                    sprite,
                    tile_sprite,
                    collision_objects=None,
                    direction=xy,
                    direction_veloc=v,
                    original_pos=(sprite.rect.x, sprite.rect.y),
                )
                if col:
                    return col
        return None
