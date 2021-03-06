#!/usr/bin/python

from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import unittest

from mannord import (ItemMixin, UserMixin, ActionMixin)
import mannord.spam_utils as su
import mannord.graph_d as gd
import mannord as mnrd

Base = declarative_base()



def print_actions_sk(session):
    actions = ActionMixin.cls.sd_get_actions_offline_spam_detect(session)
    print '\n actions'
    for act in actions:
        print act

def print_items_sk(session):
    items = ItemMixin.cls.sd_get_items_offline_spam_detect(session)
    print "\n items"
    for it in items:
        print it

algo_name = 'dirichlet'

# Creates/binds engine and bootstraps mannord
engine = create_engine('sqlite:///:memory:')
#engine = create_engine("mysql://root:@localhost/mannord_test")
Session = sessionmaker()
mnrd.bind_engine(engine, Session, Base)
session = Session()
mnrd.bootstrap(Base, create_all=True)


def recreate_tables():
    Base.metadata.drop_all()
    session.expunge_all()
    Base.metadata.create_all()


th = gd.get_reliability(0, 0)


class TestSpamFlag(unittest.TestCase):

    def test_spam_flag_dirichlet(self):
        recreate_tables()
        ModeratedAnnotation = ItemMixin.cls
        ModerationUser = UserMixin.cls

        # Creates users and annotations
        user1 = mnrd.get_add_user('user1', session)
        user2 = mnrd.get_add_user('user2', session)
        user3 = mnrd.get_add_user('user3', session)
        annot1 = mnrd.get_add_item('www.example.com', 'annot1', user1,
                                    session, spam_detect_algo=su.ALGO_DIRICHLET)
        annot2 = mnrd.get_add_item('www.example.com', 'annot2', user1,
                                    session, spam_detect_algo=su.ALGO_DIRICHLET)
        annot3 = mnrd.get_add_item('www.example.com', 'annot3', user3,
                                    session, spam_detect_algo=su.ALGO_DIRICHLET)
        session.commit()

        # Adds a flag and deletes it.
        mnrd.raise_spam_flag(annot1, user2, session, algo_name=algo_name)
        mnrd.raise_spam_flag(annot1, user2, session, algo_name=algo_name)
        self.assertTrue(annot1.spam_flag_counter == 1)
        mnrd.run_offline_spam_detection(algo_name, session)
        self.assertTrue(annot1.sd_weight < 0)
        mnrd.raise_ham_flag(annot1, user2, session, algo_name=algo_name)
        mnrd.raise_ham_flag(annot1, user2, session, algo_name=algo_name)
        mnrd.run_offline_spam_detection(algo_name, session)
        self.assertTrue(annot1.spam_flag_counter == 0)
        self.assertTrue(annot1.sd_weight > 0)

        # Adds four flags
        mnrd.raise_spam_flag(annot1, user2, session, algo_name=algo_name)
        mnrd.raise_spam_flag(annot1, user1, session, algo_name=algo_name)
        mnrd.raise_spam_flag(annot2, user2, session, algo_name=algo_name)
        mnrd.raise_spam_flag(annot2, user1, session, algo_name=algo_name)

        mnrd.run_offline_spam_detection(algo_name, session)
        self.assertTrue(annot1.spam_flag_counter == 2)
        self.assertTrue(annot1.sd_weight < 0)
        self.assertTrue(user1.sd_karma_user_reliab < th)
        self.assertTrue(user1.sd_reliab > th)

        # Changing spam to ham
        mnrd.raise_ham_flag(annot1, user2, session, algo_name=algo_name)
        mnrd.raise_ham_flag(annot1, user1, session, algo_name=algo_name)
        mnrd.raise_ham_flag(annot2, user2, session, algo_name=algo_name)
        mnrd.raise_ham_flag(annot2, user1, session, algo_name=algo_name)
        mnrd.run_offline_spam_detection(algo_name, session)
        self.assertTrue(annot1.spam_flag_counter == 0)
        self.assertTrue(annot1.sd_weight > 0)
        self.assertTrue(user1.sd_karma_user_reliab > th)

        # Testing one online update.
        mnrd.raise_spam_flag(annot3, user1, session, algo_name=algo_name)
        val = user1.sd_reliab
        self.assertTrue(annot3.sd_weight < 0)
        mnrd.raise_ham_flag(annot3, user1, session, algo_name=algo_name)
        self.assertTrue(annot3.sd_weight > 0)
        self.assertTrue(user1.sd_reliab > th and user1.sd_reliab < val)

        # Testing karma user.
        annot4 = ModeratedAnnotation('www.example.com', 'annot4', user1,
                                     spam_detect_algo=su.ALGO_DIRICHLET)
        session.add(annot4)
        session.flush()
        self.assertTrue(annot4.sd_weight > th)
        
        items = mnrd.get_n_items_for_spam_mm_randomly(2, session)
        print 'items for spam metamoderation', items
        # Deleting spam item by the author
        mnrd.delete_spam_item_by_author(annot4, session, algo_name=su.ALGO_DIRICHLET)
        annot4_true = ItemMixin.cls.get_item(annot4.id, session)
        self.assertTrue(annot4_true is None)


    def test_spam_flag_dirichlet_2(self):
        recreate_tables()
        ModeratedAnnotation = ItemMixin.cls
        ModerationUser = UserMixin.cls

        # Creates users and annotations
        user1 = mnrd.get_add_user('user1', session)
        user2 = mnrd.get_add_user('user2', session)
        user3 = mnrd.get_add_user('user3', session)
        user4 = mnrd.get_add_user('user4', session)
        user5 = mnrd.get_add_user('user5', session)
        user6 = mnrd.get_add_user('user6', session)
        user7 = mnrd.get_add_user('user7', session)
        annot1 = mnrd.get_add_item('www.example.com', 'annot1', user1,
                                    session, spam_detect_algo=su.ALGO_DIRICHLET)
        annot2 = mnrd.get_add_item('www.example.com', 'annot2', user1,
                                    session, spam_detect_algo=su.ALGO_DIRICHLET)
        annot3 = mnrd.get_add_item('www.example.com', 'annot3', user3,
                                    session, spam_detect_algo=su.ALGO_DIRICHLET)

        # Adds a flag and deletes it.
        #mnrd.raise_spam_flag(annot1, user2, session, algo_name=algo_name)
        #mnrd.raise_spam_flag(annot1, user3, session, algo_name=algo_name)
        #mnrd.raise_spam_flag(annot1, user5, session, algo_name=algo_name)
        mnrd.raise_ham_flag(annot1, user6, session, algo_name=algo_name)
        mnrd.raise_ham_flag(annot1, user4, session, algo_name=algo_name)
        mnrd.run_offline_spam_detection(algo_name, session)
        print 'annot1 spam weight', annot1.sd_weight
        print 'annot2 spam weight', annot2.sd_weight


if __name__ == '__main__':
    unittest.main()
