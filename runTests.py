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

    def test_db_design(self):
        engine = create_engine('sqlite:///:memory:')
        Session = sessionmaker()
        session = Session()
        mnrd.bind_engine(engine, Session, Base)
        mnrd.bootstrap(Base, engine, session)
        ModeratedAnnotation = ItemMixin.cls
        Action = ActionMixin.cls

        user1 = User()
        user2 = User()
        session.add_all([user1, user2])
        session.flush()

        # Testin parent-child relationship
        annot1 = ModeratedAnnotation('annot1', user1)
        annot2 = ModeratedAnnotation('annot2', user1, parent_id='annot1')
        annot3 = ModeratedAnnotation('annot3', user2, parent_id='annot1')
        annot4 = ModeratedAnnotation('annot4', user2, parent_id='annot2')
        session.add_all([annot1, annot2, annot3, annot4])
        session.flush()

        self.assertTrue(annot4.parent_id == 'annot2')
        self.assertTrue(annot3 in annot1.children)
        self.assertTrue(annot4.parent in annot1.children)

        # Testing one-to-one ralation between items and actions
        upvote = Action('annot1', user1.id, "upvote", datetime.utcnow(),
                        item_twin_id=annot1.id)
        session.flush()
        self.assertTrue(annot1.action_twin.id == upvote.id)


#    def test_spam_flag_karger(self):
#        engine = create_engine('sqlite:///:memory:')
#        #engine = create_engine("mysql://root:@localhost/mannord_test")
#        Session = sessionmaker()
#        session = Session()
#        mnrd.bind_engine(engine, Session, Base)
#        mnrd.bootstrap(Base, engine, session)
#        ModeratedAnnotation = ItemMixin.cls
#
#        # Creates users and annotations
#        user1 = User()
#        user2 = User()
#        user3 = User()
#        session.add(user1)
#        session.add(user2)
#        session.add(user3)
#        session.flush()
#        annot1 = ModeratedAnnotation('annot1', user1)
#        annot2 = ModeratedAnnotation('annot2', user1)
#        annot3 = ModeratedAnnotation('annot3', user3)
#        session.add(annot1)
#        session.add(annot2)
#        session.add(annot3)
#        session.commit()
#
#        # Adds a flag and deletes it.
#        mnrd.raise_spam_flag(annot1, user2, session)
#        mnrd.raise_spam_flag(annot1, user2, session)
#        self.assertTrue(annot1.spam_flag_counter == 1)
#        mnrd.run_offline_spam_detection('karger', session)
#        self.assertTrue(annot1.sk_weight < 0)
#        mnrd.raise_ham_flag(annot1, user2, session)
#        mnrd.raise_ham_flag(annot1, user2, session)
#        mnrd.run_offline_spam_detection('karger', session)
#        self.assertTrue(annot1.spam_flag_counter == 0)
#        self.assertTrue(annot1.sk_weight > 0)
#
#        # Adds four flags
#        mnrd.raise_spam_flag(annot1, user2, session)
#        mnrd.raise_spam_flag(annot1, user1, session)
#        mnrd.raise_spam_flag(annot2, user2, session)
#        mnrd.raise_spam_flag(annot2, user1, session)
#
#        mnrd.run_offline_spam_detection('karger', session)
#        self.assertTrue(annot1.spam_flag_counter == 2)
#        self.assertTrue(annot1.sk_weight < 0)
#        self.assertTrue(user1.sk_karma_user_reliab < 0)
#        self.assertTrue(user1.sk_reliab > 0)
#        self.assertTrue(user1.sk_base_reliab == 0)
#
#        # Changing spam to ham
#        mnrd.raise_ham_flag(annot1, user2, session)
#        mnrd.raise_ham_flag(annot1, user1, session)
#        mnrd.raise_ham_flag(annot2, user2, session)
#        mnrd.raise_ham_flag(annot2, user1, session)
#        mnrd.run_offline_spam_detection('karger', session)
#        self.assertTrue(annot1.spam_flag_counter == 0)
#        self.assertTrue(annot1.sk_weight > 0)
#        self.assertTrue(user1.sk_karma_user_reliab > 0)
#
#        # Testing one online update.
#        mnrd.raise_spam_flag(annot3, user1, session)
#        val = user1.sk_reliab
#        self.assertTrue(annot3.sk_weight < 0)
#        mnrd.raise_ham_flag(annot3, user1, session)
#        self.assertTrue(annot3.sk_weight > 0)
#        self.assertTrue(user1.sk_reliab > 0 and user1.sk_reliab < val)
#
#        # Testing karma user.
#        annot4 = ModeratedAnnotation('annot4', user1)
#        session.add(annot4)
#        session.flush()
#        self.assertTrue(annot4.sk_weight > 0)


if __name__ == '__main__':
    unittest.main()
