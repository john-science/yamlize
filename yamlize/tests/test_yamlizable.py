import unittest
import pickle

import sys
import six

from yamlize import yamlizable
from yamlize import YamlizingError
from yamlize import Attribute
from yamlize import yaml_list
from yamlize import yaml_map
from yamlize import yaml_keyed_list


@yamlizable(Attribute(name='name'),
            Attribute(name='age'))
class Animal(object):

    def __init__(self, name, age):
        self.name = name
        self.age = age


@yamlizable(Attribute(name='one', type=int),
            Attribute(name='array', type=list))
class TypeCheck(object):

    def __init__(self, one, array):
        self.one = one
        self.array = array


@yamlizable(Attribute(name='name', type=str))
class AnimalWithFriend(object):
    pass
AnimalWithFriend.attributes.add(Attribute(name='friend',
                                          type=AnimalWithFriend,
                                          default=None))


class Test_from_yaml(unittest.TestCase):

    def test_bad_type(self):
        stream = six.StringIO('[this, is a list]')
        with self.assertRaises(YamlizingError):
            Animal.load(stream)

        stream = six.StringIO('this is a scalar')
        with self.assertRaises(YamlizingError):
            Animal.load(stream)

    def test_attrs_applied(self):
        stream = 'name: Possum\nage: 5'
        poss = Animal.load(stream)
        self.assertTrue(hasattr(poss, 'name'))
        self.assertTrue(hasattr(poss, 'age'))

    def test_missing_non_default_attributes_fail(self):
        stream = 'name: Possum'
        with self.assertRaises(YamlizingError):
            Animal.load(stream)
        self.assertEqual(None, AnimalWithFriend.load(stream).friend)

    def test_bonus_attributes_fail(self):
        stream = 'name: Possum\nage: 5\nbonus: fail'
        with self.assertRaises(YamlizingError):
            Animal.load(stream)

    def test_TypeCheck_good(self):
        stream = six.StringIO('one: 1\narray: [a, bc]')
        tc = TypeCheck.load(stream)
        self.assertEqual(1, tc.one)
        self.assertEqual('a bc'.split(), tc.array)

    def test_TypeCheck_bad(self):
        stream = six.StringIO('one: 1\narray: 99')
        with self.assertRaises(YamlizingError):
            tc = TypeCheck.load(stream)

        stream = six.StringIO('one: a\narray: []')
        with self.assertRaises(YamlizingError):
            TypeCheck.load(stream)

    @unittest.skip('TODO: type check list')
    def test_typeCheck_badArray(self):
        stream = six.StringIO('one: 1\narray: this gets converted to a list')
        with self.assertRaises(YamlizingError):
            TypeCheck.load(stream)


class Test_to_yaml(unittest.TestCase):

    def test_bad_type(self):
        data = ['this', 'is a list']
        with self.assertRaises(YamlizingError):
            Animal.dump(data)

        stream = 'this is a scalar'
        with self.assertRaises(YamlizingError):
            Animal.load(stream)

    def test_writes_attrs(self):
        poss = Animal('Possum', 5)
        yaml = Animal.dump(poss)
        self.assertIn('name: Possum', yaml)
        self.assertIn('age: 5', yaml)

    def test_bonus_attributes_fail(self):
        poss = Animal('Possum', 5)
        poss.breed = 'awesome'
        yaml = Animal.dump(poss)
        self.assertNotIn('breed', yaml)
        self.assertNotIn('awesome', yaml)

    def test_TypeCheck_good(self):
        tc = TypeCheck(1, 'a bc'.split())
        yaml = TypeCheck.dump(tc)
        self.assertIn('one: 1', yaml)
        self.assertIn('array:', yaml)
        self.assertIn(' bc', yaml)

    def test_TypeCheck_bad(self):
        tc = TypeCheck(1, 99)
        with self.assertRaises(YamlizingError):
            TypeCheck.dump(tc)

        tc = TypeCheck('a', [])
        with self.assertRaises(YamlizingError):
            TypeCheck.dump(tc)

    @unittest.skip('TODO: type check list')
    def test_typeCheck_badArray(self):
        tc = TypeCheck(1, 'this gets converted to a list')
        with self.assertRaises(YamlizingError):
            TypeCheck.dump(tc)


class Test_two_way(unittest.TestCase):

    def test_animal_with_friend(self):
        in_stream = six.StringIO('&possum\n'
                                 'name: Possum\n'
                                 'friend: {name: Maggie, friend: *possum}\n'
                                 )
        poss = AnimalWithFriend.load(in_stream)
        maggie = poss.friend
        self.assertIs(poss, maggie.friend)
        out_stream = six.StringIO()
        AnimalWithFriend.dump(poss, out_stream)
        self.assertEqual(in_stream.getvalue(), out_stream.getvalue())

    def test_sequence(self):

        @yamlizable(Attribute(name='name', type=str))
        class AnimalWithFriends(object):
            pass

        @yaml_list(item_type=AnimalWithFriends)
        class AnimalSequence(object):
            pass

        AnimalWithFriends.attributes.add(Attribute(name='friends',
                                                   type=AnimalSequence,
                                                   default=None))

        in_stream = six.StringIO('# no friends :(\n'
                                 '- name: Lucy # no friends\n'
                                 '- &luna\n'
                                 '  name: Luna\n'
                                 '  friends:\n'
                                 '  - &possum\n'
                                 '    name: Possum\n'
                                 '    friends: [*luna]\n'
                                 '- *possum\n'
                                 )
        animals = AnimalSequence.load(in_stream)

        self.assertTrue(all(isinstance(a, AnimalWithFriends) for a in animals))
        self.assertEqual(animals[1], animals[2].friends[0])
        self.assertEqual(animals[2], animals[1].friends[0])

        out_stream = six.StringIO()
        AnimalSequence.dump(animals, out_stream)
        self.assertEqual(in_stream.getvalue(), out_stream.getvalue())

    def test_pickleable(self):
        in_stream = ('&possum\n'
                     'name: Possum\n'
                     'friend: {name: Maggie, friend: *possum}\n'
                     )
        poss = AnimalWithFriend.load(in_stream)
        assert getattr(sys.modules[__name__], 'AnimalWithFriend') == AnimalWithFriend
        poss2 = pickle.loads(pickle.dumps(poss))
        out_stream = AnimalWithFriend.dump(poss2)
        self.assertNotEqual(in_stream, out_stream)
        poss3 = AnimalWithFriend.load(out_stream)
        self.assertEqual(poss3.name, 'Possum')
        self.assertEqual(poss3.friend.name, 'Maggie')


if __name__ == '__main__':
    unittest.main()

