import pygame

from spygame.event_object import EventObject


class KeyboardInputs(EventObject):
    """
    A class to handle keyboard inputs by the user playing the spygame game.
    A KeyboardInput object is passed to the GameLoop c'tor, so that the GameLoop can `tick` the KeyboardInput object each frame.
    Single keys to watch out for can be registered via the `update_keys` method (not registered keys will be ignored).
    The tick method collects all keydown/keyup pygame events and stores the currently registered keys in the `keyboard_registry` as True (currently pressed)
    or False (currently not pressed).
    All keys are described by their pygame names (without the leading `K_`), e.g. pygame.K_UP=`up`, pygame.K_ESCAPE=`escape`, etc..
    """

    def __init__(self, key_list=None):
        """
        :param Union[list,None] key_list: the list of keys to be added right away to our keyboard_registry dict
        """
        super().__init__()

        # stores the keys that we would like to be registered as important
        # - key: pygame keyboard code (e.g. pygame.K_ESCAPE, pygame.K_UP, etc..)
        # - value: True if currently pressed, False otherwise
        # - needs to be ticked in order to yield up-to-date information (this will be done by a GameLoop playing a Screen)
        self.keyboard_registry = {}
        self.descriptions = {}

        if key_list is None:
            key_list = ["up", "down", "left", "right"]
        self.update_keys(key_list)

    def update_keys(self, new_key_list=None):
        """
        Populates our registry and other dicts with the new key-list given (may be an empty list).

        :param Union[List,None] new_key_list: the new key list, where each item is the lower-case pygame keycode without the leading
            `K_` e.g. `up` for pygame.K_UP; use None for clearing out the registry (no keys assigned)
        """
        self.unregister_all_events()
        self.keyboard_registry.clear()
        self.descriptions.clear()
        # OBSOLETE: self.desc_to_key.clear()
        if new_key_list:
            for desc in new_key_list:
                key = getattr(pygame, "K_" + (desc.upper() if len(desc) > 1 else desc))
                self.keyboard_registry[key] = False
                self.descriptions[key] = desc
                # OBSOLETE: self.desc_to_key[desc] = key
                # signal that we might trigger the following events:
                self.register_event("key_down." + desc, "key_up." + desc)

    def tick(self):
        """
        Pulls all keyboard events from the event queue and processes them according to our keyboard_registry/descriptions.
        Triggers events for all registered keys like: 'key_down.[desc]' (when  pressed) and 'key_up.[desc]' (when released),
        where desc is the lowercase string after `pygame.K_`... (e.g. 'down', 'up', etc..).
        """
        events = pygame.event.get([pygame.KEYDOWN, pygame.KEYUP])
        for e in events:
            # a key was pressed that we are interested in -> set to True or False
            if getattr(e, "key", None) in self.keyboard_registry:
                if e.type == pygame.KEYDOWN:
                    self.keyboard_registry[e.key] = True
                    self.trigger_event("key_down." + self.descriptions[e.key])
                else:
                    self.keyboard_registry[e.key] = False
                    self.trigger_event("key_up." + self.descriptions[e.key])


class KeyboardCommandTranslation(object):
    """
    A class to represent a relationship between a pressed key and a command (or two commands)
    The normal relationship is: [some key]: when pressed -> [command] is True; when not pressed -> [command] is False
    But other, more complex relationships are supported as well.
    """

    # key-to-command flags
    NORMAL = 0x0  # normal: when key down -> command is True (this is essentially: DOWN_LEAVE_UP_LEAVE)
    DOWN_ONE_TICK = 0x1  # when key down -> command is True for only one tick (after that, key needs to be released to fire another command)
    # DOWN_LEAVE = 0x2  # when key down -> command is x (and stays x as long as key is down)
    UP_ONE_TICK = 0x2  # when key up -> command is y for one frame

    # can only execute command if an animation is currently not playing or just completed (e.g. swinging sword)
    BLOCK_REPEAT_UNTIL_ANIM_COMPLETE = 0x4
    # when key down -> command is x (and stays x); when key gets released -> command is y for one frame (BUT only after a certain animation has been completed)
    BLOCK_OTHER_CMD_UNTIL_ANIM_COMPLETE = 0x8

    # some flags needed to describe the state for the DOWN_LEAVE_UP_ONE_TICK_WAIT_FOR_ANIM type of key-command-translation
    STATE_NONE = 0x0
    STATE_CHARGING = 0x1  # we are currently charging after key-down (when fully charged, we are ready to execute upon other_command)
    STATE_FULLY_CHARGED = 0x2  # if set, we are fully charged and we will execute other_command as soon as the key is released
    STATE_CMD_RECEIVED = 0x4  # if set, the key for the other_command has already been released, but we are still waiting for the charging to be complete

    def __init__(
        self, key, command, flags=0, other_command=None, animation_to_complete=None
    ):
        """
        :param str key: the key's description, e.g. `up` for K_UP
        :param str command: the `main` command's description; can be any string e.g. `fire`, `jump`
        :param int flags: keyboard-command behavior flags
        :param str other_command: a possible second command associated with the key (when key is released, e.g. `release_bow`)
        :param Union[list,str] animation_to_complete: animation(s) that needs to be completed in order for the other_command to be executable
        """

        self.key = key
        self.command = command

        assert (
            flags
            & (
                self.BLOCK_REPEAT_UNTIL_ANIM_COMPLETE
                | self.BLOCK_OTHER_CMD_UNTIL_ANIM_COMPLETE
            )
            == 0
            or isinstance(animation_to_complete, str)
            or isinstance(animation_to_complete, set)
        ), "ERROR: animation_to_complete needs to be of type str or set!"

        self.flags = flags
        self.other_command = other_command
        # This could be a set of anims (one of them has to be completed).
        self.animation_to_complete = (
            {animation_to_complete}
            if isinstance(animation_to_complete, str)
            else animation_to_complete
        )
        # The current state for the other_command (charging, charged, cmd_received).
        self.state_other_command = 0

        # Set to True for temporarily blocking this translation.
        self.is_disabled = False
