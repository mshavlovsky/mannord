from sqlalchemy import create_engine, and_
from datetime import datetime
import numpy as np
from models import (ActionMixin, UserMixin, ItemMixin, ComputationMixin,
                    COMPUTATION_SK_NAME)


import spam_detection_karger as sdk
import spam_detection_dirichlet as sdd

ALGO_NAME_KARGER = 'karger'
ALGO_NAME_DIRICHLET = 'dirichlet'


def bind_engine(engine, session, base, should_create=True):
    session.configure(bind=engine)
    base.metadata.bind = engine
    if should_create:
        base.metadata.create_all(engine)


def bootstrap(base, engine, session):
    class Computation(ComputationMixin, base):
        pass
    class Action(ActionMixin, base):
        pass

    class ModeratedAnnotation(ItemMixin, base):
        def __init__(self, annotation_id, user_id):
            self.id = annotation_id
            self.author_id = user_id

    base.metadata.create_all(engine)

    session.add(Computation(COMPUTATION_SK_NAME))
    session.flush()

    ActionMixin.cls = Action
    ItemMixin.cls = ModeratedAnnotation
    ComputationMixin.cls = Computation


def name_check(algo_name):
    if algo_name != ALGO_NAME_KARGER and algo_name != ALGO_NAME_DIRICHLET:
        raise Exception("Unknown algorithm !")


def bootstrap_check():
    if (ActionMixin.cls is None or
        ItemMixin.cls is None or
        ComputationMixin.cls is None):
        raise Exception("You forgot to bootstrap the mannord!")


def run_offline_spam_detection(algo_name, session):
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


def raise_spam_flag(item, user, session, algo_name=ALGO_NAME_KARGER):
    timestamp = datetime.utcnow()
    bootstrap_check()
    if algo_name == ALGO_NAME_KARGER:
        sdk.flag_spam(item, user, timestamp, session)
    else:
        sdd.flag_spam(item, user, timestamp, session)
        pass


def raise_ham_flag(item, user, session, algo_name=ALGO_NAME_KARGER):
    timestamp = datetime.utcnow()
    bootstrap_check()
    if algo_name == ALGO_NAME_KARGER:
        sdk.flag_ham(item, user, timestamp, session)
    else:
        sdd.flag_ham(item, user, timestamp, session)
        pass
