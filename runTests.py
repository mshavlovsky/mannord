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


class TestSpamFlag(unittest.TestCase):

    def test_spam_flag_karger(self):
        engine = create_engine('sqlite:///:memory:')
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
        actions = ActionMixin.cls.sk_get_actions_offline_spam_detect(session)
        print 'action length', len(actions)
        self.assertTrue(annot1.spam_flag_counter == 1)
        mnrd.raise_ham_flag(annot1, user2, session)
        self.assertTrue(annot1.spam_flag_counter == 0)
        self.assertTrue(annot1.sk_weight == 0)

        # Adding two flags
        mnrd.raise_spam_flag(annot1, user2, session)
        mnrd.raise_spam_flag(annot1, user1, session)
        mnrd.raise_spam_flag(annot2, user2, session)
        mnrd.raise_spam_flag(annot2, user1, session)
        mnrd.run_offline_spam_detection('karger', session)
        self.assertTrue(annot1.spam_flag_counter == 2)
        print annot1.sk_weight
        self.assertTrue(annot1.sk_weight < 0)
        #flag_as_spam(annot1, user3, datetime.utcnow(), session)
        #self.assertTrue(annot1.score == 0)
        #self.assertTrue(annot1.is_spam == True)
        #self.assertTrue(annot1.spam_flag_counter == 2)

        ## Deleting two flags
        #undo_flag_as_spam(annot1, user2, session)
        #self.assertTrue(annot1.is_spam == True)
        #self.assertTrue(user1.score == THRESHOLD_SCORE_SPAM)
        #self.assertTrue(annot1.spam_flag_counter == 1)
        #undo_flag_as_spam(annot1, user3, session)
        #self.assertTrue(annot1.is_spam == False)
        #self.assertTrue(user1.score == SCORE_DEFAULT)
        #self.assertTrue(annot1.spam_flag_counter == 0)


if __name__ == '__main__':
    unittest.main()
