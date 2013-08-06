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
ALGO_KARGER_BASE_SPAM_INCREMENT = 1
ALGO_KARGER_BASE_SPAM_ = 1


def bind_engine(engine, session, base, should_create=True):
    # todo(michael): do I need to bind session? I don't use anywhere.
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
    # 
    UserMixin.cls = UserClass
    ItemClass.cls = ItemClass


def run_offline_spam_detection(algo_name):
    """ Method runs complete spam detection algorithm.
    """
    if ActionMixin.cls is None:
        raise Exception("You forgot to bootstrap the mannord!")
    if algo_type == ALGO_NAME_KARGER:
        run_offline_spam_detect_karger()
    else:
        raise Exception("Unknown algorithm type")


def flag_spam(item, session, algo_name=ALGO_NAME_KARGER):
    if ActionMixin.cls is None:
        raise Exception("You forgot to bootstrap the mannord!")
    if algo_type == ALGO_NAME_KARGER:
        run_offline_spam_detect_karger()
    else:
        raise Exception("Unknown algorithm type")
    

def flag_spam_karger(item, session):
    


def offline_spam_detection_karger(session):
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
    ItemClass = ItemMixin.cls
    graph = gk.Graph()
    # Fetches all actions
    actions = ActionClass.get_actions_offline_spam_detect(session)
    items = ItemClass.get_items_offline_spam_detect(session)
    # Adds info to the graph object.
    _add_spam_info_to_graph_k(graph, items, actions)
    # Runs vandalism detection!
    graph.compute_answers(ALGO_KARGER_K_MAX)
    # Marks spam annotations.
    _mark_spam_items(graph, items, actions)
    # Saves information back to the DB
    session.flush()

def _add_spam_info_to_graph_k(graph, actions, item):
    """ Adds spam information a graph for detection using Karger's algorithm.
    """
    # Adds flag information (graph.add_answer(...)) to the graph object.
    for act in actions:
        if act.type == ACTION_FLAG_SPAM:
            # Spam flag!
            graph.add_answer(act.user_id, act.item_id, -1,
                base_reliab = act.user.base_reliab_spam_detect)
        elif act.type == ACTION_FLAG_HAM or act.type == ACTION_UPVOTE:
            # Ham flag!
            graph.add_answer(act.user_id, act.item_id, 1,
                base_reliab = act.user.base_reliab_spam_detect)
        else:
            # The action does not related to vandalizm detection, so ignore it.
            # todo(michael): make sure that after flush() the action is unmarked
            act.participate_in_offline_spam_detect = False
            continue
    for it in items:
        # Creates karma user (old "null" user)
        graph.add_answer(-it.author.id, it.id, KARMA_USER_VOTE,
                   base_reliab = it.author.base_reliab_spam_karma_user)

def _mark_spam_items(graph, items, actions):
    """ Marks items as spam/ham and excludes them from future offline
    computations if necessary.
    """
    for it in items:
        it.is_spam = False
        it.is_ham = False
        it.participate_offline_spam_detect = True
        # item_k represents item "it" in the algorithm, it contains spam info.
        item_k = graph.get_item(it.id)
        spam_weight = item_k.weight
        # Marks spam and ham
        if spam_weight < ALGO_KARGER_THRESHOLD_SPAM:
            it.is_spam = True
        if spam_weight > ALGO_KARGER_THRESHOLD_HAM:
            it.is_spam = True
        # Marks off items actions from offline computation
        if (spam_weight > ALGO_KARGER_THRESHOLD_DEFINITELY_HAM or
            spam_weight < ALGO_KARGER_THRESHOLD_DEFINITELY_SPAM):
            it.participate_offline_spam_detect = False
        # Saves reliability of a spam karma user related to an author of the item
        k_user = graph.get_user(-it.author.id)
        it.author.reliab_spam_karma_user = k_user.reliability

    # Some items were marked to be excluded in future offline computations,
    # based on it we need to mark corresponding action and update base
    # spam reliability for users who performed actions.
    for act in actions:
        it = act.item
        if it.participate_offline_spam_detect == False:
            if act.type == ACTION_FLAG_SPAM:
                act_val = -1
            elif act.type == ACTION_FLAG_HAM or act.type == ACTION_UPVOTE:
                act_val = 1
            else:
                continue
            if it.is_spam:
                act.user.base_reliab_spam_detect += \
                    act_val * (-ALGO_KARGER_BASE_SPAM_INCREMENT)
                act.user.base_reliab_spam_karma_user += \
                    act_val * (-ALGO_KARGER_BASE_SPAM_INCREMENT)
            if it.is_ham:
                act.user.base_reliab_spam_detect += \
                    act_val * ALGO_KARGER_BASE_SPAM_INCREMENT
                act.user.base_reliab_spam_karma_user += \
                    act_val * ALGO_KARGER_BASE_SPAM_INCREMENT
