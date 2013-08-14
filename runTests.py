#!/usr/bin/python

from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import unittest

from models import (ItemMixin, UserMixin, ActionMixin)
import mannord as mnrd

Base = declarative_base()


class User(Base, UserMixin):

    __tablename__ = 'user'

    def __init__(self):
        pass


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


class TestSpamFlag(unittest.TestCase):

    def test_spam_flag_karger(self):
        engine = create_engine('sqlite:///:memory:')
        #engine = create_engine("mysql://root:@localhost/mannord_test")
        Session = sessionmaker()
        mnrd.bind_engine(engine, Session, Base)
        mnrd.bootstrap(Base, engine)
        ModeratedAnnotation = ItemMixin.cls
        session = Session()

        # Creates users and annotations
        user1 = User()
        user2 = User()
        user3 = User()
        session.add(user1)
        session.add(user2)
        session.add(user3)
        session.flush()
        annot1 = ModeratedAnnotation('annot1', user1.id)
        annot2 = ModeratedAnnotation('annot2', user1.id)
        session.add(annot1)
        session.add(annot2)
        session.commit()

        # Adds a flag and deletes it.
        mnrd.raise_spam_flag(annot1, user2, session)
        mnrd.raise_spam_flag(annot1, user2, session)
        self.assertTrue(annot1.spam_flag_counter == 1)
        mnrd.run_offline_spam_detection('karger', session)
        self.assertTrue(annot1.sk_weight < 0)
        mnrd.raise_ham_flag(annot1, user2, session)
        mnrd.raise_ham_flag(annot1, user2, session)
        mnrd.run_offline_spam_detection('karger', session)
        self.assertTrue(annot1.spam_flag_counter == 0)
        self.assertTrue(annot1.sk_weight > 0)

        # Adds four flags
        mnrd.raise_spam_flag(annot1, user2, session)
        mnrd.raise_spam_flag(annot1, user1, session)
        mnrd.raise_spam_flag(annot2, user2, session)
        mnrd.raise_spam_flag(annot2, user1, session)

        mnrd.run_offline_spam_detection('karger', session)
        self.assertTrue(annot1.spam_flag_counter == 2)
        self.assertTrue(annot1.sk_weight < 0)
        self.assertTrue(user1.sk_karma_user_reliab < 0)
        self.assertTrue(user1.sk_reliab > 0)
        self.assertTrue(user1.sk_base_reliab == 0)

        # Changing spam to ham
        mnrd.raise_ham_flag(annot1, user2, session)
        mnrd.raise_ham_flag(annot1, user1, session)
        mnrd.raise_ham_flag(annot2, user2, session)
        mnrd.raise_ham_flag(annot2, user1, session)
        mnrd.run_offline_spam_detection('karger', session)
        self.assertTrue(annot1.spam_flag_counter == 0)
        self.assertTrue(annot1.sk_weight > 0)
        self.assertTrue(user1.sk_karma_user_reliab > 0)


if __name__ == '__main__':
    unittest.main()
