#!/usr/bin/python

from models import *
from mannord import *
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import unittest

Base = declarative_base()


class User(Base, UserMixin):

    __tablename__ = 'user'

    def __init__(self, user_email):
        self.email = user_email


class Annotation(Base, ItemMixin):


    def __init__(self, annotation_id, user_email):
        self.id = annotation_id
        self.author_email = user_email

class Action(ActionMixin, Base):

    def __init__(self, annotation_id, user_id, action_type, value, timestamp):
        super(Action, self).__init__(annotation_id, user_id,
                                     action_type, value, timestamp)



class TestSpamFlag(unittest.TestCase):

    def test_flag(self):
        engine = create_engine('sqlite:///:memory:')
        Session = sessionmaker()
        bind_engine(engine, Session, Base)
        session = Session()

        # Create users and annotations
        user1 = User('user1')
        user2 = User('user2')
        user3 = User('user3')
        annot1 = Annotation('annot1', 'user1')
        session.add(user1)
        session.add(user2)
        session.add(user3)
        session.add(annot1)
        session.commit()

        # Adding two flags
        flag_as_spam(annot1, user2, datetime.utcnow(), session, Action)
        self.assertTrue(annot1.spam_flag_counter == 1)
        self.assertTrue(annot1.is_spam == False)
        self.assertTrue(annot1.score == THRESHOLD_SCORE_SPAM)
        flag_as_spam(annot1, user3, datetime.utcnow(), session, Action)
        self.assertTrue(annot1.score == 0)
        self.assertTrue(annot1.is_spam == True)
        self.assertTrue(annot1.spam_flag_counter == 2)

        # Deleting two flags
        undo_flag_as_spam(annot1, user2, session, Action)
        self.assertTrue(annot1.is_spam == True)
        self.assertTrue(user1.score == THRESHOLD_SCORE_SPAM)
        self.assertTrue(annot1.spam_flag_counter == 1)
        undo_flag_as_spam(annot1, user3, session, Action)
        self.assertTrue(annot1.is_spam == False)
        self.assertTrue(user1.score == SCORE_DEFAULT)
        self.assertTrue(annot1.spam_flag_counter == 0)


if __name__ == '__main__':
    unittest.main()
