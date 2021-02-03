from abc import ABCMeta, abstractmethod

from spygame.utils import defaults


class TmxLayer(object, metaclass=ABCMeta):
    """
    A wrapper class for the pytmx TiledObject class that can either represent a TiledTileLayer or a TiledObjectGroup.
    Needs to implement render and stores some spygame specific properties such as collision, render, etc.

    :param pytmx.pytmx.TiledElement tmx_layer_obj: the underlying pytmx TiledTileLayer
    :param pytmx.pytmx.TiledMap tmx_tiled_map: the underlying pytmx TiledMap object (representing the tmx file)
    """

    def __init__(self, tmx_layer_obj, tmx_tiled_map):
        self.pytmx_layer = tmx_layer_obj
        self.pytmx_tiled_map = tmx_tiled_map
        self.name = tmx_layer_obj.name
        properties = tmx_layer_obj.properties
        defaults(properties, {"do_render": "true", "render_order": 0})
        self.properties = properties

    @abstractmethod
    def render(self, display):
        raise NotImplementedError
