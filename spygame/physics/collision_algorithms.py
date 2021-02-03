from abc import abstractmethod
import math


class Collision(object):
    """
    A simple feature object that stores collision properties for collisions between two objects or between an object and a TiledTileLayer.
    """

    def __init__(self):
        self.sprite1 = (
            None  # hook into the first Sprite participating in this collision
        )
        self.sprite2 = None  # hook into the second Sprite participating in this collision (this could be a TileSprite)
        self.is_collided = True  # True if a collision happened (usually True)
        self.distance = 0  # how much do we have to move sprite1 to separate the two Sprites? (always negative)
        self.magnitude = 0  # abs(distance)
        self.impact = 0.0  # NOT SURE: the impulse of the collision on some mass (used for pushing heavy objects)
        self.normal_x = 0.0  # x-component of the collision normal
        self.normal_y = 0.0  # y-component of the collision normal
        self.separate = [
            0,
            0,
        ]  # (-distance * normal_x, -distance * normal_y) how much to we have to change x/y values for rect to separate the two sprites
        self.direction = None  # None, 'x' or 'y' (direction in which we measure the collision; the other direction is ignored)
        self.direction_veloc = 0  # velocity direction component (e.g. direction=='x' veloc==5 -> moving right, veloc==-10.4 -> moving left)
        self.original_pos = [
            0,
            0,
        ]  # the original x/y-position of sprite1 before the move that lead to the collision happened

    def invert(self):
        """
        Inverts this Collision in place to yield the Collision for the case that the two Sprites are switched.
        """
        # flip the sprites
        tmp = self.sprite1
        self.sprite1 = self.sprite2
        self.sprite2 = tmp
        # invert the normal and separate (leave distance negative, leave magnitude positive)
        self.normal_x = -self.normal_x
        self.normal_y = -self.normal_y
        self.separate = [-self.separate[0], -self.separate[1]]
        # the direction veloc
        self.direction_veloc = -self.direction_veloc
        return self


class CollisionAlgorithm(object):
    """
    A static class that is used to store a collision algorithm.
    """

    # the default collision objects
    # - can be overridden via the collide method
    default_collision_objects = (Collision(), Collision())

    @staticmethod
    @abstractmethod
    def collide(sprite1, sprite2, collision_objects=None, original_pos=None):
        """
        solves a simple spatial collision problem for two Sprites (that have a rect property)
        - defaults to SAT collision between two objects
        - thanks to doc's at: http://www.sevenson.com.au/actionscript/sat/
        - TODO: handle angles on objects
        - TODO: handle velocities of sprites prior to collision to calculate correct normals

        :param Sprite sprite1: sprite 1
        :param Sprite sprite2: sprite 2 (the other sprite)
        :param Union[None,Tuple[Collision]] collision_objects: the two always-recycled returnable Collision instances (aside from None); if None,
            use our default ones
        :param Union[Tuple[int],None] original_pos: the position of sprite1 before doing the move that lead to this collision-detection call
        :return: a Collision object with all details of the collision between the two Sprites (None if there is no collision)
        :rtype: Union[None,Collision]
        """
        pass


class AABBCollision(CollisionAlgorithm):
    """
    A simple axis-aligned bounding-box collision mechanism which only works on Pygame rects.
    """

    @staticmethod
    def collide(
        sprite1,
        sprite2,
        collision_objects=None,
        direction="x",
        direction_veloc=0.0,
        original_pos=None,
    ):
        # TODO: actually, we only need one collision object as we should always only resolve one object at a time

        # TODO: utilize direction veloc information to only return the smallest separation collision

        # direction must be given AND direction_veloc must not be 0.0
        # assert direction == "x" or direction == "y", "ERROR: in AABB collision between {} and {}: direction needs to be either 'x' or 'y'!". \
        #    format(type(sprite1).__name__, type(sprite2).__name__)
        # assert direction_veloc != 0.0, "ERROR in AABB collision between {} and {}: direction_veloc must not be 0.0!".\
        #    format(type(sprite1).__name__, type(sprite2).__name__)

        # use default CollisionObjects?
        if not collision_objects:
            collision_objects = AABBCollision.default_collision_objects

        ret = AABBCollision.try_collide(
            sprite1, sprite2, collision_objects[0], direction, direction_veloc
        )
        if not ret:
            return None

        if not ret.is_collided:
            return None

        # fill in some more values in the recycled Collision object before returning it
        ret.separate[0] = -ret.distance * ret.normal_x
        ret.separate[1] = -ret.distance * ret.normal_y
        if not original_pos:
            original_pos = (sprite1.rect.x, sprite1.rect.y)
        ret.original_pos = original_pos

        return ret

    @staticmethod
    def try_collide(o1, o2, collision_obj, direction, direction_veloc):
        """
        does the actual AABB collision test

        :param Sprite o1: object 1
        :param Sprite o2: object 2
        :param Collision collision_obj: the collision object to be populated
        :param str direction: the direction in which we have to measure a collision (x or y)
        :param float direction_veloc: the velocity value in the given x- or y-direction
        :return: the populated Collision object
        :rtype: Collision
        """
        # reset the recycled collision object
        collision_obj.is_collided = False
        collision_obj.normal_x = 0.0
        collision_obj.normal_y = 0.0
        collision_obj.magnitude = 0.0
        collision_obj.direction = direction
        collision_obj.direction_veloc = direction_veloc

        # overlap?
        if (
            o1.rect.right > o2.rect.left
            and o1.rect.left < o2.rect.right
            and o1.rect.bottom > o2.rect.top
            and o1.rect.top < o2.rect.bottom
        ):
            collision_obj.sprite1 = o1
            collision_obj.sprite2 = o2
            collision_obj.is_collided = True
            if direction == "x":
                if direction_veloc > 0:
                    collision_obj.distance = -(o1.rect.right - o2.rect.left)
                    collision_obj.normal_x = -1.0
                elif direction_veloc < 0:
                    collision_obj.distance = -(o2.rect.right - o1.rect.left)
                    collision_obj.normal_x = 1.0
            else:
                if direction_veloc > 0:
                    collision_obj.distance = -(o1.rect.bottom - o2.rect.top)
                    collision_obj.normal_y = -1.0
                elif direction_veloc < 0:
                    collision_obj.distance = -(o2.rect.bottom - o1.rect.top)
                    collision_obj.normal_y = 1.0

            collision_obj.magnitude = abs(collision_obj.distance)

        return collision_obj if collision_obj.is_collided else None


