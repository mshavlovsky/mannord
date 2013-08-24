#!/usr/bin/python

import unittest
import hits


class TestHITS(unittest.TestCase):

    def test_hits(self):
        g = hits.Graph()
        g.add_link('u1', 'it1', 1)
        g.add_link('u1', 'it2', 1)
        g.add_link('u2', 'it2', 1)
        print g
        g.hubs_and_authorities(10)
        u1 = g.get_user('u1')
        u2 = g.get_user('u2')
        it1 = g.get_item('it1')
        it2 = g.get_item('it2')
        self.assertTrue(u1.hub_weight > u2.hub_weight)
        self.assertTrue(it1.auth_weight < it2.auth_weight)


if __name__ == '__main__':
    unittest.main()
