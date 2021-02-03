import pygame

from spygame.keyboard_inputs import KeyboardInputs
from spygame.utils import defaults


class GameLoop(object):
    """
    Class that represents the GameLoop.
    Has play and pause functions: play starts the tick/callback loop.
    Has clock for ticking (keeps track of self.dt each tick), handles and abides to max-fps rate setting.
    Handles keyboard input registrations via its KeyboardInputs object.
    Needs a callback to know what to do each tick.
    Tick method does keyboard_inputs.tick, then calls the given callback with self as only argument.
    """

    # static loop object (the currently active GameLoop gets stored here)
    active_loop = None

    @staticmethod
    def play_a_loop(**kwargs):
        """
        Factory: plays a given GameLoop object or creates a new one using the given \*\*kwargs options.

        :param any kwargs:
                - force_loop (bool): whether to play regardless of whether we still have some active loop running
                - callback (callable): the GameLoop's callback loop function
                - keyboard_inputs (KeyboardInputs): the GameLoop's KeyboardInputs object
                - display (Display): the Display object to render everything on
                - max_fps (int): the max frames per second to loop through
                - screen_obj (Screen): alternatively, a Screen can be given, from which we will extract `display`, `max_fps` and `keyboard_inputs`
                - game_loop (Union[str,GameLoop]): the GameLoop to use (instead of creating a new one); "new" or [empty] for new one
                - dont_play (bool): whether - after creating the GameLoop - it should be played. Can be used for openAI gym purposes, where we just step,
                  not tick
        :return: the created/played GameLoop object or None
        :rtype: Union[GameLoop,None]
        """

        defaults(
            kwargs,
            {
                "force_loop": False,
                "screen_obj": None,
                "keyboard_inputs": None,
                "display": None,
                "max_fps": None,
                "game_loop": "new",
                "dont_play": False,
            },
        )

        # - if there's no other loop active, run the default stageGameLoop
        # - or: there is an active loop, but we force overwrite it
        if GameLoop.active_loop is None or kwargs["force_loop"]:
            # generate a new loop (and play)
            if kwargs["game_loop"] == "new":
                keyboard_inputs = None
                # set keyboard inputs directly
                if kwargs["keyboard_inputs"]:
                    keyboard_inputs = kwargs["keyboard_inputs"]
                # or through the screen_obj
                elif kwargs["screen_obj"]:
                    keyboard_inputs = kwargs["screen_obj"].keyboard_inputs

                display = None
                # set display directly
                if kwargs["display"]:
                    display = kwargs["display"]
                # or through the screen_obj
                elif kwargs["screen_obj"]:
                    display = kwargs["screen_obj"].display

                max_fps = 60
                # set max_fps directly
                if kwargs["max_fps"]:
                    max_fps = kwargs["max_fps"]
                # or through the screen_obj
                elif kwargs["screen_obj"]:
                    max_fps = kwargs["screen_obj"].max_fps

                # Create a new GameLoop object.
                from spygame.stage import Stage
                loop = GameLoop(
                    Stage.stage_default_game_loop_callback,
                    display=display,
                    keyboard_inputs=keyboard_inputs,
                    max_fps=max_fps,
                )
                # And play it, if necessary.
                if not kwargs["dont_play"]:
                    loop.play()
                return loop

            # Play an already existing loop.
            elif isinstance(kwargs["game_loop"], GameLoop):
                kwargs["game_loop"].play()
                return kwargs["game_loop"]

            # do nothing
            return None

    def __init__(self, callback, display, keyboard_inputs=None, max_fps=60):
        """
        :param callable callback: the callback function to call each time we `tick` (after collecting keyboard events)
        :param Display display: the Display object associated with the loop
        :param KeyboardInputs keyboard_inputs: the KeyboardInputs object to use for collecting keyboard information each tick (we simply call the
        KeyboardInputs' `tick` method during our own `tick` method)
        :param int max_fps: the maximum frame rate per second to allow when ticking. fps can be slower, but never faster
        """
        self.is_paused = True  # True -> Game loop will be paused (no frames, no ticks)
        self.callback = callback  # gets called each tick with this GameLoop instance as the first parameter (can then extract dt as `game_loop.dt`)
        self.timer = pygame.time.Clock()  # our tick object
        self.frame = 0  # global frame counter
        self.dt = 0.0  # time since last tick was executed
        # registers those keyboard inputs to capture each tick (up/right/down/left as default if none given)
        # - keyboard inputs can be changed during the loop via self.keyboard_input.update_keys([new key list])
        self.keyboard_inputs = keyboard_inputs or KeyboardInputs(None)
        self.display = display
        self.max_fps = max_fps

    def pause(self):
        """
        Pauses this GameLoop.
        """
        self.is_paused = True
        GameLoop.active_loop = None

    def play(self, max_fps=None):
        """
        Plays this GameLoop (after pausing the currently running GameLoop, if any).
        """
        # pause the current loop
        if GameLoop.active_loop:
            GameLoop.active_loop.pause()
        GameLoop.active_loop = self
        self.is_paused = False
        # tick as long as we are not paused
        while not self.is_paused:
            self.tick(max_fps)

    def tick(self, max_fps=None):
        """
        Called each frame of the GameLoop.
        Collects keyboard events.
        Calls the GameLoop's `callback`.
        Keeps a frame counter.

        :param int max_fps: the maximum allowed number of frames per second (usually 60)
        """
        if not max_fps:
            max_fps = self.max_fps

        # move the clock and store the dt (since last frame) in sec
        self.dt = self.timer.tick(max_fps) / 1000

        # default global events?
        events = pygame.event.get(pygame.QUIT)  # TODO: add more here?
        for e in events:
            if e.type == pygame.QUIT:
                raise Exception(SystemExit, "QUIT")

        # collect keyboard events
        self.keyboard_inputs.tick()

        # call the callback with self (for references to important game parameters)
        self.callback(self)

        # increase global frame counter
        self.frame += 1

    def step(self, action):
        """
        (!)for reinforcement learning only(!) WIP:
        Executes one action on the game.
        The action gets translated into a keyboard sequence first, then is played.

        :param str action: the action to execute on the MDP
        """
        # default global events?
        events = pygame.event.get(pygame.QUIT)  # TODO: add more here?
        for e in events:
            if e.type == pygame.QUIT:
                raise (SystemExit, "QUIT")

        # collect keyboard events
        self.keyboard_inputs.tick()

        # call the callback with self (for references to important game parameters)
        self.callback(self)

        # increase global frame counter
        self.frame += 1
