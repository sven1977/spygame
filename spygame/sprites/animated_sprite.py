from spygame.components.animation import Animation
from spygame.sprites.sprite import Sprite
from spygame.sprites.sprite_sheet import SpriteSheet


class AnimatedSprite(Sprite):
    """
    Adds an Animation component to each Sprite instance.
    AnimatedSprites need a SpriteSheet (no static images or no-render allowed).

    :param int x: the initial x position of the Sprite
    :param int y: the initial y position of the Sprite
    :param SpriteSheet spritesheet: the SpriteSheet object to use for this Sprite
    :param dict animation_setup: the dictionary with the animation setup data to be sent to Animation.register_settings (the name of the registry record will
            be kwargs["anim_settings_name"] OR spritesheet.name)
    """

    def __init__(self, x, y, sprite_sheet, animation_setup, **kwargs):
        """
        :param int x: the initial x position of the AnimatedSprite
        :param int y: the initial y position of the AnimatedSprite
        :param SpriteSheet sprite_sheet: the SpriteSheet to use for animations
        :param dict animation_setup: a dictionary with all the different animation name and their settings (animation speed, frames to use, etc..)
        """
        assert isinstance(
            sprite_sheet, SpriteSheet
        ), "ERROR: AnimatedSprite needs a SpriteSheet in its c'tor!"

        super().__init__(x, y, sprite_sheet=sprite_sheet, **kwargs)
        self.cmp_animation = self.add_component(Animation("animation"))

        self.anim_settings_name = (
            kwargs.get("anim_settings_name", None) or sprite_sheet.name
        )
        Animation.register_settings(
            self.anim_settings_name, animation_setup, register_events_on=self
        )
        # play the default animation (now that we have added the Animation Component, we can call play_animation on ourselves)
        self.play_animation(animation_setup["default"])
