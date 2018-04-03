import sys

from .attributes import Attribute, MapItem, KeyedListItem
from .attribute_collection import (AttributeCollection, MapAttributeCollection,
                                   KeyedListAttributeCollection)
from .maps import Map, KeyedList
from .objects import Object
from .sequences import Sequence
from .yamlizable import Dynamic, Yamlizable, Typed
from .yamlizing_error import YamlizingError


class StrList(Sequence):

    item_type = Dynamic


class FloatList(Sequence):

    item_type = float


class IntList(Sequence):

    item_type = int


