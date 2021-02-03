from spygame.event_object import EventObject


# can handle events as well as
class State(EventObject):
    """
    A simple state class that serves as a dict with settable and gettable key/value pairs.
    Setting a new value will trigger "changed"+key events.
    """

    def __init__(self):
        super().__init__()
        self.dict = {}

    # sets a value in our dict and triggers a changed event
    def set(self, key, value, trigger_event=False):
        # trigger an event that the value changed
        if trigger_event:
            old = self.dict[key] if key in self.dict else None
            self.trigger_event("changed." + key, value)
        # set to new value
        self.dict[key] = value

    # retrieve a value from the dict
    def get(self, key):
        if key not in self.dict:
            raise (Exception, "ERROR: key {} not in dict!".format(key))
        return self.dict[key]

    # decrease value by amount
    def dec(self, key, amount: int = 1):
        self.dict[key] -= amount

    # increase value by amount
    def inc(self, key, amount: int = 1):
        self.dict[key] += amount
