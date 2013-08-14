import numpy as np
from models import (ActionMixin, UserMixin, ItemMixin,
                    ACTION_FLAG_SPAM, ACTION_FLAG_HAM,
                    ACTION_UPVOTE, ACTION_DOWNVOTE)

import graph_k as gk


# todo(michael): tune parameters
K_MAX = 10
THRESHOLD_SPAM = -0.7
THRESHOLD_HAM = 5
# If weight of an item is less than ..._DEFINITELY_SPAM then annotation is
# excluded from offline computations, similarly for  ..._DEFINITELY_HAM
THRESHOLD_DEFINITELY_SPAM =-2
THRESHOLD_DEFINITELY_HAM = 10
# Increment for base reliability, user's base reliability changes
# by this amound every time he make an action on an spam/ham annotation.
BASE_SPAM_INCREMENT = 1
BASE_SPAM_ = 1
KARMA_USER_VOTE = 0.3


def run_offline_computations(session):
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
    # Creates graph
    graph = gk.Graph()
    # Fetches all actions
    actions = ActionClass.sk_get_actions_offline_spam_detect(session)
    items = ItemClass.sk_get_items_offline_spam_detect(session)
    #--
    #print 'num items', len(items)
    #for it in items:
    #    print it
    #print 'num actions', len(actions)
    #for act in actions:
    #    print act
    #--
    # Adds info to the graph object.
    _add_spam_info_to_graph_k(graph, items, actions)
    print graph
    # Runs vandalism detection!
    graph.compute_answers(K_MAX)
    # Marks spam annotations.
    _mark_spam_items(graph, items, actions)
    # Saves information back to the DB
    session.flush()

def _add_spam_info_to_graph_k(graph, items, actions):
    """ Adds spam information a graph for detection using Karger's algorithm.
    """
    # Adds flag information (graph.add_answer(...)) to the graph object.
    for act in actions:
        if act.type == ACTION_FLAG_SPAM:
            # Spam flag!
            graph.add_answer(act.user_id, act.item_id, -1,
                base_reliability = act.user.sk_base_reliab)
        elif act.type == ACTION_FLAG_HAM or act.type == ACTION_UPVOTE:
            # Ham flag!
            graph.add_answer(act.user_id, act.item_id, 1,
                base_reliability = act.user.sk_base_reliab)
        else:
            # The action does not related to vandalizm detection, so ignore it.
            # todo(michael): make sure that after flush() the action is unmarked
            act.sk_frozen = True
            continue
    for it in items:
        # Creates karma user (old "null" user)
        graph.add_answer(-it.author.id, it.id, KARMA_USER_VOTE,
                   base_reliability = it.author.sk_karma_user_base_reliab)

def _mark_spam_items(graph, items, actions):
    """ Marks items as spam/ham and excludes them from future offline
    computations if necessary.
    """
    for it in items:
        it.is_spam = False
        it.is_ham = False
        it.sk_frozen = False
        # item_k represents item "it" in the algorithm, it contains spam info.
        item_k = graph.get_item(it.id)
        print item_k, item_k.weight
        it.sk_weight = item_k.weight
        # Marks spam and ham
        if it.sk_weight < THRESHOLD_SPAM:
            it.is_spam = True
        if it.sk_weight > THRESHOLD_HAM:
            it.is_ham = True
        # Marks off items actions from offline computation
        if (it.sk_weight > THRESHOLD_DEFINITELY_HAM or
            it.sk_weight < THRESHOLD_DEFINITELY_SPAM):
            it.sk_frozen = True
        # Saves reliability of a spam karma user related to an author of the item
        k_user = graph.get_user(-it.author.id)
        it.author.sk_karma_user_reliab = k_user.reliability

    # Some items were marked to be excluded in future offline computations,
    # based on it we need to mark corresponding action and update base
    # spam reliability for users who performed actions.
    for act in actions:
        it = act.item
        if it.sk_frozen == True:
            if act.type == ACTION_FLAG_SPAM:
                act_val = -1
            elif act.type == ACTION_FLAG_HAM or act.type == ACTION_UPVOTE:
                act_val = 1
            else:
                continue
            if it.is_spam:
                act.user.sk_base_reliab += \
                    act_val * (-BASE_SPAM_INCREMENT)
                act.user.sk_karma_user_base_reliab += \
                    act_val * (-BASE_SPAM_INCREMENT)
            if it.is_ham:
                act.user.sk_base_reliab += \
                    act_val * BASE_SPAM_INCREMENT
                act.user.sk_karma_user_base_reliab += \
                    act_val * BASE_SPAM_INCREMENT


