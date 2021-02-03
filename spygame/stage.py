import pygame
import pytmx

from spygame import (
    DEBUG_FLAGS,
    DEBUG_RENDER_SPRITES_AFTER_EACH_TICK,
    DEBUG_RENDER_SPRITES_BEFORE_EACH_TICK,
    DEBUG_RENDER_SPRITES_RECTS,
    DEBUG_RENDER_SPRITES_RECTS_COLOR,
)
from spygame.game_loop import GameLoop
from spygame.game_object import GameObject
from spygame.physics.collision_algorithms import AABBCollision
from spygame.utils import defaults


class Stage(GameObject):
    """
    A Stage is a container class for Sprites sorted by pygame.sprite.Groups and TiledTileLayers.
    Sprites within a Stage can collide with each other or with the TiledTileLayers in the Stage.
    Sprites and TiledTileLayers that are to be rendered are stored sorted by their render_order property (lowest renders first).
    """

    # list of all Stages
    max_stages = 10
    stages = [None for x in range(max_stages)]
    active_stage = 0  # the currently ticked/rendered Stage

    @staticmethod
    def stage_default_game_loop_callback(game_loop: GameLoop):
        """
        The default game loop callback to use if none is given when staging a Scene.
        Order: Clamps dt (to avoid extreme values), ticks all stages, renders all stages, updates the pygame.display

        :param GameLoop game_loop: the currently playing (active) GameLoop
        """
        # clamp dt
        if game_loop.dt < 0:
            game_loop.dt = 1.0 / 60
        elif game_loop.dt > 1.0 / 15:
            game_loop.dt = 1.0 / 15

        # tick all Stages
        for i, stage in enumerate(Stage.stages):
            Stage.active_stage = i
            if stage:
                stage.tick(game_loop)

        # render all Stages and refresh the pygame.display
        Stage.render_stages(game_loop.display, refresh_after_render=True)

        Stage.active_stage = 0

    @staticmethod
    def render_stages(display, refresh_after_render=False):
        """
        Loops through all Stages and renders all of them.

        :param Display display: Display object on which to render
        :param bool refresh_after_render: do we refresh the pygame.display after all Stages have been called with `render`?
        """
        # black out display (really necessary? I think so)
        display.surface.fill(pygame.Color("#000000"))
        # call render on all Stages
        for i, stage in enumerate(Stage.stages):
            Stage.active_stage = i
            if stage:
                stage.render(display)
        # for debugging purposes
        if refresh_after_render:
            pygame.display.flip()

    @staticmethod
    def clear_stage(idx):
        """
        Clears one of the Stage objects by index.

        :param int idx: the index of the Stage to clear (index==slot in static Stage.stages list)
        """
        if Stage.stages[idx]:
            Stage.stages[idx].destroy()
            Stage.stages[idx] = None

    @staticmethod
    def clear_stages():
        """
        Clears all our Stage objects.
        """
        for i in range(len(Stage.stages)):
            Stage.clear_stage(i)

    @staticmethod
    def get_stage(idx=0):
        """
        Returns the Stage at the given index (returns None if none found).

        :param Union[int,None] idx: the index of the Stage to return (0=default Stage)
        :return: the Stage object at the given index or None if there is no Stage at that index
        :rtype: Union[Stage,None]
        """
        if idx is None:
            idx = Stage.active_stage
        return Stage.stages[idx]

    @staticmethod
    def stage_screen(screen, screen_func=None, stage_idx=None, options=None):
        """
        Supported options are (if not given, we take some of them from given Screen object, instead):
        - stage_idx (int): sets the stage index to use (0-9)
        - stage_class (class): sets the class (must be a Stage class) to be used when creating the new Stage
        - force_loop (bool): if set to True and we currently have a GameLoop running, stop the current GameLoop and replace it with a new one, which has
        to be given via the "game_loop" option (as GameLoop object, or as string "new" for a default GameLoop)
        - keyboard_inputs (KeyboardInputs): the KeyboardInputs object to use for the new GameLoop
        - display (Display): the Display to use for the new GameLoop
        - components (List[Component]): a list of Component objects to add to the new Stage (e.g. a Viewport)

        :param Screen screen: the Screen object to set up on a certain stage
        :param callable screen_func: the function to use to set up the Stage (before playing it)
        :param int stage_idx: the Stage index to use (0=default Stage)
        :param dict options: options to be used when instantiating the Stage
        :return: the new Stage object
        :rtype: Stage
        """
        if options is None:
            options = {}

        defaults(options, {"stage_class": Stage})

        # figure out which stage to use
        stage_idx = (
            stage_idx
            if stage_idx is not None
            else (options["stage_idx"] if "stage_idx" in options else 0)
        )

        # clean up an existing stage if necessary
        Stage.clear_stage(stage_idx)

        # create a new Stage and make this this the active stage
        stage = Stage.stages[stage_idx] = options["stage_class"](screen, options)
        Stage.active_stage = stage_idx

        # setup the Stage via the screen_fun (passing it the newly created Stage)
        if not screen_func:
            screen_func = screen.screen_func

        screen_func(stage)
        Stage.active_stage = 0

        # finally return the stage to the user for use if needed
        return stage

    def __init__(self, screen, options=None):
        """
        :param Screen screen: the Stage's Screen object (a Screen determines which elements (layers and sprites) go on the Stage)
        :param dict options: the options ruling the behavior of this Stage. options can be:
         components (list): a list of components to add to this Stage during construction (usually, a Viewport gets added)
         tile_sprite_handler (callable): a method taking a TiledTileLayer and returning an ndarray (tile-x/y position) of TileSprite objects (None if tile is
          empty)
         physics_collision_detector (callable): a method to use to detect a possible collision between two Sprites (defaults to AABBCollision.collide)
         tick_sprites_in_range_only (bool): if set to True (default), we will not tick those Sprite objects that are currently outside a) our Viewport
          component or b) outside the display
        """
        super().__init__()
        self.screen = screen  # the screen object associated with this Stage
        self.tiled_tile_layers = {}  # TiledLayer objects by name
        self.tiled_object_groups = {}  # TiledObjectGroup objects by name
        self.to_render = (
            []
        )  # list of all layers and sprites by name (TiledTileLayers AND Sprites) in the order in which they have to be rendered

        # dict of pygame.sprite.Group objects (by name) that contain Sprites (each TiledObjectGroup results in one Group)
        # - the name of the group is always the name of the TiledObjectGroup in the tmx file
        self.sprite_groups = {}
        self.sprites = []  # a plain list of all Sprites in this Stage

        from spygame.sprites.sprite import Sprite

        # Used to do test collisions on a Stage.
        self.locate_obj = Sprite(0, 0, width_height=(0, 0))

        # Sprites to be removed from the Stage (only remove when Stage gets ticked).
        self.remove_list = []

        defaults(
            options,
            {
                "physics_collision_detector": AABBCollision.collide,
                "tick_sprites_in_range_only": True,
                "tick_sprites_n_more_frames": 500,
            },
        )
        self.options = options

        self.is_paused = False
        self.is_hidden = False

        # Register events that we will trigger.
        self.register_event(
            "destroyed",
            "added_to_stage",
            "removed_from_stage",  # Sprites added/removed to/from us
            "pre_ticks",
            "pre_collisions",  # before we tick all Sprites, before we analyse all Sprites for collisions
            "post_tick",  # after we ticked all Sprites
            "pre_render",
            "post_render",  # before/after we render all our layers
        )

        # add Components to this Stage (given in options)
        self.cmp_viewport = None  # type: Union[Viewport,None]
        if "components" in self.options:
            from spygame.components.component import Component

            for comp in self.options["components"]:
                assert isinstance(
                    comp, Component
                ), "ERROR: one of the given components in Stage's c'tor (options['components']) is not of type Component!"
                self.add_component(comp)
                if comp.name == "viewport":
                    self.cmp_viewport = comp

        # store the viewable range Rect
        self.respect_viewable_range = (
            self.cmp_viewport and self.options["tick_sprites_in_range_only"]
        )
        self.viewable_rect = pygame.Rect(
            0, 0, self.screen.display.width, self.screen.display.height
        )

        # make sure our destroyed method is called when the stage is destroyed
        self.on_event("destroyed")

    def destroyed(self):
        self.invoke("debind_events")

    def for_each(self, callback, params=None):
        """
        Calls the given callback function for each sprite, each time passing it the sprite itself and \*params.

        :param callable callback: the callback to call for each sprite in the Stage
        :param any params: the params to pass as second/third/etc.. parameter to the callback
        """
        if not params:
            params = []
        for sprite in self.sprites:
            callback(sprite, *params)

    def invoke(self, func_name, params=None):
        """
        Calls a function on all of the GameObjects on this Stage.

        :param str func_name: the function name to call on all our GameObjects using getattr
        :param Union[list,None] params: the \*args passed to that function
        """
        if not params:
            params = []
        for sprite in self.sprites:
            func = getattr(sprite, func_name, None)
            if callable(func):
                func(*params)

    def detect(self, detector, params=None):
        """
        Returns the first GameObject in this Stage that - when passed to the detector function with params - returns True.

        :param callable detector: a function that returns a bool
        :param list params: the list of positional args that are passed to the detector
        :return: the first GameObject in this Stage that - when passed to the detector function with params - returns True
        :rtype: Union[Sprite,None]
        """
        if not params:
            params = []
        for sprite in self.sprites:
            if detector(sprite, *params):
                return sprite

    def locate(
        self,
        x,
        y,
        w=1,
        h=1,
        type_=None,
        collision_mask=None,
    ):
        """
        Returns the first Collision found by colliding the given measurements (Rect) against this Stage's objects.
        Starts with all TiledTileLayer objects, then all other Sprites.

        :param int x: the x-coordinate of the Rect to check
        :param int y: the y-coordinate of the Rect to check
        :param int w: the width of the Rect to check
        :param int h: the height of the Rect to check
        :param int type_: the type of the Rect (has to match collision_mask of Stage's objects)
        :param int collision_mask: the collision mask of the Rect (only layers and Sprites that match this mask are checked)
        :return: the first Collision encountered
        :rtype: Union[Collision,None]
        """
        from spygame.sprites.sprite import Sprite

        obj = self.locate_obj
        obj.rect.x = x
        obj.rect.y = y
        obj.rect.width = w
        obj.rect.height = h
        obj.type = type_ or Sprite.get_type("default")
        obj.collision_mask = collision_mask or Sprite.get_type("default")

        if DEBUG_FLAGS & DEBUG_RENDER_SPRITES_RECTS:
            pygame.draw.rect(
                self.screen.display.surface,
                DEBUG_RENDER_SPRITES_RECTS_COLOR,
                pygame.Rect(
                    (
                        obj.rect.x - self.screen.display.offsets[0],
                        obj.rect.y - self.screen.display.offsets[1],
                    ),
                    (obj.rect.w, obj.rect.h),
                ),
                1,
            )
            GameLoop.active_loop.display.debug_refresh()

        # collide with all matching tile layers
        for tiled_tile_layer in self.tiled_tile_layers.values():
            if obj.collision_mask & tiled_tile_layer.type:
                col = tiled_tile_layer.collide_simple_with_sprite(
                    obj, self.options["physics_collision_detector"]
                )
                # don't solve -> just return
                if col:
                    return col

        # collide with all Sprites (only if both collision masks match each others types)
        for sprite in self.sprites:
            if obj.collision_mask & sprite.type and sprite.collision_mask & obj.type:
                col = self.options["physics_collision_detector"](obj, sprite)
                if col:
                    return col
        # nothing found
        return None

    def add_tiled_layer(self, pytmx_layer, pytmx_tiled_map):
        """
        Adds a pytmx.TiledElement to the Stage with all its tiles or objects.
        The TiledElement could either be converted into a TiledTileLayer or a TiledObjectGroup (these objects are generated in this function based on the
        pytmx equivalent being passed in).

        :param pytmx.pytmx.TiledElement pytmx_layer: the original pytmx object to derive our TiledTileLayer or TileObjectGroup from
        :param pytmx.pytmx.TiledMap pytmx_tiled_map: the original pytmx TiledMap object (the tmx file) to which this layer belongs
        """
        # a TiledObjectGroup ("Object Layer" in the tmx file)
        if isinstance(pytmx_layer, pytmx.pytmx.TiledObjectGroup):
            assert (
                pytmx_layer.name not in self.tiled_object_groups
            ), "ERROR: TiledObjectGroup with name {} already exists in Stage!".format(
                pytmx_layer.name
            )
            from spygame.tmx.tiled_object_group import TiledObjectGroup

            l = TiledObjectGroup(pytmx_layer, pytmx_tiled_map)
            self.add_tiled_object_group(l)

        # a TiledTileLayer ("Tile Layer" in the tmx file)
        elif isinstance(pytmx_layer, pytmx.pytmx.TiledTileLayer):
            assert (
                pytmx_layer.name not in self.tiled_tile_layers
            ), "ERROR: TiledTileLayer with name {} already exists in Stage!".format(
                pytmx_layer.name
            )
            assert (
                "tile_sprite_handler" in self.options
            ), "ERROR: a TiledTileLayer needs a tile_sprite_handler callable to generate all TileSprite objects in the layer!"

            from spygame.tmx.tiled_tile_layer import TiledTileLayer

            l = TiledTileLayer(
                pytmx_layer, pytmx_tiled_map, self.options["tile_sprite_handler"]
            )
            self.add_tiled_tile_layer(l)

        else:
            raise Exception(
                "ERROR: pytmx_layer of type {} cannot be added to Stage. Needs to be pytmx.pytmx.TiledTileLayer or pytmx.pytmx.TiledObjectGroup!".format(
                    type(pytmx_layer).__name__
                )
            )

    def add_tiled_object_group(self, tiled_object_group):
        """
        Adds a TiledObjectGroup (all it's objects as single Sprites) to this Stage.

        :param TiledObjectGroup tiled_object_group:
        """
        # add the layer to our tiled_layers list
        self.tiled_object_groups[tiled_object_group.name] = tiled_object_group

        # add the (already created) sprite-group to this stage under the name of the layer
        assert (
            tiled_object_group.name not in self.sprite_groups
        ), "ERROR: trying to add a TiledObjectGroup to a Stage, but the Stage already has a sprite_group with the name of that layer ({})".format(
            tiled_object_group.name
        )
        self.sprite_groups[tiled_object_group.name] = tiled_object_group.sprite_group

        # add each single sprite of the group to the Stage
        for sprite in tiled_object_group.sprite_group.sprites():
            self.add_sprite(sprite, tiled_object_group.name)

    def add_tiled_tile_layer(self, tiled_tile_layer):
        """
        Adds a TiledTileLayer to this Stage.
        Puts it in the ordered to_render list, in the tiled_layers list.

        :param TiledTileLayer tiled_tile_layer: the TiledTileLayer to add to this Stage
        """
        # put the pytmx_layer into one of the collision groups (if not type==none)?
        # - this is useful for our solve_collisions method
        # if tiled_tile_layer.type != Sprite.get_type("none"):
        #    self.tiled_layers_to_collide.append(tiled_tile_layer)

        # put only TiledTileLayers in to_render (iff do_render=true) and single Sprites (from the TiledObjectGroup) all ordered by render_order
        self.tiled_tile_layers[tiled_tile_layer.name] = tiled_tile_layer

        # add it to the to_render list and re-sort the list by render_order values (note: this list also contains single Sprites)
        if tiled_tile_layer.do_render:
            self.to_render.append(tiled_tile_layer)
            self.to_render.sort(key=lambda x: x.render_order)

        # capture ladders and other autobuild structures?
        if tiled_tile_layer.properties.get("autobuild_objects") == "true":
            objects = tiled_tile_layer.capture_autobuilds()
            for obj in objects:
                self.add_sprite(obj, "autobuilds")

    def add_sprite(self, sprite, group_name):
        """
        Adds a new single Sprite to an existing or a new pygame.sprite.Group.

        :param Sprite sprite: the Sprite to be added to this Stage (the Sprite's position is defined in its rect.x/y properties)
        :param str group_name: the name of the group to which the GameObject should be added (group will not be created if it doesn't exist yet)
        :return: the Sprite that was added
        :rtype: Sprite
        """
        # if the group doesn't exist yet, create it
        if group_name not in self.sprite_groups:
            self.sprite_groups[group_name] = pygame.sprite.Group()
        sprite.stage = self  # set the Stage of this GameObject
        self.sprite_groups[group_name].add(sprite)
        self.sprites.append(sprite)
        sprite.sprite_groups.append(self.sprite_groups[group_name])

        # add each single Sprite to the sorted (by render_order) to_render list and to the "all"-sprites list
        # - note: the to_render list also contains entire TiledTileLayer objects
        if sprite.do_render:
            self.to_render.append(sprite)
            self.to_render.sort(key=lambda x: x.render_order)

        # trigger two events, one on the Stage with the object as target and one on the object with the Stage as target
        self.trigger_event("added_to_stage", sprite)
        sprite.trigger_event("added_to_stage", self)

        return sprite

    def remove_sprite(self, sprite):
        """
        Removes a Sprite from this Stage by putting it in the remove_list for later removal.

        :param Sprite sprite: the Sprite to be removed from the Stage
        """
        self.remove_list.append(sprite)

    def force_remove_sprite(self, sprite):
        """
        Force-removes the given Sprite immediately (without putting it in the remove_list first).

        :param Sprite sprite: the Sprite to be removed from the Stage
        """
        try:
            self.sprites.remove(sprite)
            if sprite.do_render:
                self.to_render.remove(sprite)
        except ValueError:
            return

        # destroy the object
        sprite.destroy()
        self.trigger_event("removed_from_stage", sprite)

    def pause(self):
        """
        Pauses playing the Stage.
        """
        self.is_paused = True

    def unpause(self):
        """
        Unpauses playing the Stage.
        """
        self.is_paused = False

    def tick(self, game_loop):
        """
        Gets called each frame by the GameLoop.
        Calls the tick method on all its Sprites (but only if the sprite is within the viewport).

        :param GameLoop game_loop: the GameLoop object that's currently running (and ticking all Stages)
        """

        if self.is_paused:
            return False

        # do the ticking of all Sprite objects
        self.trigger_event("pre_ticks", game_loop)

        # only tick sprites that are within our viewport
        if self.respect_viewable_range:
            self.viewable_rect.x = self.cmp_viewport.x
            self.viewable_rect.y = self.cmp_viewport.y
            for sprite in self.sprites:
                if (
                    sprite.rect.bottom > self.viewable_rect.top
                    and sprite.rect.top < self.viewable_rect.bottom
                    and sprite.rect.left < self.viewable_rect.right
                    and sprite.rect.right > self.viewable_rect.left
                ):
                    sprite.ignore_after_n_ticks = self.options[
                        "tick_sprites_n_more_frames"
                    ]  # reset to max
                    self.tick_sprite(sprite, game_loop)
                else:
                    sprite.ignore_after_n_ticks -= 1  # if reaches 0 -> ignore
                    if sprite.ignore_after_n_ticks > 0:
                        self.tick_sprite(sprite, game_loop)
        else:
            for sprite in self.sprites:
                sprite.ignore_after_n_ticks = self.options[
                    "tick_sprites_n_more_frames"
                ]  # always reset to max
                self.tick_sprite(sprite, game_loop)

        # do the collision resolution
        self.trigger_event("pre_collisions", game_loop)
        self.solve_collisions()

        # garbage collect destroyed GameObjects
        for sprite in self.remove_list:
            self.force_remove_sprite(sprite)
        self.remove_list.clear()

        self.trigger_event("post_tick", game_loop)

    @staticmethod
    def tick_sprite(sprite, game_loop):
        """
        ticks one single sprite
        :param Sprite sprite: the Sprite object to tick
        :param GameLoop game_loop: the GameLoop object that's currently playing
        """
        if DEBUG_FLAGS & DEBUG_RENDER_SPRITES_BEFORE_EACH_TICK:
            sprite.render(game_loop.display)
            game_loop.display.debug_refresh()
        sprite.tick(game_loop)
        if DEBUG_FLAGS & DEBUG_RENDER_SPRITES_AFTER_EACH_TICK:
            sprite.render(game_loop.display)
            game_loop.display.debug_refresh()

    def solve_collisions(self):
        """
        Look for the objects layer and do each object against the main collision layer.
        Some objects in the objects layer do their own collision -> skip those here (e.g. ladder climbing objects).
        After the main collision layer, do each object against each other.
        """
        # collide each object with all collidable layers (matching collision mask of object)
        for sprite in self.sprites:
            # not ignored (one-tick) and if this game_object completely handles its own collisions within its tick -> ignore it
            if (
                sprite.ignore_after_n_ticks > 0
                and not sprite.handles_own_collisions
                and sprite.collision_mask > 0
            ):
                # collide with all matching tile layers
                for tiled_tile_layer in self.tiled_tile_layers.values():
                    # only collide, if one of the types of the layer matches one of the bits in the Sprite's collision_mask
                    if sprite.collision_mask & tiled_tile_layer.type:
                        col = tiled_tile_layer.collide_simple_with_sprite(
                            sprite, self.options["physics_collision_detector"]
                        )
                        if col:
                            sprite.trigger_event("collision", col)

        # collide all Sprites with all other Sprites (both ways!)
        # - only check if sprite1's collision_matrix matches sprite2's type
        for sprite in self.sprites:
            # not ignored (one-tick) and if this Sprite completely handles its own collisions within its tick -> ignore it
            if (
                sprite.ignore_after_n_ticks > 0
                and not sprite.handles_own_collisions
                and sprite.collision_mask > 0
            ):
                for sprite2 in self.sprites:
                    if (
                        sprite is not sprite2
                        and sprite2.collision_mask > 0
                        and sprite.collision_mask & sprite2.type
                        and sprite2.collision_mask & sprite.type
                    ):
                        direction, v = self.estimate_sprite_direction(sprite)
                        col = self.options["physics_collision_detector"](
                            sprite, sprite2, direction=direction, direction_veloc=v
                        )
                        if col:
                            # trigger "collision" for sprite1
                            sprite.trigger_event("collision", col)
                            ## but only for sprite2 if it does NOT handle its own collisions
                            # if not sprite2.handles_own_collisions:
                            sprite2.trigger_event("collision", col.invert())

    @staticmethod
    def estimate_sprite_direction(sprite):
        """
        tries to return an accurate tuple of direction (x/y) and direction_veloc
        - if sprite directly has vx and vy, use these
        - if sprite has a physics component: use vx and vy from that Component
        - else: pretend vx and vy are 0.0
        then return the direction whose veloc component is highest plus that highest veloc

        :param Sprite sprite: the Sprite to estimate
        :return: tuple of direction (x/y) and direction_veloc
        :rtype: Tuple[str,float]
        """
        phys = sprite.components.get("physics", None)
        # sprite has a physics component with vx/vy
        if phys and hasattr(phys, "vx") and hasattr(phys, "vy"):
            vx = phys.vx
            vy = phys.vy
        # sprite has a vx/vy (meaning handles its own physics)
        elif hasattr(sprite, "vx") and hasattr(sprite, "vy"):
            vx = sprite.vx
            vy = sprite.vy
        else:
            vx = 0.0
            vy = 0.0

        if abs(vx) > abs(vy):
            return "x", vx
        else:
            return "y", vy

    def hide(self):
        """
        Hides the Stage.
        """
        self.is_hidden = True

    def show(self):
        """
        Unhides the Stage.
        """
        self.is_hidden = False

    def stop(self):
        """
        Stops playing the Stage (stops calling `tick` on all GameObjects).
        """
        self.hide()
        self.pause()

    def start(self):
        """
        Starts running the Stage (and calling all GameObject's `tick` method).
        """
        self.show()
        self.unpause()

    def render(self, display):
        """
        Gets called each frame by the GameLoop (after 'tick' is called on all Stages).
        Renders all its layers (ordered by 'render_order' property of the TiledTileLayer in the tmx file).
        TODO: renders Sprites that are not part of any layer.

        :param Display display: the Display object to render on
        """
        if self.is_hidden:
            return False

        self.trigger_event("pre_render", display)
        # loop through the sorted to_render list and render all TiledTileLayer and Sprite objects in this list
        for layer_or_sprite in self.to_render:
            if getattr(layer_or_sprite, "ignore_after_n_ticks", 1) <= 0:
                continue
            layer_or_sprite.render(display)
        self.trigger_event("post_render", display)
