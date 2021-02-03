from abc import ABCMeta, abstractmethod
import functools
import pygame
import pytmx

from spygame.event_object import EventObject
from spygame.game_loop import GameLoop
from spygame.keyboard_inputs import KeyboardInputs
from spygame.stage import Stage
from spygame.utils import defaults


class Screen(EventObject, metaclass=ABCMeta):
    """
    A Screen object has a play and a done method that need to be implemented.
    The play method stages the Screen on a Stage.
    The done method can do some cleanup.
    """

    def __init__(self, name: str = "start", **kwargs):
        super().__init__()
        self.name = name
        self.id = kwargs.get("id", 0)  # type: int

        # handle keyboard inputs
        self.keyboard_inputs = kwargs.get(
            "keyboard_inputs", KeyboardInputs([])
        )  # type: KeyboardInputs
        # our Display object
        self.display = kwargs.get("display", None)  # type: Display
        self.max_fps = kwargs.get("max_fps", 60)  # type: float

    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def done(self):
        pass


class SimpleScreen(Screen):
    """
    A simple Screen that has support for labels and sprites (static images) shown on the screen.
    """

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.sprites = kwargs["sprites"] if "sprites" in kwargs else []
        # labels example: {x: Q.width / 2, y: 220, w: 150, label: "NEW GAME", color: "white", align: "left", weight: "900", size: 22, family: "Fixedsys"},
        self.labels = kwargs["labels"] if "labels" in kwargs else []
        ## TODO: audio? self.audio = kwargs["audio"] if "audio" in kwargs else []

    @staticmethod
    def screen_func(stage: Stage):
        """
        Defines this screen's Stage setup.
        Stage functions are used to setup a Stage (before playing it).

        :param Stage stage: the Stage to be setup
        """
        # get the Screen object (instance) from the options
        screen = stage.options["screen_obj"]

        from spygame.sprites.sprite import Sprite

        # insert labels to screen
        for label_def in screen.labels:
            # generate new Font object
            font = pygame.font.Font(None, label_def["size"])
            surf = font.render(label_def["text"], 1, pygame.Color(label_def["color"]))
            sprite = Sprite(label_def["x"], label_def["y"], surf)
            stage.add_sprite(sprite, "labels")

        # insert objects to screen
        for game_obj in screen.game_objects:
            stage.add_sprite(game_obj, "sprites")

    def play(self):
        """
        Plays the Screen.
        """

        # start screen (will overwrite the old 0-stage (=main-stage))
        # - also, will give our keyboard-input setup to the new GameLoop object
        Stage.stage_screen(self, SimpleScreen.screen_func, stage_idx=0)

    def done(self):
        print("we're done!")


class Level(Screen, metaclass=ABCMeta):
    """
    A Level class adds tmx file support to the Screen.
    TiledTileLayers (background, collision, foreground, etc..) as well as single Sprite objects can be defined in the tmx file.
    """

    def __init__(self, name: str = "test", **kwargs):
        super().__init__(name, **kwargs)

        # TODO: warn here if keyboard_inputs is given (should be given in tmx file exclusively)

        self.tmx_file = kwargs.get("tmx_file", "data/" + name.lower() + ".tmx")
        # load in the world's tmx file
        self.tmx_obj = pytmx.load_pygame(self.tmx_file)
        self.width = self.tmx_obj.width * self.tmx_obj.tilewidth
        self.height = self.tmx_obj.height * self.tmx_obj.tileheight

        self.register_event("mastered", "aborted", "lost")

        # get keyboard_inputs directly from the pytmx object
        if not self.keyboard_inputs:
            key_list = self.tmx_obj.properties.get("keyboard_inputs", "")
            assert (
                len(key_list) > 0
            ), "ERROR: tmx file needs a global map property `keyboard_inputs` such as e.g. `up,down,left,right`"
            descriptions = key_list.split(",")
            self.keyboard_inputs = KeyboardInputs(descriptions)

    # populates a Stage with this Level by going through the tmx file layer by layer and adding it
    # - unlike SimpleScreen, uses only the tmx file for adding things to the Stage
    @staticmethod
    def screen_func(stage):
        """
        Sets up the Stage by adding all layers (one-by-one) from the tmx file to the Stage.

        :param Stage stage:
        """
        assert isinstance(
            stage.screen, Level
        ), "ERROR: screen property of a Stage that uses Level.screen_func to stage a Screen must be a Level object!"

        # force add the default physics functions to the Stage's options

        from spygame.components.viewport import Viewport
        from spygame.physics.collision_algorithms import AABBCollision
        from spygame.physics.physics_component import PhysicsComponent
        from spygame.sprites.tile_sprite import TileSprite
        defaults(
            stage.options,
            {
                "components": [Viewport(stage.screen.display)],
                "physics_collision_detector": AABBCollision.collide,
                "tile_sprite_handler": functools.partial(
                    PhysicsComponent.tile_sprite_handler, TileSprite
                ),
            },
        )
        for layer in stage.screen.tmx_obj.layers:
            stage.add_tiled_layer(layer, stage.screen.tmx_obj)

    def play(self):
        """
        Start level (stage the scene; will overwrite the old 0-stage (=main-stage)).
        The options-object below will be also stored in [Stage object].options.
        Child Level classes only need to do these three things: a) stage a screen, b) register some possible events, c) play a new game loop.
        """
        from spygame.physics.physics_component import PhysicsComponent
        from spygame.sprites.tile_sprite import TileSprite
        Stage.stage_screen(
            self,
            None,
            stage_idx=0,
            options={
                "tile_sprite_handler": functools.partial(
                    PhysicsComponent.tile_sprite_handler, TileSprite
                ),
                # "components": [Viewport(self.display)]
            },
        )

        # activate level triggers
        self.on_event("agent_reached_exit", self, "done", register=True)
        # play a new GameLoop giving it some options
        GameLoop.play_a_loop(screen_obj=self)

    def done(self):
        Stage.get_stage().stop()

        # switch off keyboard
        self.keyboard_inputs.update_keys([])  # empty list -> no more keys
