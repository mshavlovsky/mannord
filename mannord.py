from sqlalchemy import create_engine, and_
from datetime import datetime
from models import (ActionMixin, UserMixin, ItemMixin,
                    ACTION_FLAG_SPAM, ACTION_UPVOTE,
                    ACTION_DOWNVOTE, THRESHOLD_SCORE_SPAM,
                    SCORE_DEFAULT)
import graph_k as gk

ALGO_NAME_KARGER = 'karger'


# todo(michael): tune ALGO_KARGER_* parameters
ALGO_KARGER_K_MAX = 10
ALGO_KARGER_KARMA_USER_VOTE = 0.5
ALGO_KARGER_THRESHOLD_SPAM = -0.7
ALGO_KARGER_THRESHOLD_HAM = 5
# If weight of an item is less than ..._DEFINITELY_SPAM then annotation is
# excluded from offline computations, similarly for  ..._DEFINITELY_HAM
ALGO_KARGER_THRESHOLD_DEFINITELY_SPAM =-2
ALGO_KARGER_THRESHOLD_DEFINITELY_HAM = 10
# Increment for base reliability, user's base reliability changes
# by this amound every time he make an action on an spam/ham annotation.
ALGO_KARGER_BASE_INCREMENT = 1


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
    if algo_type == ALGO_NAME_KARGER:
        run_offline_spam_detect_karger():
    else:
        raise Exception("Unknown algorithm type")

def full_spam_detection_karger(session):
    """ The function
                - fetches action infromation from the db
                - given action information it runs Karger's algorithm
                - it marks anctions and annotations based on the output
                - it writes information back to the db

    todo(michael): note that it possible that on large scale there would be
    not enough memory to hold all information.
    It is possible to make the algorithm work on any scale (process one
    annotation at a time, saving intermediate result into the db, be careful
    about the order, etc.), but premature optimization is evil!
    """
    ActionClass = ActionMixin.cls
    graph = gk.Graph()
    # Fetches all actions
    actions = ActionClass.get_actions_offline_spam_detection(session)
    # todo(michael): fix next line
    items = ItemMixin.get_items_offline_spam_detection(session)
    # Adds flag information (graph.add_answer(...)) to the graph object.
    for act in actions:
        if act.type == ACTION_FLAG_SPAM:
            # Spam flag!
            graph.add_answer(act.user_id, act.item_id, -1,
                base_reliability = act.user.base_reliability_for_spam_detection)
        elif act.type == ACTION_FLAG_HAM or act.type == ACTION_UPVOTE:
            # Ham flag!
            graph.add_answer(act.user_id, act.item_id, 1,
                base_reliability = act.user.base_reliability_for_spam_detection)
        else:
            # The action does not related to vandalizm detection, so ignore it.
            # todo(michael): make sure that after flush() the action is unmarked
            act.participate_in_offline_spam_detection = False
            continue
        # Creates karma user (old "null" user)
        graph.add_answer(-act.user_id, act.item_id, KARMA_USER_VOTE,
                    base_reliability = act.user.base_reliability_for_karma_user)
    # Runs vandalism detection!
    graph.compute_answers(ALGO_KARGER_K_MAX)
    # Marks spam annotations.
    # todo(michael): messy part
    for it in items:
        item_k = graph.get_item()
        if not item_k:
            pass
        if item_k and item_k.weight > ALGO_KARGER_THRESHOLD_DEFINITELY_HAM:
            it.is_spam = False
            it.is_ham = True
            it.participate_offline_spam_detection = False
            # Adds value to the base of users who provided feedback on the item
            # todo(michael): do it

    # Marks annotations and actions which should not participate in further
    # off-line computations
    # Saves information back to the DB
