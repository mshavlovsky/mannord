from sqlalchemy import create_engine, and_
from datetime import datetime
import numpy as np
from models import (ActionMixin, UserMixin, ItemMixin,
                    ACTION_FLAG_SPAM, ACTION_FLAG_HAM,
                    ACTION_UPVOTE, ACTION_DOWNVOTE,
                    THRESHOLD_SCORE_SPAM, SCORE_DEFAULT)

import spam_detection_karger as sdk
import spam_detection_dirichlet as sdd

ALGO_NAME_KARGER = 'karger'
ALGO_NAME_DIRICHLET = 'dirichlet'


def bind_engine(engine, session, base, should_create=True):
    session.configure(bind=engine)
    base.metadata.bind = engine
    if should_create:
        base.metadata.create_all(engine)


def bootstrap(base,engine, UserClass, ItemClass):
    class Action(ActionMixin, base):
        pass
    base.metadata.create_all(engine)
    ActionMixin.cls = Action
    # todo(michael): create ItemClass here and User class can be known from
    UserMixin.cls = UserClass
    ItemClass.cls = ItemClass


def name_check(algo_name):
    if algo_name != ALGO_NAME_KARGER or algo_name != ALGO_NAME_DIRICHLET:
        raise Exception("Unknown algorithm !")


def bootstrap_check():
    if ActionMixin.cls is None:
        raise Exception("You forgot to bootstrap the mannord!")


def offline_spam_detection(algo_name, session):
    """ Method runs offline spam detection. """
    # Some initial chenking.
    name_check(algo_name)
    bootstrap_check()
    # Obtains class names to perform db querries later.
    if algo_name == ALGO_NAME_KARGER:
        sdk.run_offline_computations(session)
    else:
        sdd.run_offline_computations(session)
        pass
    session.flush()


def flag_spam(item, user, session, algo_name=ALGO_NAME_KARGER):
    timestamp = datetime.utcnow()
    bootstrap_check()
    if algo_name == ALGO_NAME_KARGER:
        sdk.flag_spam(item, user, timestamp, session)
    else:
        sdd.flag_spam(item, user, timestamp, session)
        pass


def flag_ham(item, user, session, algo_name=ALGO_NAME_KARGER):
    timestamp = datetime.utcnow()
    bootstrap_check()
    if algo_name == ALGO_NAME_KARGER:
        sdk.flag_ham(item, user, timestamp, session)
    else:
        sdd.flag_ham(item, user, timestamp, session)
        pass
