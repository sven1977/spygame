from abc import ABCMeta, abstractmethod
import numpy as np
import pygame

from spygame.components.component import Component
from spygame.game_loop import GameLoop
from spygame.utils import convert_type


class PhysicsComponent(Component, metaclass=ABCMeta):
    """
    Defines an abstract generic physics component that can be added to agents (or enemies) to behave in the world.
    GameObject's that own this Comonent may have a Brain component as well in order to steer behavior of the agent in `tick`.
    Needs to override `tick` and `collision`.
    """

    @staticmethod
    def tile_sprite_handler(tile_sprite_class, layer):
        """
        Populates the tile_sprites dict of a TiledTileLayer with tile_sprite_class (e.g. TileSprite or SlopedTileSprite) objects.

        :param TiledTileLayer layer: the TiledTileLayer, whose tiles we would like to process and store (each one) in the returned np.ndarray
        :param type tile_sprite_class: the TiledSprite subclass to use for generating TileSprite objects
        :return: a 2D np.ndarray (x,y) with the created TileSprite objects for each x/y coordinate (None if there is no tile at a position)
        :rtype: np.ndarray (2D)
        """
        # set up ndarray
        ret = np.ndarray(
            shape=(layer.pytmx_tiled_map.width, layer.pytmx_tiled_map.height),
            dtype=tile_sprite_class,
        )
        # loop through each tile and generate TileSprites
        for x, y, gid in layer.pytmx_layer.iter_data():
            # skip empty tiles (gid==0)
            if gid == 0:
                continue
            tile_props = layer.pytmx_tiled_map.get_tile_properties_by_gid(gid) or {}
            # go through dict and translate data types into proper python types ("true" -> bool, 0.0 -> float, etc..)
            # also keep autobuild kwargs in a separate dict
            look_for_autobuild = True if tile_props.get("autobuild_class") else False
            autobuild_kwargs = {}
            for key, value in tile_props.items():
                value = convert_type(value)
                # a special autobuild kwarg (for the autobuild c'tor)
                if look_for_autobuild and key[:2] == "P_":
                    autobuild_kwargs[key[2:]] = value
                else:
                    tile_props[key] = value

            if look_for_autobuild:
                tile_props["autobuild_kwargs"] = autobuild_kwargs

            ret[x, y] = tile_sprite_class(
                layer,
                layer.pytmx_tiled_map,
                gid,
                tile_props,
                pygame.Rect(
                    x * layer.pytmx_tiled_map.tilewidth,
                    y * layer.pytmx_tiled_map.tileheight,
                    layer.pytmx_tiled_map.tilewidth,
                    layer.pytmx_tiled_map.tileheight,
                ),
            )
        return ret

    # probably needs to be extended further by child classes
    def added(self):
        obj = self.game_object
        # handle collisions
        obj.on_event("collision", self, "collision", register=True)
        # flag the GameObject as "handles collisions itself"
        self.game_object.handles_own_collisions = True

    # may determine x/y-speeds and movements of the GameObject (gravity, etc..)
    @abstractmethod
    def tick(self, game_loop: GameLoop):
        """
        Needs to be called by the GameObject at some point during the GameObject's `tick` method.

        :param GameLoop game_loop: the currently playing GameLoop object
        """
        pass

    @abstractmethod
    def collision(self, col):
        """
        This is the resolver for a Collision that happened between two Sprites under this PhysicsComponent.

        :param Collision col: the Collision object describing the collision that already happened between two sprites
        """
        pass


class ControlledPhysicsComponent(PhysicsComponent, metaclass=ABCMeta):
    """
    When added to a GameObject, checks for an existing Brain Component and creates a property (self.game_obj_cmp_brain) for easy access.
    """

    def __init__(self, name="physics"):
        super().__init__(name)
        self.game_obj_cmp_brain = None  # the GameObject's HumanPlayerBrain component (used by Physics for steering and action control within `tick` method)

    def added(self):
        super().added()
        self.game_obj_cmp_brain = self.game_object.components.get("brain", None)

        # If there is a Component named `brain` in the GameObject it has to be of type Brain.
        from spygame.components.brains import Brain

        assert not self.game_obj_cmp_brain or isinstance(
            self.game_obj_cmp_brain, Brain
        ), "ERROR: {}'s `brain` Component is not of type Brain!".format(
            type(self.game_object).__name__
        )
