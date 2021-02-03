import math

from spygame import DEBUG_FLAGS, \
    DEBUG_RENDER_SPRITES_BEFORE_COLLISION_DETECTION
from spygame.physics.collision_algorithms import AABBCollision
from spygame.physics.physics_component import ControlledPhysicsComponent
from spygame.sprites.sprite import Sprite
from spygame.sprites.tile_sprite import TileSprite


class TopDownPhysics(ControlledPhysicsComponent):
    """
    Defines "top-down-2D"-step physics (agent can move in any of the 4 directions using any step-size (smooth walking)).
    To be addable to any character (player or enemy).
    """

    def __init__(self, name="physics"):
        super().__init__(name)
        # velocities/physics stuff
        self.vx = 0
        self.vy = 0
        self.run_acceleration = 300  # running acceleration
        self.v_max = 150  # max run-speed
        self.stops_abruptly_on_direction_change = True  # Vikings stop abruptly when running in one direction, then the other direction is pressed

        # environment stuff (TODO: where to get Level dimensions from?)
        self.x_min = 0  # the minimum/maximum allowed positions
        self.y_min = 0
        self.x_max = 9000
        self.y_max = 9000

        self.touching = 0  # bitmap with those bits set that the entity is currently touching (colliding with)
        # TODO: what does at_exit mean in terms of an MDP/RL-setting?
        self.at_exit = False

    def added(self):
        super().added()

        obj = self.game_object
        self.x_max -= obj.rect.width
        self.y_max -= obj.rect.height

        obj.register_event(
            "bump.top", "bump.bottom", "bump.left", "bump.right"
        )  # we will trigger these as well -> register them

    # determines x/y-speeds and moves the GameObject
    def tick(self, game_loop):
        """
        Needs to be called by the GameObject at some point during the GameObject's `tick` method.

        :param GameLoop game_loop: the currently playing GameLoop object
        """
        dt = game_loop.dt
        # accelerations
        ax = 0
        ay = 0
        obj = self.game_object
        stage = obj.stage

        # entity has a brain component
        if self.game_obj_cmp_brain:
            # determine x speed
            # -----------------
            # user is trying to move left or right (or both?)
            if self.game_obj_cmp_brain.commands["left"]:
                # only left is pressed
                if not self.game_obj_cmp_brain.commands["right"]:
                    if self.stops_abruptly_on_direction_change and self.vx > 0:
                        self.vx = 0  # stop first if still walking in other direction
                    ax = -self.run_acceleration  # accelerate left
                    obj.flip["x"] = True  # mirror sprite
                # user presses both keys (left and right) -> just stop
                else:
                    self.vx = 0
            # only right is pressed
            elif self.game_obj_cmp_brain.commands["right"]:
                if self.stops_abruptly_on_direction_change and self.vx < 0:
                    self.vx = 0  # stop first if still walking in other direction
                ax = self.run_acceleration  # accelerate right
                obj.flip["x"] = False
            # stop immediately (vx=0; don't accelerate negatively)
            else:
                self.vx = 0

            # determine y speed
            # -----------------
            # user is trying to move up or down (or both?)
            if self.game_obj_cmp_brain.commands["up"]:
                # only up is pressed
                if not self.game_obj_cmp_brain.commands["down"]:
                    if self.stops_abruptly_on_direction_change and self.vy > 0:
                        self.vy = 0  # stop first if still walking in other direction
                    ay = -self.run_acceleration  # accelerate up
                # user presses both keys (up and down) -> just stop
                else:
                    self.vy = 0
            # only down is pressed
            elif self.game_obj_cmp_brain.commands["down"]:
                if self.stops_abruptly_on_direction_change and self.vy < 0:
                    self.vy = 0  # stop first if still walking in other direction
                ay = self.run_acceleration  # accelerate down
            # stop immediately (vy=0; don't accelerate negatively)
            else:
                self.vy = 0

        # entity has no steering unit (speed = 0)
        else:
            self.vx = 0
            self.vy = 0

        # TODO: check the entity's magnitude of vx and vy,
        # reduce the max dt_step if necessary to prevent skipping through objects.
        dt_step = dt
        while dt_step > 0:
            dt = min(1 / 30, dt_step)

            # update x/y-velocity based on acceleration
            self.vx += ax * dt
            if abs(self.vx) > self.v_max:
                self.vx = -self.v_max if self.vx < 0 else self.v_max
            self.vy += ay * dt
            if abs(self.vy) > self.v_max:
                self.vy = -self.v_max if self.vy < 0 else self.v_max

            # reset all touch flags before doing all the collision analysis
            self.at_exit = False

            # first move in x-direction and solve x-collisions
            orig_pos = (obj.rect.x, obj.rect.y)
            if self.vx != 0.0:
                obj.move(self.vx * dt, 0.0)
                if DEBUG_FLAGS & DEBUG_RENDER_SPRITES_BEFORE_COLLISION_DETECTION:
                    obj.render(game_loop.display)
                    game_loop.display.debug_refresh()
                self.collide_in_one_direction(obj, "x", self.vx, orig_pos)

            # then move in y-direction and solve y-collisions
            if self.vy != 0.0:
                obj.move(0.0, self.vy * dt)
                if DEBUG_FLAGS & DEBUG_RENDER_SPRITES_BEFORE_COLLISION_DETECTION:
                    obj.render(game_loop.display)
                    game_loop.display.debug_refresh()
                self.collide_in_one_direction(obj, "y", self.vy, orig_pos)

            dt_step -= dt

    def collide_in_one_direction(
        self, sprite, direction, direction_veloc, original_pos
    ):
        """
        Detects and solves all possible collisions between our GameObject and all Stage's objects (layers and Sprites) in one direction (x or y).

        :param Sprite sprite: the GameObject of this Component (the moving/colliding Sprite)
        :param str direction: either "x" or "y"
        :param float direction_veloc: the velocity in the given direction (x/y-component of the velocity vector)
        :param Tuple[int,int] original_pos: the position of the game_object before this collision detection execution
        """
        stage = sprite.stage

        # default layers
        if sprite.collision_mask & Sprite.get_type("default"):
            for layer in stage.tiled_tile_layers.values():
                if layer.type & Sprite.get_type("default"):
                    self.collide_with_collision_layer(
                        sprite, layer, direction, direction_veloc, original_pos
                    )
        # simple sprites (e.g. enemies)
        for other_sprite in stage.sprites:
            if sprite is other_sprite:
                continue
            if sprite.collision_mask & other_sprite.type:
                col = AABBCollision.collide(
                    sprite,
                    other_sprite,
                    direction=direction,
                    direction_veloc=direction_veloc,
                    original_pos=original_pos,
                )
                if col:
                    sprite.trigger_event("collision", col)

    def collide_with_collision_layer(
        self, sprite, layer, direction, direction_veloc, original_pos
    ):
        """
        Collides a Sprite with a collision TiledTileLayer (type==default) and solves all detected collisions.

        :param Sprite sprite: the Sprite to test for collisions against a TiledTileLayer
        :param TiledTileLayer layer: the TiledTileLayer object in which to look for collision tiles (full of sloped)
        :param str direction: `x` or `y` direction in which the sprite is currently moving before this test
        :param float direction_veloc: the velocity in the given direction (could be negative or positive)
        :param Tuple[int,int] original_pos: the position of the sprite before the move that caused this collision test to be executed
        """
        # determine the tile boundaries (which tiles does the sprite overlap with?)
        (
            tile_start_x,
            tile_end_x,
            tile_start_y,
            tile_end_y,
        ) = layer.get_overlapping_tiles(sprite)

        # if sprite is moving in +/-x-direction:
        # 1) move in columns from left to right (right to left) to look for tiles
        if direction == "x":
            direction_x = int(math.copysign(1.0, direction_veloc))
            for tile_x in range(
                tile_start_x if direction_x > 0 else tile_end_x,
                (tile_end_x if direction_x > 0 else tile_start_x) + direction_x,
                direction_x,
            ):
                for tile_y in range(
                    tile_start_y, tile_end_y + 1
                ):  # y-order doesn't matter
                    tile_sprite = layer.tile_sprites[tile_x, tile_y]
                    if tile_sprite:
                        col = AABBCollision.collide(
                            sprite,
                            tile_sprite,
                            None,
                            direction,
                            direction_veloc,
                            original_pos,
                        )
                        if col:
                            sprite.trigger_event("collision", col)
                            return
        else:
            direction_y = int(math.copysign(1.0, direction_veloc))
            for tile_y in range(
                tile_start_y if direction_y > 0 else tile_end_y,
                (tile_end_y if direction_y > 0 else tile_start_y) + direction_y,
                direction_y,
            ):
                for tile_x in range(
                    tile_start_x, tile_end_x + 1
                ):  # x-order doesn't matter
                    tile_sprite = layer.tile_sprites[tile_x, tile_y]
                    if tile_sprite:
                        col = AABBCollision.collide(
                            sprite,
                            tile_sprite,
                            None,
                            direction,
                            direction_veloc,
                            original_pos,
                        )
                        if col:
                            sprite.trigger_event("collision", col)
                            return

    def collision(self, col):
        obj = self.game_object
        assert (
            obj is col.sprite1
        ), "ERROR: game_object ({}) of physics component is not identical with passed in col.sprite1 ({})!".format(
            obj, col.sprite1
        )

        assert hasattr(col, "sprite2"), "ERROR: no sprite2 in col-object!"
        other_obj = col.sprite2

        # collided with a tile (from a layer)
        if isinstance(other_obj, TileSprite):
            tile_props = other_obj.tile_props
            # colliding with an exit
            # TODO: what does exit mean? in a RL setting? end of episode?
            if tile_props.get("exit"):
                self.at_exit = True
                obj.stage.options["screen_obj"].trigger_event(
                    "reached_exit", obj
                )  # let the level know
                return

        # solve collision
        obj.move(col.separate[0], col.separate[1])

        # top/bottom collisions
        if abs(col.normal_y) > 0.3:
            if (
                self.vy * col.normal_y < 0
            ):  # if normal_y < 0 -> vy is > 0 -> set to 0; if normal_x > 0 -> vy is < 0 -> set to 0
                self.vy = 0
            obj.trigger_event("bump." + ("bottom" if col.normal_y < 0 else "top"), col)

        # left/right collisions
        if abs(col.normal_x) > 0.3:
            if (
                self.vx * col.normal_x < 0
            ):  # if normal_y < 0 -> vx is > 0 -> set to 0; if normal_y > 0 -> vx is < 0 -> set to 0
                self.vx = 0
                obj.trigger_event(
                    "bump." + ("right" if col.normal_x < 0 else "left"), col
                )
