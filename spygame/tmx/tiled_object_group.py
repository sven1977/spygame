import pygame
import pytmx

from spygame.tmx.tmx_layer import TmxLayer
from spygame.utils import convert_type, get_kwargs_from_obj_props


class TiledObjectGroup(TmxLayer):
    """
    A wrapper class for the pytmx.TiledObjectGroup class, which represents an object layer in a tmx file.
    Generates all GameObjects specified in the layer (a.g. the agent, enemies, etc..).
    Implements `render` by looping through all GameObjects and rendering their Sprites one by one.
    """

    def __init__(
        self,
        pytmx_layer: pytmx.pytmx.TiledObjectGroup,
        pytmx_tiled_map: pytmx.pytmx.TiledMap,
    ):
        super().__init__(pytmx_layer, pytmx_tiled_map)

        # create the sprite group for this layer (all GameObjects will be added to this group)
        self.sprite_group = pygame.sprite.Group()

        # construct each object from the layer (as a Sprite) and add them to the sprite_group of this layer
        for obj in self.pytmx_layer:
            # allow objects in the tmx file to be 'switched-off' by making them invisible
            if not obj.visible:
                continue

            obj_props = obj.properties

            # if the (Sprite) class of the object is given, construct it here using its c'tor
            # - classes are given as strings: e.g. sypg.Sprite, vikings.Viking, Agent (Agent class would be in __main__ module)
            # - first look in the tile's properties for the 'class' field, only then try the 'type' field directly of the object (manually given by designer)
            class_global = obj_props.pop("class", None) or obj.type
            if class_global:
                ctor = convert_type(class_global, force_class=True)
                assert isinstance(
                    ctor, type
                ), "ERROR: python class `{}` for object in object-layer `{}` not defined!".format(
                    class_global, self.pytmx_layer.name
                )

                # get other kwargs for the Sprite's c'tor
                kwargs = get_kwargs_from_obj_props(obj_props)

                # generate the Sprite
                sprite = ctor(obj.x, obj.y, **kwargs)
                ## add the do_render and render_order to the new instance
                # sprite.do_render = (obj_props.get("do_render", "true") == "true")  # the default for objects is true
                # if sprite.do_render:
                #    sprite.render_order = int(obj_props.get("render_order", 50))  # the default for objects is 50
                self.sprite_group.add(sprite)

    def render(self, display):
        pass