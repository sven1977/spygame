import importlib
import re
import sys


def convert_type(value, force_class=False):
    """
    Converts the given value from a string (or other) type into the most likely type.
    E.g.
    'some text' -> 'some text' (str)
    '1' -> 1 (int)
    '-51' -> -51 (int)
    '0.1' -> 0.1 (float)
    'true' -> True (bool)
    'False' -> False (bool)
    [1, 2, 3] -> [1, 2, 3] (list)
    spygame.Ladder -> <type spygame.Ladder> (a python class object; can be used as a ctor to construct objects of that class)

    :param any value: the given value to be converted to the most-likely python type
    :param bool force_class: if True, we will interpret even simple strings (starting with upper case but without any dots) as class names (e.g. Ladder)
    :return: the converted value
    :rtype: any
    """
    as_str = str(value)
    # int
    if re.fullmatch("-?\\d+", as_str):
        return int(value)
    # float
    elif re.fullmatch("-?\d+\.\d+", as_str):
        return float(value)
    # bool
    elif re.fullmatch("(true|false)", as_str, flags=re.I):
        return value in ("True", "true")
    else:
        match_obj = re.fullmatch("^((.+)\.)?([A-Z][a-zA-Z0-9]+)$", as_str)
        # a class with preceding modules (force_class does not have to be set to trigger this detection)
        if match_obj:
            _, module_, class_ = match_obj.groups(
                default="__main__"
            )  # if no module given, assume a class defined in __main__

            # module_name, function_name = type_.rsplit(".", 1)
            # try:
            module = importlib.import_module(module_)
            ctor = getattr(module, class_, None)
            # except (ModuleNotFoundError, ImportError):
            #    pass

            # ctor = getattr(sys.modules[module_], class_, None)
            assert isinstance(
                ctor, type
            ), "ERROR: the string {}.{} does not resolve into a defined class!".format(
                module_, class_
            )
            return ctor
        # a class (no modules, but force_class is set to True)
        elif force_class:
            match_obj = re.fullmatch("^([A-Z][a-zA-Z0-9]+)$", as_str)
            if match_obj:
                (class_) = match_obj.groups()
                ctor = getattr(sys.modules["__main__"], class_, None)
                assert isinstance(
                    ctor, type
                ), "ERROR: the string {} does not resolve into a defined class!".format(
                    class_
                )
                return ctor
        # str (or list or others)
        return value


def defaults(dictionary, defaults_dict):
    """
    Adds all key/value pairs from defaults_dict into dictionary, but only if dictionary doesn't have the key defined yet.

    :param dict dictionary: the target dictionary
    :param dict defaults_dict: the source (default) dictionary to take the keys from (only if they are not defined in dictionary
    """
    for key, value in defaults_dict.items():
        if key not in dictionary:  # overwrite only if key is missing
            dictionary[key] = value


def get_kwargs_from_obj_props(obj_props):
    """
    returns a kwargs dict retrieved from a single object's properties in a level-tmx TiledObjectGroup
    """
    kwargs = {}
    for key, value in obj_props.items():
        # special cases
        # a spritesheet (filename)
        if key == "tsx":
            from spygame.sprites.sprite_sheet import SpriteSheet

            kwargs["sprite_sheet"] = SpriteSheet("data/" + value + ".tsx")
        # an image_file
        elif key == "img":
            kwargs["image_file"] = "images/" + value + ".png"
        # a width/height information for the collision box
        elif key == "width_height":
            kwargs["width_height"] = tuple(
                map(lambda x: convert_type(x), value.split(","))
            )
        # vanilla kwarg
        else:
            kwargs[key] = convert_type(value)

    return kwargs
