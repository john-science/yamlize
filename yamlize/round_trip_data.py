import six


# TODO: replace with ruamel.yaml.comments.Anchor
class _AnchorNode(object):

    __slots__ = ('value', )

    def __init__(self, value):
        self.value = value


class __RoundTripType(type):

    def __init__(cls, *args):
        type.__init__(cls, *args)
        cls.__no_data = cls.__new__(cls)
        cls.__no_data.__init__(None)

    def __call__(cls, node):
        if node is None:
            return cls.__no_data
        else:
            inst = type.__call__(cls, node)
            return inst


@six.add_metaclass(__RoundTripType)
class RoundTripData(object):

    __slots__ = ('_rtd', '_kids_rtd')  # can't use private variables with six

    def __init__(self, node):
        self._rtd = {}
        self._kids_rtd = {}

        if node is not None:
            for key in dir(node):
                if key.startswith('__') or key in {'value', 'id'}:
                    continue

                attr = getattr(node, key)

                if callable(attr) or attr is None:
                    continue

                self._rtd[key] = attr

    def __reduce__(self):
        """
        Used for pickling, redults in a loss of data.

        Some objects from ruamel.yaml do not appear to be pickleable.
        """
        return (RoundTripData, (None,))

    def __bool__(self):
        return len(self._rtd) > 0

    __nonzero__ = __bool__

    def apply(self, node):
        for key, val in self._rtd.items():
            if key == 'anchor':
                val = _AnchorNode(val)
            setattr(node, key, val)

    def __get_key(self, key):
        try:
            return hash(key)
        except TypeError:
            return type(key), id(key)

    def __setitem__(self, key, rtd):
        # don't bother storing if there wasn't any data
        if rtd:
            self._kids_rtd[self.__get_key(key)] = rtd

    def __getitem__(self, key):
        return self._kids_rtd.get(self.__get_key(key), RoundTripData(None))

