import math

from spygame.components.component import Component
from spygame.stage import Stage


class Viewport(Component):
    """
    A viewport is a component that can be added to a Stage to help that Stage render
    the scene depending on scrolling/obj_to_follow certain GameObjects.
    Any GameObject with offset_x/y fields is supported, the Viewport will set these
    offsets to the Viewports x/y values before each render call.
    """

    def __init__(self, display):
        """
        :param Display display: the Display object associated with this Viewport
        """
        # Fix name to 'viewport' (only one viewport per Stage).
        super().__init__("viewport")

        # The pygame display (Surface) to draw on; so far we only need it to get the
        # display's dimensions.
        self.display = display

        # Top/left corner (world coordinates) of the Viewport window.
        # Will be used as offset_x/y for the Display.
        self.x = 0
        self.y = 0

        # Parameters used for shaking the Viewport (if something heavy lands on the
        # ground).
        self.is_shaking = False
        self.shake_y = 0  # the current shake-y-offset
        self.shake_time_total = 0
        self.shake_time_switch = 0
        self.shake_frequency = 5

        self.scale = 1.0

        self.directions = {}
        self.obj_to_follow = None
        self.max_speed = 10
        self.bounding_box = None

    def added(self):
        assert isinstance(
            self.game_object, Stage
        ), "ERROR: Viewport Component can only be added to a Stage, but game_objects is of type {}!".format(
            type(self.game_object).__name__
        )
        self.game_object.on_event("pre_render", self, "pre_render")

        self.extend(self.follow_object_with_viewport)
        self.extend(self.unfollow_object_with_viewport)
        self.extend(self.center_on_xy_with_viewport)
        self.extend(self.move_to_xy_with_viewport)
        self.extend(self.shake_viewport)

    # EXTENSION methods (take self as well as GameObject as first two params)
    def follow_object_with_viewport(
        self,
        stage,
        obj_to_follow,
        directions=None,
        bounding_box=None,
        max_speed=float("inf"),
    ):
        """
        Makes the viewport follow a GameObject (obj_to_follow).

        :param GameObject stage: our game_object (the Stage) that has `self` as component
        :param GameObject obj_to_follow: the GameObject that we should follow
        :param dict directions: dict with 'x' and 'y' set to either True or False depending on whether we follow only in x direction or y or both
        :param dict bounding_box: should contain min_x, max_x, min_y, max_y so we know the boundaries of the camera
        :param float max_speed: the max speed of the camera
        """
        stage.off_event("post_tick", self, "follow")
        if not directions:
            directions = {"x": True, "y": True}

        # this should be the level dimensions to avoid over-scrolling by the camera
        # - if we don't have a Level (just a Screen), use the display's size
        if not bounding_box:  # get a default bounding box
            # TODO: this is very specific to us having always a Stage (with options['screen_obj']) as our owning stage
            w = (
                self.game_object.screen.width
                if hasattr(self.game_object.screen, "width")
                else self.display.surface.get_width()
            )
            h = (
                self.game_object.screen.height
                if hasattr(self.game_object.screen, "height")
                else self.display.surface.get_height()
            )
            bounding_box = {"min_x": 0, "min_y": 0, "max_x": w, "max_y": h}

        self.directions = directions
        self.obj_to_follow = obj_to_follow
        self.bounding_box = bounding_box
        self.max_speed = max_speed
        stage.on_event("post_tick", self, "follow")
        self.follow(first=(False if max_speed > 0.0 else True))  # start following

    def unfollow_object_with_viewport(self, stage):
        """
        Stops following.

        :param GameObject stage: our game_object (the Stage) that has `self` as component
        """
        stage.off_event("post_tick", self, "follow")
        self.obj_to_follow = None

    def center_on_xy_with_viewport(self, stage, x, y):
        """
        Centers the Viewport on a given x/y position (so that the x/y position is in the center of the screen afterwards).

        :param GameObject stage: our game_object (the Stage) that has `self` as component
        :param int x: the x position to center on
        :param int y: the y position to center on
        """
        self.center_on(x, y)

    def move_to_xy_with_viewport(self, stage, x, y):
        """
        Moves the Viewport to the given x/y position (top-left corner, not center(!)).

        :param GameObject stage: our game_object (the Stage) that has `self` as Component
        :param int x: the x position to move to
        :param int y: the y position to move to
        """
        self.move_to(x, y)

    def shake_viewport(self, stage, time=3, frequency=5):
        """
        Shakes the Viewport object for the given time and with the given frequency.

        :param GameObject stage: our game_object (the Stage) that has `self` as Component
        :param float time: the amount of time (in sec) for which the Viewport should shake
        :param floar frequency: the frequency (in up/down shakes per second) with which we should shake; higher numbers mean more rapid shaking
        """

        self.is_shaking = True
        self.shake_time_total = time
        self.shake_frequency = frequency
        self.shake_time_switch = 1 / (
            frequency * 2
        )  # after this time, we have to switch direction (2 b/c up and down)

    # END: EXTENSION METHODS

    def follow(self, game_loop=None, first=False):
        """
        Helper method to follow our self.obj_to_follow (should not be called by the API user).
        Called when the Stage triggers Event 'post_tick' (passes GameLoop into it which is not used).

        :param GameLoop game_loop: the GameLoop that's currently playing
        :param bool first: whether this is the very first call to this function (if so, do a hard center on, otherwise a soft-center-on)
        """
        follow_x = (
            self.directions["x"](self.obj_to_follow)
            if callable(self.directions["x"])
            else self.directions["x"]
        )
        follow_y = (
            self.directions["y"](self.obj_to_follow)
            if callable(self.directions["y"])
            else self.directions["y"]
        )

        func = self.center_on if first else self.soft_center_on
        func(
            self.obj_to_follow.rect.centerx if follow_x else None,
            self.obj_to_follow.rect.centery if follow_y else None,
        )

    def soft_center_on(self, x=None, y=None):
        """
        Soft-centers on a given x/y position respecting the Viewport's max_speed property (unlike center_on).

        :param Union[int,None] x: the x position to center on (None if we should ignore the x position)
        :param Union[int,None] y: the y position to center on (None if we should ignore the y position)
        """
        if x:
            dx = (
                x - self.display.width / 2 / self.scale - self.x
            ) / 3  # //, this.followMaxSpeed);
            if abs(dx) > self.max_speed:
                dx = math.copysign(self.max_speed, dx)

            if self.bounding_box:
                if (self.x + dx) < self.bounding_box["min_x"]:
                    self.x = self.bounding_box["min_x"] / self.scale
                elif (
                    self.x + dx
                    > (self.bounding_box["max_x"] - self.display.width) / self.scale
                ):
                    self.x = (
                        self.bounding_box["max_x"] - self.display.width
                    ) / self.scale
                else:
                    self.x += dx
            else:
                self.x += dx

        if y:
            dy = (y - self.display.height / 2 / self.scale - self.y) / 3
            if abs(dy) > self.max_speed:
                dy = math.copysign(self.max_speed, dy)
            if self.bounding_box:
                if self.y + dy < self.bounding_box["min_y"]:
                    self.y = self.bounding_box["min_y"] / self.scale
                elif (
                    self.y + dy
                    > (self.bounding_box["max_y"] - self.display.height) / self.scale
                ):
                    self.y = (
                        self.bounding_box["max_y"] - self.display.height
                    ) / self.scale
                else:
                    self.y += dy
            else:
                self.y += dy

    def center_on(self, x=None, y=None):
        """
        Centers on a given x/y position without(!) respecting the Viewport's max_speed property (unlike soft_center_on).

        :param Union[int,None] x: the x position to center on (None if we should ignore the x position)
        :param Union[int,None] y: the y position to center on (None if we should ignore the y position)
        """
        if x:
            self.x = x - self.display.width / 2 / self.scale
        if y:
            self.y = y - self.display.height / 2 / self.scale

    def move_to(self, x=None, y=None):
        """
        Moves the Viewport to a given x/y position (top-left corner, not centering) without(!) respecting the Viewport's max_speed property.

        :param Union[int,None] x: the x position to move to (None if we should ignore the x position)
        :param Union[int,None] y: the y position to move to (None if we should ignore the y position)
        """
        if x:
            self.x = x
        if y:
            self.y = y
        return self.game_object  # ?? why

    def tick(self, game_loop):
        if self.is_shaking:
            dt = game_loop.dt
            self.shake_time_total -= dt
            # done shaking

    def pre_render(self, display):
        """
        Sets the offset property of the given Display so that it matches our (previously) calculated x/y values.

        :param Display display: the Display, whose offset we will change here
        """
        self.display.offsets[0] = self.x
        self.display.offsets[1] = self.y
