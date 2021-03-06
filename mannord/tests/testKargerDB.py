#!/usr/bin/python

from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import unittest

from mannord import (ItemMixin, UserMixin, ActionMixin, ComputationMixin)
import mannord as mnrd
import mannord.spam_utils as su

Base = declarative_base()



def print_actions_sk(session):
    actions = ActionMixin.cls.sk_get_actions_offline_spam_detect(session)
    print '\n actions'
    for act in actions:
        print act

def print_items_sk(session):
    items = ItemMixin.cls.sk_get_items_offline_spam_detect(session)
    print "\n items"
    for it in items:
        print it

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
    session.flush()


class TestSpamFlag(unittest.TestCase):

    def test_spam_flag_karger(self):
        recreate_tables()
        ModeratedAnnotation = ItemMixin.cls
        ModerationUser = UserMixin.cls

        # Creates users and annotations
        user1 = ModerationUser('user1')
        user2 = ModerationUser('user2')
        user3 = ModerationUser('user3')
        session.add_all([user1, user2, user3])
        session.flush()
        annot1 = ModeratedAnnotation('www.example.com', 'annot1', user1,
                                            spam_detect_algo=su.ALGO_KARGER)
        annot2 = ModeratedAnnotation('www.example.com', 'annot2', user1,
                                            spam_detect_algo=su.ALGO_KARGER)
        annot3 = ModeratedAnnotation('www.example.com', 'annot3', user3,
                                            spam_detect_algo=su.ALGO_KARGER)
        session.add_all([annot1, annot2, annot3])
        session.commit()

        # Adds a flag and deletes it.
        mnrd.raise_spam_flag(annot1, user2, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_spam_flag(annot1, user2, session, algo_name = su.ALGO_KARGER)
        self.assertTrue(annot1.spam_flag_counter == 1)
        mnrd.run_offline_spam_detection(su.ALGO_KARGER, session)
        self.assertTrue(annot1.sk_weight < 0)
        mnrd.raise_ham_flag(annot1, user2, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_ham_flag(annot1, user2, session, algo_name = su.ALGO_KARGER)
        mnrd.run_offline_spam_detection('karger', session)
        self.assertTrue(annot1.spam_flag_counter == 0)
        self.assertTrue(annot1.sk_weight > 0)

        # Adds four flags
        mnrd.raise_spam_flag(annot1, user2, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_spam_flag(annot1, user1, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_spam_flag(annot2, user2, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_spam_flag(annot2, user1, session, algo_name = su.ALGO_KARGER)

        mnrd.run_offline_spam_detection('karger', session)
        self.assertTrue(annot1.spam_flag_counter == 2)
        self.assertTrue(annot1.sk_weight < 0)
        self.assertTrue(user1.sk_karma_user_reliab < 0)
        self.assertTrue(user1.sk_reliab > 0)
        self.assertTrue(user1.sk_base_reliab == 0)

        # Changing spam to ham
        mnrd.raise_ham_flag(annot1, user2, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_ham_flag(annot1, user1, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_ham_flag(annot2, user2, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_ham_flag(annot2, user1, session, algo_name = su.ALGO_KARGER)
        mnrd.run_offline_spam_detection('karger', session)
        self.assertTrue(annot1.spam_flag_counter == 0)
        self.assertTrue(annot1.sk_weight > 0)
        self.assertTrue(user1.sk_karma_user_reliab > 0)

        # Testing one online update.
        mnrd.raise_spam_flag(annot3, user1, session, algo_name = su.ALGO_KARGER)
        val = user1.sk_reliab
        self.assertTrue(annot3.sk_weight < 0)
        mnrd.raise_ham_flag(annot3, user1, session, algo_name = su.ALGO_KARGER)
        self.assertTrue(annot3.sk_weight > 0)
        self.assertTrue(user1.sk_reliab > 0 and user1.sk_reliab < val)

        # Testing karma user.
        annot4 = ModeratedAnnotation('www.example.com', 'annot4', user1,
                                            spam_detect_algo=su.ALGO_KARGER)
        session.add(annot4)
        session.flush()
        self.assertTrue(annot4.sk_weight > 0)

        items = mnrd.get_n_items_for_spam_mm_randomly(2, session)
        print 'items for spam metamoderation', items
        # Deleting spam item by the author
        mnrd.delete_spam_item_by_author(annot4, session, algo_name = su.ALGO_KARGER)
        annot4_true = ItemMixin.cls.get_item(annot4.id, session)
        self.assertTrue(annot4_true is None)


    def test_spam_flag_karger_2(self):
        recreate_tables()
        ModeratedAnnotation = ItemMixin.cls
        ModerationUser = UserMixin.cls

        # Creates users and annotations
        user1 = ModerationUser('user1')
        user2 = ModerationUser('user2')
        user3 = ModerationUser('user3')
        user4 = ModerationUser('user4')
        user5 = ModerationUser('user5')

        session.add_all([user1, user2, user3, user4, user5])
        session.flush()
        annot1 = ModeratedAnnotation('www.example.com', 'annot1', user1,
                                            spam_detect_algo=su.ALGO_KARGER)
        annot2 = ModeratedAnnotation('www.example.com', 'annot2', user2,
                                            spam_detect_algo=su.ALGO_KARGER)
        annot3 = ModeratedAnnotation('www.example.com', 'annot3', user3,
                                            spam_detect_algo=su.ALGO_KARGER)
        session.add_all([annot1, annot2, annot3])
        session.commit()

        # Adds a flag and deletes it.
        mnrd.raise_spam_flag(annot1, user2, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_spam_flag(annot1, user3, session, algo_name = su.ALGO_KARGER)
        mnrd.raise_ham_flag(annot2, user3, session, algo_name = su.ALGO_KARGER)
        mnrd.run_offline_spam_detection('karger', session)
        print 'annot1 spam weight', annot1.sk_weight
        print 'annot2 spam weight', annot2.sk_weight


if __name__ == '__main__':
    unittest.main()
