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


# Creates/binds engine and bootstraps mannord
engine = create_engine('sqlite:///:memory:')
#engine = create_engine("mysql://root:@localhost/mannord_test")
Session = sessionmaker()
mnrd.bind_engine(engine, Session, Base)
session = Session()
mnrd.bootstrap(Base, engine, session, add_computation_record=False)


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

def recreate_tables():
    Base.metadata.drop_all()
    session.expunge_all()
    Base.metadata.create_all()


class TestSpamFlag(unittest.TestCase):

    def test_db_design(self):
        recreate_tables()

        ModeratedAnnotation = ItemMixin.cls
        Action = ActionMixin.cls

        user1 = User()
        user2 = User()
        session.add_all([user1, user2])
        session.flush()

        # Testin parent-child relationship
        annot1 = ModeratedAnnotation('www.example.com', 'annot1', user1)
        annot2 = ModeratedAnnotation('www.example.com', 'annot2', user1,
                                      parent_id='annot1')
        annot3 = ModeratedAnnotation('www.example.com', 'annot3', user2,
                                     parent_id='annot1')
        annot4 = ModeratedAnnotation('www.example.com', 'annot4', user2,
                                     parent_id='annot2')
        session.add_all([annot1, annot2, annot3, annot4])
        session.flush()

        self.assertTrue(annot4.parent_id == 'annot2')
        self.assertTrue(annot3 in annot1.children)
        self.assertTrue(annot4.parent in annot1.children)

        # Testing one-to-one ralation between items and actions
        upvote = Action(annot1.id, user1.id, "upvote", datetime.utcnow(),
                        item_twin_id=annot2.id)
        session.add(upvote)
        session.flush()
        self.assertTrue(upvote.item_twin.id == annot2.id)
        self.assertTrue(annot2.action_twin.id == upvote.id)


if __name__ == '__main__':
    unittest.main()
