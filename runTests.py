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

    def __init__(self):
        pass


class ModeratedAnnotation(Base, ItemMixin):

    def __init__(self, annotation_id, user_id):
        self.id = annotation_id
        self.author_id = user_id


#class Action(ActionMixin, Base):
#
#    def __init__(self, annotation_id, user_id, action_type, value, timestamp):
#        super(Action, self).__init__(annotation_id, user_id,
#                                     action_type, value, timestamp)



class TestSpamFlag(unittest.TestCase):

    def test_flag(self):
        engine = create_engine('sqlite:///:memory:')
        Session = sessionmaker()
        bind_engine(engine, Session, Base)
        bootstrap(Base, engine)
        session = Session()


        # Create users and annotations
        user1 = User()
        user2 = User()
        user3 = User()
        session.add(user1)
        session.add(user2)
        session.add(user3)
        session.flush()
        annot1 = ModeratedAnnotation('annot1', user1.id)
        session.add(annot1)
        session.commit()

        # Adding two flags
        flag_as_spam(annot1, user2, datetime.utcnow(), session)
        self.assertTrue(annot1.spam_flag_counter == 1)
        self.assertTrue(annot1.is_spam == False)
        self.assertTrue(annot1.score == THRESHOLD_SCORE_SPAM)
        flag_as_spam(annot1, user3, datetime.utcnow(), session)
        self.assertTrue(annot1.score == 0)
        self.assertTrue(annot1.is_spam == True)
        self.assertTrue(annot1.spam_flag_counter == 2)

        # Deleting two flags
        undo_flag_as_spam(annot1, user2, session)
        self.assertTrue(annot1.is_spam == True)
        self.assertTrue(user1.score == THRESHOLD_SCORE_SPAM)
        self.assertTrue(annot1.spam_flag_counter == 1)
        undo_flag_as_spam(annot1, user3, session)
        self.assertTrue(annot1.is_spam == False)
        self.assertTrue(user1.score == SCORE_DEFAULT)
        self.assertTrue(annot1.spam_flag_counter == 0)


if __name__ == '__main__':
    unittest.main()
