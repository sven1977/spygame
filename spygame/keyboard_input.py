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
        #OBSOLETE: self.desc_to_key.clear()
        if new_key_list:
            for desc in new_key_list:
                key = getattr(pygame, "K_" + (desc.upper() if len(desc) > 1 else desc))
                self.keyboard_registry[key] = False
                self.descriptions[key] = desc
                #OBSOLETE: self.desc_to_key[desc] = key
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
            if getattr(e, 'key', None) in self.keyboard_registry:
                if e.type == pygame.KEYDOWN:
                    self.keyboard_registry[e.key] = True
                    self.trigger_event("key_down." + self.descriptions[e.key])
                else:
                    self.keyboard_registry[e.key] = False
                    self.trigger_event("key_up." + self.descriptions[e.key])
