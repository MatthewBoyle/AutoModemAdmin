from collections import defaultdict

class NoNonesDefaultDict(defaultdict):
    """A defaultdict that also substitutes the default for any keys with a value set to None.

    The original defaultdict will provide a default value for any key that does not already exist. However,
    if a key is explicitly set to None, then that will replace the default value. This class will prevent None
    from ever being returned, replacing it with the called instance of the callable default_factory. Unlike normal
    defaultdicts, default_factory cannot be set to None.

    :parameter
        default_factory: A callable that takes no arguments and returns the default value for missing keys."""

    def __init__(self, default_factory):
        if default_factory is None:
            raise ValueError("Cannot instantiate a NoNonesDefaultDict with None as the default factory method!")
        elif default_factory() is None:
            raise ValueError("Nice try, smart Alec. Thinking you can use a 'lambda: None' instead. Use a regular "
                             "defaultdict if you want to set the default to None.")
        else:
            super().__init__(default_factory)

    def __setitem__(self, key, value):
        if value is None:
            self.pop(key)
        else:
            super().__setitem__(key, value)

