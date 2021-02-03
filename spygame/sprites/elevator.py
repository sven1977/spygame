from spygame.sprites.sprite import Sprite


class Elevator(Sprite):
    """
    A simple elevator/moving platform class.
    Can either go in x or in y direction, with a configurable speed and in between settable coordinate values.
    Has a Dockable Component to be able to carry characters standing on top of it.
    Is of type one_way_platform so one can jump on the Elevator also from below it.
    """

    def __init__(self, x, y, direction="y", initial_veloc=50, max_pos=500, min_pos=0):
        super().__init__(x, y, image_file="images/elevator.png")
        self.direction = direction
        self.vx = initial_veloc if direction == "x" else 0.0
        self.vy = initial_veloc if direction == "y" else 0.0
        self.max_pos = max_pos
        self.min_pos = min_pos

        # add Dockable component (so that objects can stand on the elevator and move along with it)
        from spygame.components.dockable import Dockable

        self.cmp_dockable = self.add_component(Dockable("dockable"))  # type: Dockable

        # adjust the type
        self.type |= Sprite.get_type("dockable,one_way_platform")
        self.collision_mask = 0  # don't do any collisions for this elevator (only other Sprites vs Elevator)

    def tick(self, game_loop):
        """
        Moving elevator up and down OR left and right.
        """
        dt = game_loop.dt

        self.move(self.vx * dt, self.vy * dt)
        if self.direction == "x":
            if self.rect.x < self.min_pos:
                self.vx = abs(self.vx)
                self.move(self.min_pos, None, absolute=True)
            elif self.rect.x > self.max_pos:
                self.vx = -abs(self.vx)
                self.move(self.max_pos, None, absolute=True)
        else:
            if self.rect.y < self.min_pos:
                self.vy = abs(self.vy)
                self.move(None, self.min_pos, absolute=True)
            elif self.rect.y > self.max_pos:
                self.vy = -abs(self.vy)
                self.move(None, self.max_pos, absolute=True)
