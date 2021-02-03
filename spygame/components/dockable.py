from spygame.components.component import Component
from spygame.sprites.sprite import Sprite


class Dockable(Component):
    """
    A dockable component allows 1) for Sprites to dock to a so-called "mother_ship" and b) for Sprites to become "mother_ships" themselves (other Sprites can
    dock to this Sprite). Sprites that are docked to our mother_ship (this Component's Sprite) will be moved along with it when they stand on top.
    """

    DEFINITELY_DOCKED = 0x1  # this object is definitely docked to something right now
    DEFINITELY_NOT_DOCKED = (
        0x2  # this object is definitely not docked to something right now
    )
    TO_BE_DETERMINED = (
        0x4  # the docking state of this object is currently being determined
    )
    PREVIOUSLY_DOCKED = (
        0x8  # if set, the object was docked to something in the previous frame
    )

    def __init__(self, name="dockable"):
        """
        :param str name: the name of the Component
        """
        super().__init__(name)
        self.docked_sprites = (
            set()
        )  # set that holds all Sprites (by GameObject id) currently docked to this one
        # holds the objects that we stand on and stood on previously:
        # slot 0=current state; slot 1=previous state (sometimes we need the previous state since the current state gets reset to 0 every step)
        self.docking_state = 0
        self.docked_to = (
            None  # the reference to the object that we are currently docked to
        )

    def added(self):
        # make sure our GameObject is a Sprite
        assert isinstance(
            self.game_object, Sprite
        ), "ERROR: game_object of Component Dockable must be of type Sprite (not {})!".format(
            type(self.game_object).__name__
        )
        # extend our GameObject with move (thereby overriding the Sprite's move method)
        self.extend(self.move)

    def move(self, sprite, x, y, absolute=False):
        """
        This will 'overwrite' the normal Sprite's `move` method by Component's extend.

        :param Sprite sprite: the GameObject that this Component belongs to (the Sprite to move around)
        :param Union[int,None] x: the amount in pixels to move in x-direction
        :param Union[int,None] y: the amount in pixels to move in y-direction
        :param bool absolute: whether x and y are given as absolute coordinates (default: False): in this case x/y=None means do not move in this dimension
        """
        orig_x = sprite.rect.x
        orig_y = sprite.rect.y

        # first call the original Sprite's move method
        sprite._super_move(x, y, absolute)

        # move all our docked Sprites along with us
        if not absolute:
            for docked_sprite in self.docked_sprites:
                docked_sprite.move(x, y, absolute=False)
        else:
            # translate into relative movement: we don't want the docked components to move to the given mothership's absolute values
            x_move = x - orig_x if x is not None else 0
            y_move = y - orig_y if y is not None else 0
            for docked_sprite in self.docked_sprites:
                docked_sprite.move(x_move, y_move)

    def dock_to(self, mother_ship):
        """
        A sprite lands on an elevator -> couple the elevator to the sprite so that when the elevator moves, the sprite moves along with it.
        Only possible to dock to `dockable`-type objects.

        :param Sprite mother_ship: the Sprite to dock to (Sprite needs to have a dockable component)
        """
        prev = self.is_docked()
        obj = self.game_object
        # can only dock to dockable-type objects
        if mother_ship.type & Sprite.get_type("dockable"):
            self.docking_state = Dockable.DEFINITELY_DOCKED
            if prev:
                self.docking_state |= Dockable.PREVIOUSLY_DOCKED
            self.docked_to = mother_ship
            # add docked obj to mothership docked-obj-list (if present)
            if "dockable" in mother_ship.components:
                # print("adding {} (id {}) to mothership {}".format(type(obj).__name__, obj.id, type(self.docked_to).__name__))
                mother_ship.components["dockable"].docked_sprites.add(obj)

    def undock(self):
        """
        Undocks itself from the mothership.
        """
        obj = self.game_object
        prev = self.is_docked()
        self.docking_state = Dockable.DEFINITELY_NOT_DOCKED
        if prev:
            self.docking_state |= Dockable.PREVIOUSLY_DOCKED
        # remove docked obj from mothership docked-obj-list (if present)
        if self.docked_to and "dockable" in self.docked_to.components:
            # print("removing {} (id {}) from mothership {}".format(type(obj).__name__, obj.id, type(self.docked_to).__name__))
            self.docked_to.components["dockable"].docked_sprites.discard(obj)
        self.docked_to = None

    def undock_all_docked_objects(self):
        """
        undocks all objects currently docked to this object
        """
        l = list(self.docked_sprites)
        for obj in l:
            if "dockable" in obj.components:
                obj.components["dockable"].undock()

    def to_determine(self):
        """
        Changes our docking state to be undetermined (saves the current state as PREVIOUS flag).
        """
        prev = self.is_docked()
        self.docking_state = Dockable.TO_BE_DETERMINED
        if prev:
            self.docking_state |= Dockable.PREVIOUSLY_DOCKED

    def is_docked(self):
        """
        :return: True if the current state is definitely docked OR (to-be-determined AND previous state was docked)
        :rtype: bool
        """
        return bool(
            self.docking_state & Dockable.DEFINITELY_DOCKED
            or (
                self.docking_state & Dockable.TO_BE_DETERMINED
                and self.docking_state & Dockable.PREVIOUSLY_DOCKED
            )
        )

    def state_unsure(self):
        """
        :return: True if our current docking state is not 100% sure (TO_BE_DETERMINED)
        :rtype: bool
        """
        return bool(self.docking_state & Dockable.TO_BE_DETERMINED)
