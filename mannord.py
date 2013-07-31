from sqlalchemy import create_engine, and_
from datetime import datetime
from models import (ActionMixin, UserMixin, ItemMixin,
                    ACTION_FLAG_SPAM, ACTION_UPVOTE,
                    ACTION_DOWNVOTE, THRESHOLD_SCORE_SPAM,
                    SCORE_DEFAULT)

ALGO_KARGER_K_MAX = 10
ALGO_KARGER_KARMA_USER_VOTE = 0.5


def bind_engine(engine, session, base, should_create=True):
    # todo(michael): do I need to bind session? I don't use anywhere.
    session.configure(bind=engine)
    base.metadata.bind = engine
    if should_create:
        base.metadata.create_all(engine)


def bootstrap(base,engine):
    class Action(ActionMixin, base):
        pass
    base.metadata.create_all(engine)
    ActionMixin.cls = Action


def run_offline_spam_detection(algo_name):
    """ Method runs complete spam detection algorithm.
    """
    if ActionMixin.cls is None:
        raise Exception("You forgot to bootstrap the mannord!")
    if algo_type == 'karger':
        run_offline_spam_detect_karger():
    else:
        raise Exception("Unknown algorithm type")

def full_spam_detection_karger():
    # Fetch all actions
    # Fetch all annotations
    # Create Karma user(old 'null' user)