# TODO: SATCollisions are WIP
class SATCollision(CollisionAlgorithm):
    normal = [0.0, 0.0]

    @staticmethod
    def collide(sprite1, sprite2, collision_objects=None, original_pos=None):
        # use default CollisionObjects?
        if not collision_objects:
            collision_objects = SATCollision.default_collision_objects

        # do AABB first for a likely early out
        # TODO: right now, we only have pygame.Rect anyway, so these are AABBs
        if (
            sprite1.rect.right < sprite2.rect.left
            or sprite1.rect.bottom < sprite2.rect.top
            or sprite2.rect.right < sprite1.rect.left
            or sprite2.rect.right < sprite1.rect.left
        ):
            return None

        test = SATCollision.try_collide(sprite1, sprite2, collision_objects[0], False)
        if not test:
            return None

        test = SATCollision.try_collide(sprite2, sprite1, collision_objects[1], True)
        if not test:
            return None

        # pick the best collision from the two
        ret = (
            collision_objects[1]
            if collision_objects[1].magnitude < collision_objects[0].magnitude
            else collision_objects[0]
        )

        if not ret.is_collided:
            return None

        # fill in some more values in the recycled Collision object before returning it
        ret.separate[0] = -ret.distance * ret.normal_x
        ret.separate[1] = -ret.distance * ret.normal_y
        if not original_pos:
            original_pos = (sprite1.rect.x, sprite1.rect.y)
        ret.original_pos = original_pos

        return ret

    @staticmethod
    def calculate_normal(points, idx):
        pt1 = points[idx]
        pt2 = points[idx + 1] if idx < len(points) - 1 else points[0]

        SATCollision.normal[0] = -(pt2[1] - pt1[1])
        SATCollision.normal[1] = pt2[0] - pt1[0]

        dist = math.sqrt(SATCollision.normal[0] ** 2 + SATCollision.normal[1] ** 2)
        if dist > 0:
            SATCollision.normal[0] /= dist
            SATCollision.normal[1] /= dist

    @staticmethod
    def dot_product_against_normal(point):
        return (SATCollision.normal[0] * point[0]) + (SATCollision.normal[1] * point[1])

    @staticmethod
    def try_collide(o1, o2, collision_obj, flip):
        shortest_dist = float("inf")
        collision_obj.is_collided = False

        # the following only works for AABBs, we will have to change that once objects start rotating or being non-rects
        p1 = [
            [o1.rect.x, o1.rect.y],
            [o1.rect.x + o1.rect.width, o1.rect.y],
            [o1.rect.x + o1.rect.width, o1.rect.y + o1.rect.height],
            [o1.rect.x, o1.rect.y + o1.rect.height],
        ]

        p2 = [
            [o2.rect.x, o2.rect.y],
            [o2.rect.x + o2.rect.width, o2.rect.y],
            [o2.rect.x + o2.rect.width, o2.rect.y + o2.rect.height],
            [o2.rect.x, o2.rect.y + o2.rect.height],
        ]

        # loop through all axes of sprite1
        for i in range(len(p1)):
            SATCollision.calculate_normal(p1, i)

            min1 = SATCollision.dot_product_against_normal(p1[0])
            max1 = min1

            for j in range(1, len(p1)):
                tmp = SATCollision.dot_product_against_normal(p1[j])
                if tmp < min1:
                    min1 = tmp
                if tmp > max1:
                    max1 = tmp

            min2 = SATCollision.dot_product_against_normal(p2[0])
            max2 = min2

            for j in range(1, len(p2)):
                tmp = SATCollision.dot_product_against_normal(p2[j])
                if tmp < min2:
                    min2 = tmp
                if tmp > max2:
                    max2 = tmp

            d1 = min1 - max2
            d2 = min2 - max1

            if d1 > 0 or d2 > 0:
                return None

            min_dist = (max2 - min1) * -1
            if flip:
                min_dist *= -1
            min_dist_abs = abs(min_dist)
            if min_dist_abs < shortest_dist:
                collision_obj.sprite1 = o1
                collision_obj.sprite2 = o2
                collision_obj.distance = min_dist
                collision_obj.magnitude = min_dist_abs
                collision_obj.normal_x = SATCollision.normal[0]
                collision_obj.normal_y = SATCollision.normal[1]
                if collision_obj.distance > 0:
                    collision_obj.distance *= -1
                    collision_obj.normal_x *= -1
                    collision_obj.normal_y *= -1

                collision_obj.is_collided = True
                shortest_dist = min_dist_abs

        # return the actual collision
        return collision_obj if collision_obj.is_collided else None