def flag_spam(item, user, timestamp, session):
    # Check whether the annotation was flagged as spam.
    act = ActionMixin.cls.get_action(item.id, user.id, ACTION_FLAG_SPAM, session)
    if not act is None:
        # Nothing todo.
        # todo(michael): We can return special code when user tries to flag
        # spam when he/she already has done it.
        return
    # Check whether the item was flagged as ham.
    act = ActionMixin.cls.get_action(item.id, user.id, ACTION_FLAG_HAM, session)
    if act is None:
        # Flag as spam the first time!
        _raise_spam_ham_flag_fresh(item, user, timestamp, session, spam_flag=True)
    else:
        # The item was flagged as ham.
        # Undoes effects of ham flag.
        # todo(michael): add spam flag counter
        _undo_spam_ham_flag(item, user, session, spam_flag=False)
        # Deletes the ham aciton.
        session.delete(act)
        # Flags the item as spam.
        _raise_spam_ham_flag_fresh(item, user, timestamp, session, spam_flag=True)


def flag_ham(item, user, timestamp, session):
    # Check whether the item was flagged as ham.
    act = ActionMixin.cls.get_action(item.id, user.id, ACTION_FLAG_HAM, session)
    if not act is None:
        # Nothing todo.
        return
    # Check whether the item was flagged as spam.
    act = ActionMixin.cls.get_action(item.id, user.id, ACTION_FLAG_SPAM, session)
    if act is None:
        # Flag as ham the first time!
        _raise_spam_ham_flag_fresh(item, user, timestamp, session, spam_flag=False)
    else:
        # The item was flagged as spam, so undo it.
        _undo_spam_ham_flag(item, user, session, spam_flag=True)
        # Deletes the spam aciton.
        _delete_spam_action(act, session)
        # Flags the item as spam.
        _raise_spam_ham_flag_fresh(item, user, timestamp,
                                          session, spam_flag=False)


def _undo_spam_ham_flag(item, user, session, spam_flag=True):
    """ The function udoes flagging spam/ham without checking for original
    action in the DB (it is assumed that it should be done outside the function)
    Arguments:
        - spam_flag is a flag we want to reverse, i.e. we want to reverse
        spam flag then spam_flag=True, spam_flag=False for reverting ham flag.
    """
    answr = -1 if spam_flag else 1
    if not item.sk_frozen:
        # The item is as known as spam/ham.
        val = np.sign(item.sk_weight) * answr * BASE_SPAM_INCREMENT
        user.sk_base_reliab -= val
        return
    # Okay, item participate in offline spam detection.
    # Updating weight of the item
    val = item.sk_weight
    item.sk_weight -= answr * user.sk_reliab
    # Updating user's raw/regular spam reliability.
    user.sk_reliab_raw -= answr * gk.asympt_func(val)
    user.sk_reliab = gk.asympt_func(user.sk_reliab_raw)
    session.flush()


def _raise_spam_ham_flag_fresh(item, user, timestamp,
                                      session, spam_flag=True):
    """ The function flags spam/ham on the item.
    It is assumed that the item was not flagged as spam/ham by the user.
    Argumets:
        - spam_flag is True if we want to raise spam flag, otherwise use False.
    """
    # Creates a record in Action table
    if spam_flag:
        answr = -1
        act = ActionMixin.cls(item.id, user.id, ACTION_FLAG_SPAM, timestamp)
        item.spam_flag_counter += 1
    else:
        answr = 1
        act = ActionMixin.cls(item.id, user.id, ACTION_FLAG_HAM, timestamp)
    session.add(act)
    # If the item is known as spam/ham then we change
    # the user's spam base reliability.
    if item.sk_frozen:
        val = np.sign(item.sk_weight) * answr * BASE_SPAM_INCREMENT
        user.sk_base_reliab += val
        # Mark action to not use in offline spam detection.
        act.sk_frozen = True
        session.flush()
        return
    # Okay, item participate in offline spam detection.
    # Updating weight of the item
    val = item.sk_weight
    item.sk_weight += answr * user.sk_reliab
    # Updating user's raw/regular spam reliability.
    user.sk_reliab_raw += answr * gk.asympt_func(val)
    user.sk_reliab = gk.asympt_func(user.sk_reliab_raw)
    session.flush()

def _delete_spam_action(act, session):
    """ Deletes spam action from the db, it takes care of spam flag counter. """
    if act is None:
        return
    act.item.spam_flag_counter -= 1
    session.delete(act)

