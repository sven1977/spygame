import pygame


class Display(object):
    """
    A simple wrapper class for a pygame.display/pygame.Surface object representing the pygame display.
    Also stores offset information for Viewport focusing (if Viewport is smaller that the Level, which is usually the case).
    """

    instantiated = False

    def __init__(self, width=600, height=400, title="Spygame Rocks!"):
        """
        :param int width: the width of the Display
        :param int height: the height of the Display
        :param str title: the caption to use on the pygame display
        """
        assert not Display.instantiated, "ERROR: can only create one {} object!".format(
            type(self).__name__
        )
        Display.instantiated = True

        pygame.display.set_caption(title)
        self.width = width
        self.height = height
        self.surface = pygame.display.set_mode((width, height))
        self.offsets = [0, 0]

    def change_dims(self, width, height):
        """
        Changes the Display's size dynamically (during the game).

        :param int width: the new width to use
        :param int height: the new height to use
        """
        self.width = width
        self.height = height
        pygame.display.set_mode((width, height))
        assert (
            self.surface is pygame.display.get_surface()
        ), "ERROR: self.display is not same object as pygame.display.get_surface() anymore!"

    def debug_refresh(self):
        """
        Force-refreshes the display (used only for debug purposes).
        """
        pygame.display.flip()
        pygame.event.get([])  # we seem to have to do this
