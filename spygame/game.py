import pygame

from spygame import DEBUG_NONE
from spygame.display import Display
from spygame.screens import Screen, Level
from spygame.stage import Stage


class Game(object):
    """
    An object that serves as a container for Screen and Level objects.
    Manages displaying the screens (start screen, menus, etc..) and playable levels of the game.
    Also keeps a Display object (and determines its size), which is used for rendering and displaying the game.
    """

    instantiated = False

    def __init__(
        self,
        screens_and_levels,
        width=0,
        height=0,
        title="spygame Demo!",
        max_fps=60,
        debug_flags=DEBUG_NONE,
    ):
        """
        :param list screens_and_levels: a list of Screen and Level definitions. Each item is a dict with
        :param int width: the width of the screen in pixels (0 for auto)
        :param int height: the height of the screen in pixels (0 for auto)
        :param str title: the title of the game (will be displayed as the game Window caption)
        :param int max_fps: the max. number of frames in one second (could be less if Game runs slow, but never more)
        :param int debug_flags: a bitmap for setting different debug flags (see global variables DEBUG_...)
        """
        assert not Game.instantiated, "ERROR: can only create one {} object!".format(
            type(self).__name__
        )
        Game.instantiated = True

        # init the pygame module (if this did not already happen)
        pygame.init()

        self.screens_by_name = {}  # holds the Screen objects by key=level-name
        self.screens = []  # list of screens
        self.levels_by_name = {}  # holds the Level objects by key=level-name
        self.levels = []  # sorted list of levels

        self.max_fps = max_fps

        # try this: set debug flags globally
        global DEBUG_FLAGS
        DEBUG_FLAGS = debug_flags

        # create the Display object for the entire game: we pass it to all levels and screen objects
        self.display = Display(
            width, height, title
        )  # use widthxheight for now (default); this will be reset to the largest Level dimensions further below

        # our levels (if any) determine the size of the display
        get_w_from_levels = True if width == 0 else False
        get_h_from_levels = True if height == 0 else False

        # initialize all screens and levels
        for i, screen_or_level in enumerate(screens_and_levels):
            name = screen_or_level.pop("name", "screen{:02d}".format(i))
            id_ = screen_or_level.pop("id", 0)
            keyboard_inputs = screen_or_level.pop("keyboard_inputs", None)
            max_fps = screen_or_level.pop("max_fps", self.max_fps)

            # Screen class has to be given since Screen (as a default) would be abstract
            assert (
                "class" in screen_or_level
            ), "ERROR: Game object needs the 'class' property for all given Screens and Levels!"
            assert issubclass(
                screen_or_level["class"], Screen
            ), "ERROR: Game object needs the 'class' property to be a subclass of Screen!"
            class_ = screen_or_level["class"]
            # only distinguish between Level and "regular" Screen
            if issubclass(class_, Level):
                level = class_(
                    name,
                    id=id_,
                    display=self.display,
                    keyboard_inputs=keyboard_inputs,
                    max_fps=max_fps,
                    **screen_or_level
                )
                self.levels_by_name[name] = level
                self.levels.append(level)
                # register events
                level.on_event("mastered", self, "level_mastered")
                level.on_event("aborted", self, "level_aborted")
                level.on_event("lost", self, "level_lost")
                # store level dimensions for display
                if get_w_from_levels and level.width > width:
                    width = level.width
                if get_h_from_levels and level.height > height:
                    height = level.height
            # a Screen
            else:
                screen = class_(
                    name,
                    id=id_,
                    display=self.display,
                    keyboard_inputs=keyboard_inputs,
                    max_fps=max_fps,
                    **screen_or_level
                )
                self.screens_by_name[name] = screen
                self.screens.append(screen)

        # now that we know all Level sizes, change the dims of the pygame.display if width and/or height were Level-dependent
        if (get_w_from_levels and width > 0) or (get_h_from_levels and height > 0):
            # static method
            self.display.change_dims(width, height)

    def get_next_level(self, level):
        """
        returns the next level (if exists) as object; None if no next level

        :param Level level: the Level, whose next Level we would like to get
        :return: the next Level after level; None if no next Level exists
        :rtype: Union[Level,None]
        """
        try:
            next_ = self.levels[(level if isinstance(level, int) else level.id) + 1]
        except IndexError:
            next_ = None
        return next_

    def level_mastered(self, level):
        """
        a level has been successfully finished -> play next one

        :param Level level: the Level object that has been mastered
        """
        next_ = self.get_next_level(level)
        if next_:
            next_.play()
        else:
            print("All done!! Congrats!!")
            self.level_aborted(level)

    def level_lost(self, level):
        """
        a level has been lost

        :param Level level: the Level object in which the loss happened
        """
        print("Game Over!")
        self.level_aborted(level)

    def level_aborted(self, level):
        """
        aborts the level and tries to play the "start" screen

        :param Level level: the Level object that has been aborted
        """
        Stage.clear_stages()
        screen = self.screens_by_name.get("start")
        if screen:
            screen.play()
        else:
            quit()
