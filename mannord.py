from sqlalchemy import create_engine, and_
from datetime import datetime
import numpy as np
from models import (ActionMixin, UserMixin, ItemMixin, ComputationMixin,
                    COMPUTATION_SK_NAME)


import spam_detection_karger as sdk
import spam_detection_dirichlet as sdd
import hitsDB

ALGO_NAME_KARGER = 'karger'
ALGO_NAME_DIRICHLET = 'dirichlet'


def bind_engine(engine, session, base, should_create=True):
    session.configure(bind=engine)
    base.metadata.bind = engine
    if should_create:
        base.metadata.create_all(engine)


def bootstrap(base, engine, session, add_computation_record=True):
    class Computation(ComputationMixin, base):
        pass

    class Action(ActionMixin, base):
        pass

    class ModeratedAnnotation(ItemMixin, base):
        pass

    base.metadata.create_all(engine)
    if add_computation_record:
        session.add(Computation(COMPUTATION_SK_NAME))
        session.flush()

    ActionMixin.cls = Action
    ItemMixin.cls = ModeratedAnnotation
    ComputationMixin.cls = Computation


def add_computation_record(base, engine, session):
        if not ComputationMixin.cls is None:
            session.add(ComputationMixin.cls(COMPUTATION_SK_NAME))
        else:
            raise Exception("Mannord has not been bootrstraped!")
        session.flush()

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


def suggest_n_users_to_review(item, n, session):
    if item is None or item.page_url is None:
        return []
    n_users = hitsDB.suggest_n_users_to_review(item, n, session)
    if len(n_users) < n:
        # todo(michael): do random sampling (or some criteria)
        pass
    return n_users
