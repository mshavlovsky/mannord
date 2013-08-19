#!/usr/bin/python
import unittest
import graph_d as gd

# Behaviour of the aglorithm depends on how we compute user's reliability.
# We can listen to a user (reliability > 0) only if we have some agreement
# with someone, so this way a new user has zero reliability in spam detection.
# We can listen to a new user by assigning small positive reliability by default
# As for now, a new user has some trust.

class TestDirichletVanilla(unittest.TestCase):

    def test_single_action(self):
        g = gd.Graph()
        g.add_answer('u1', 'it1', 1)
        # Runs main algo
        g.compute_answers(10)
        u1 = g.get_user('u1')
        it1 = g.get_item('it1')
        self.assertTrue(it1.weight > 0)


    def test_2_user_in_agreemnt(self):
        # Creating users and items.
        g = gd.Graph()
        th = gd.get_reliability(0, 0)
        g.add_answer('u1', 'it1', -1)
        g.add_answer('u2', 'it1', -1)
        # Runs main algo
        g.compute_answers(10)
        u1 = g.get_user('u1')
        it1 = g.get_item('it1')

        self.assertTrue(u1.reliability > th)
        self.assertTrue(it1.weight < 0)

    def test_2_user_in_agreemnt_neg(self):
        # Creating users and items.
        g = gd.Graph()
        th = gd.get_reliability(0, 0)
        g.add_answer('u1', 'it1', -1)
        g.add_answer('u1', 'it2', -1)
        g.add_answer('u2', 'it1', -1)
        g.add_answer('u2', 'it2', -1)
        # Runs main algo
        g.compute_answers(10)
        u1 = g.get_user('u1')
        it1 = g.get_item('it1')

        self.assertTrue(it1.weight < 0)
        self.assertTrue(u1.reliability > th)

    def test_2_users_disagree(self):
        # Creating users and items.
        g = gd.Graph()
        g.add_answer('u1', 'it1', 1)
        g.add_answer('u2', 'it1', -1)
        # Runs main algo
        g.compute_answers(10)
        u1 = g.get_user('u1')
        u2 = g.get_user('u2')
        it1 = g.get_item('it1')

        self.assertTrue(it1.weight > 0)

    def test_2_agains_1(self):
        # Creating users and items.
        g = gd.Graph()
        th = gd.get_reliability(0, 0)
        g.add_answer('u1', 'it1', 1)
        g.add_answer('u1', 'it2', 1)
        g.add_answer('u1', 'it3', -1)
        g.add_answer('u2', 'it1', 1)
        g.add_answer('u2', 'it2', 1)
        g.add_answer('u2', 'it3', -1)
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
        self.assertTrue(it3.weight < 0)
        self.assertTrue(u1.reliability > th)
        self.assertTrue(u2.reliability > th)

        self.assertTrue(u3.reliability < th)

if __name__ == '__main__':
    unittest.main()
