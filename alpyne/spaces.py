import logging

log = logging.getLogger("RLSpace")


class RLSpace:
    """
    A generic object containing the core structure for the Configuration, Observation, and Action spaces.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: The sequence of items to match to the space's names (will throw an error unless the space's name order is set)
        :param kwargs: name-value pairs to include
        """
        if args:
            names = getattr(self, '_NAME_ORDER')
            if not names:
                raise AttributeError(
                    "Cannot use args; the name order is not set for the space type (requires passing the source or manual assignment)")
            if len(args) != len(names):
                raise AttributeError(f"Provided {len(args)} args when {len(names)} were expected")
            kwargs = dict(zip(names, args))

        for name, value in kwargs.items():
            setattr(self, name, value)

    def __getattribute__(self, item):
        try:
            attr = object.__getattribute__(self, item)
            return attr() if callable(attr) else attr
        except AttributeError:
            raise

    def __str__(self):
        return type(self).__name__ + str(self.__dict__)

    def __repr__(self):
        return str(self)


class Configuration(RLSpace):
    """
    An object representing the starting values to pass to the sim at the start of each run.

    Allows values to be assigned as either static values or generators (retrieving the next value whenever it is queried).
    """
    _NAME_ORDER = None
    pass  # no current special attributes


class Observation(RLSpace):
    """ A read-only object representing an observation taken from the simulator """
    _NAME_ORDER = None

    def __init__(self, *args, **kwargs):
        """
        :param kwargs: name-value pairs to include
        """
        self.__dict__['_initializing'] = True
        super().__init__(*args, **kwargs)
        self.__dict__.pop('_initializing')

    def __setattr__(self, key, value):
        if '_initializing' not in self.__dict__:
            raise AttributeError("Cannot modify an immutable object")
        super().__setattr__(key, value)


class Action(RLSpace):
    """
    An object representing an action to sent to the simulator.

    Allows values to be assigned as either static values or generators (retrieving the next value whenever it is queried).
    """
    _NAME_ORDER = None
    pass  # no current special attributes
