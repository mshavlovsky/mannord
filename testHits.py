#!/usr/bin/python

import unittest
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import (ItemMixin, UserMixin, ActionMixin)
import hits
import mannord as mnrd


Base = declarative_base()


class User(Base, UserMixin):

    __tablename__ = 'user'

    def __init__(self):
        pass


class TestHITS(unittest.TestCase):

    def test_hits_basic(self):
        g = hits.Graph()
        g.add_link('u1', 'it1', 1)
        g.add_link('u1', 'it2', 1)
        g.add_link('u2', 'it2', 1)
        g.hubs_and_authorities(10)
        u1 = g.get_user('u1')
        u2 = g.get_user('u2')
        it1 = g.get_item('it1')
        it2 = g.get_item('it2')
        self.assertTrue(u1.hub_weight > u2.hub_weight)
        self.assertTrue(it1.auth_weight < it2.auth_weight)

    def test_hits(self):
        g = hits.Graph()
        g.add_link('u1', 'it1', 1)
        g.add_link('u1', 'it2', 1)
        g.add_link('u2', 'it2', 1)
        g.add_link('u2', 'it3', 1)
        g.add_link('u3', 'it1', 1)
        g.add_link('u3', 'it2', 1)
        g.add_link('u3', 'it3', 1)
        g.hubs_and_authorities(10)
        n_users = g.get_n_top_users(3, 'u2')
        self.assertTrue(n_users[0] == 'u3')
        self.assertTrue(n_users[1] == 'u1')
        self.assertTrue(len(n_users) == 2)
        n_items = g.get_n_top_items(10)
        self.assertTrue(len(n_items) == 3)
        self.assertTrue(n_items[0] == 'it2')

    def test_hits_db(self):
        engine = create_engine('sqlite:///:memory:')
        #engine = create_engine("mysql://root:@localhost/mannord_test")
        Session = sessionmaker()
        session = Session()
        mnrd.bind_engine(engine, Session, Base)
        mnrd.bootstrap(Base, engine, session)
        ModeratedAnnotation = ItemMixin.cls

        # Creates users and annotations
        user1 = User()
        user2 = User()
        user3 = User()
        user4 = User()
        user5 = User()
        session.add_all([user1, user2, user3, user4, user5])
        session.flush()
        annot1 = ModeratedAnnotation('www.example1.com', 'annot1', user1)
        annot2 = ModeratedAnnotation('www.example1.com', 'annot2', user2)
        annot3 = ModeratedAnnotation('www.example1.com', 'annot3', user3)
        annot4 = ModeratedAnnotation('www.example2.com', 'annot4', user1)
        annot5 = ModeratedAnnotation('www.example2.com', 'annot5', user1)
        annot6 = ModeratedAnnotation('www.example2.com', 'annot6', user3)
        annot7 = ModeratedAnnotation('www.example3.com', 'annot7', user2)
        annot8 = ModeratedAnnotation('www.example3.com', 'annot8', user2)
        annot9 = ModeratedAnnotation('www.example3.com', 'annot9', user3)
        annot10 = ModeratedAnnotation('www.example3.com', 'annot10', user4)
        annot11 = ModeratedAnnotation('www.example4.com', 'annot11', user5)
        session.add_all([annot1, annot2, annot3, annot4, annot5, annot6,
                         annot7, annot8, annot9, annot10, annot11])
        mnrd.raise_ham_flag(annot1, user3, session)
        session.flush()

        n_items = mnrd.suggest_n_users_to_review(annot8,4, session)
        self.assertTrue(n_items[0] == user3.id)
        self.assertTrue(n_items[2] == user4.id)
        self.assertTrue(len(n_items) == 3)


if __name__ == '__main__':
    unittest.main()
