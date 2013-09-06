#!/usr/bin/python
import unittest
import mannord.graph_k as gk


class TestKargerVanilla(unittest.TestCase):

    def test_2negative_against_1(self):
        # Creating users and items.
        g = gk.Graph()
        g.add_answer('u1', 'it1', -1)
        g.add_answer('u1', 'it2', -1)
        g.add_answer('u2', 'it1', -1)
        g.add_answer('u2', 'it2', -1)
        g.add_answer('u3', 'it1', 0.3)
        g.add_answer('u3', 'it2', 0.3)
        # Runs main algo
        g.compute_answers(10)
        u1 = g.get_user('u1')
        u2 = g.get_user('u2')
        u3 = g.get_user('u3')
        it1 = g.get_item('it1')
        it2 = g.get_item('it2')

        self.assertTrue(it1.weight < 0)
        self.assertTrue(it2.weight < 0)
        self.assertTrue(u1.reliability > 0)
        self.assertTrue(u2.reliability > 0)
        self.assertTrue(u3.reliability < 0)

    def test_2_in_agreement(self):
        # Creating users and items.
        g = gk.Graph()
        g.add_answer('u1', 'it1', -1)
        g.add_answer('u1', 'it2', -1)
        g.add_answer('u2', 'it1', -1)
        g.add_answer('u2', 'it2', -1)
        # Runs main algo
        g.compute_answers(10)
        u1 = g.get_user('u1')
        u2 = g.get_user('u2')
        it1 = g.get_item('it1')
        it2 = g.get_item('it2')

        self.assertTrue(it1.weight < 0)
        self.assertTrue(it2.weight < 0)
        self.assertTrue(u1.reliability > 0)
        self.assertTrue(u2.reliability > 0)

    def test_single_action(self):
        g = gk.Graph()
        g.add_answer('u1', 'it1', 1)
        # Runs main algo
        g.compute_answers(10)
        u1 = g.get_user('u1')
        it1 = g.get_item('it1')
        self.assertTrue(it1.weight > 0)


    def test_2_against_1(self):
        # Creating users and items.
        g = gk.Graph()
        g.add_answer('u1', 'it1', 1)
        g.add_answer('u1', 'it2', 1)
        g.add_answer('u1', 'it3', 1)
        g.add_answer('u2', 'it1', 1)
        g.add_answer('u2', 'it2', 1)
        g.add_answer('u2', 'it3', 1)
        g.add_answer('u3', 'it1', -1)
        g.add_answer('u3', 'it2', -1)
        # Runs main algo
        g.compute_answers(10)
        u1 = g.get_user('u1')
        u2 = g.get_user('u2')
        u3 = g.get_user('u3')
        it1 = g.get_item('it1')
        it2 = g.get_item('it2')
        it3 = g.get_item('it3')

        self.assertTrue(it1.weight > 0)
        self.assertTrue(it2.weight > 0)
        self.assertTrue(it3.weight > 0)
        self.assertTrue(u1.reliability > 0)
        self.assertTrue(u2.reliability > 0)
        self.assertTrue(u3.reliability < 0)

    def test_4_against_2(self):
        # Creating users and items.
        g = gk.Graph()
        g.add_answer('u1', 'it1', 1)
        g.add_answer('u1', 'it2', 1)
        g.add_answer('u2', 'it1', 1)
        g.add_answer('u2', 'it2', 1)
        g.add_answer('u3', 'it1', 1)
        g.add_answer('u3', 'it2', 1)
        g.add_answer('u4', 'it1', 1)
        g.add_answer('u4', 'it2', 1)
        g.add_answer('u5', 'it1', -1)
        g.add_answer('u5', 'it2', -1)
        g.add_answer('u6', 'it1', -1)
        g.add_answer('u6', 'it2', -1)
        # User 7 is not consistend with anybody.
        g.add_answer('u7', 'it1', -1)
        g.add_answer('u7', 'it2', +1)
        # Runs main algo
        g.compute_answers(100)
        u1 = g.get_user('u1')
        u5 = g.get_user('u5')
        u7 = g.get_user('u7')
        it1 = g.get_item('it1')
        it2 = g.get_item('it2')

        self.assertTrue(it1.weight > 0)
        self.assertTrue(it2.weight > 0)
        self.assertTrue(u1.reliability > 0)
        self.assertTrue(u5.reliability < 0)


    def test_2small_against_1big(self):
        # Creating users and items.
        g = gk.Graph()
        g.add_answer('u1', 'it1', 1)
        g.add_answer('u1', 'it2', 1)
        g.add_answer('u2', 'it1', 1)
        #g.add_answer('u2', 'it2', 0.7)
        # Runs main algo
        g.compute_answers(10)
        u1 = g.get_user('u1')
        u2 = g.get_user('u2')
        u3 = g.get_user('u3')
        it1 = g.get_item('it1')
        it2 = g.get_item('it2')

        self.assertTrue(it1.weight > 0)
        self.assertTrue(it2.weight > 0)
        self.assertTrue(u1.reliability > 0)
        self.assertTrue(u2.reliability > 0)


    ##todo(michael): this function is temporary
    #def test_temp(self):
    #    """ An example when a user have lots of agreement can significantly
    #    overweigh new user."""
    #    g = gk.Graph()
    #    g.add_answer('u1', 'it1', 1)
    #    g.add_answer('u1', 'it2', 1)

    #    g.add_answer('u2', 'it1', 1)
    #    g.add_answer('u2', 'it2', 1)

    #    for i in xrange(4, 100, 1):
    #        g.add_answer('u2', 'it%s' % i, 1)

    #    for i in xrange(4, 100, 1):
    #        g.add_answer('u3', 'it%s' % i, 1)

    #    g.compute_answers(100)
    #    u1 = g.get_user('u1')
    #    u2 = g.get_user('u2')
    #    it1 = g.get_item('it1')
    #    it2 = g.get_item('it2')
    #    print
    #    print u1.reliability
    #    print u2.reliability
    #    print it1.weight
    #    print it2.weight
    #    print g.normaliz


if __name__ == '__main__':
    unittest.main()
