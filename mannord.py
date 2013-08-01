from sqlalchemy import create_engine, and_
from datetime import datetime
from models import (ActionMixin, UserMixin, ItemMixin,
                    ACTION_FLAG_SPAM, ACTION_UPVOTE,
                    ACTION_DOWNVOTE, THRESHOLD_SCORE_SPAM,
                    SCORE_DEFAULT)
import graph_k as gk

ALGO_KARGER_K_MAX = 10
ALGO_KARGER_KARMA_USER_VOTE = 0.5
ALGO_NAME_KARGER = 'karger'


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
    # todo(michael): note that it possible that on large scale there would be
    # not enough memory to hold all information.
    # It is possible to make the algorithm work on any scale (process one
    # annotation at a time, saving intermediate result into the db, be careful
    # about the order, etc.), but premature optimization is evil!
    ActionClass = ActionMixin.cls
    graph = gk.Graph()
    # Fetches all actions
    actions = ActionClass.get_actions_offline_spam_detection(session)
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
    # Run vandalism detection!
    graph.compute_answers(ALGO_KARGER_K_MAX)
    # Marks spam annotations.
    # Marks annotations and actions which should not participate in further
    # off-line computations
    # Saves information back to the DB



