import numpy as np
from models import (ActionMixin, UserMixin, ItemMixin,
                    ComputationMixin, COMPUTATION_SK_NAME,
                    ACTION_FLAG_SPAM, ACTION_FLAG_HAM,
                    ACTION_UPVOTE, ACTION_DOWNVOTE)

import spam_utils as su
import graph_k as gk


K_MAX = 11
# If weight of an item is less than ..._DEFINITELY_SPAM then annotation is
# excluded from offline computations, similarly for  ..._DEFINITELY_HAM
THRESHOLD_DEFINITELY_SPAM = - np.inf
THRESHOLD_DEFINITELY_HAM = np.inf
# Increment for base reliability, user's base reliability changes
# by this amound every time he make an action on an spam/ham annotation.
BASE_SPAM_INCREMENT = 1


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
    # Adds info to the graph object.
    _add_spam_info_to_graph_k(graph, items, actions)
    # Runs vandalism detection!
    graph.compute_answers(K_MAX)
    # Puts information back to the db.
    comp = ComputationMixin.cls.get(COMPUTATION_SK_NAME, session)
    _from_graph_to_db(graph, items, actions, comp)
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
            act.sk_frozen = True
            continue
    for it in items:
        # Creates karma user.
        graph.add_answer('-' + it.author.id, it.id, gk.KARMA_USER_VOTE,
                   base_reliability = it.author.sk_karma_user_base_reliab)

def _from_graph_to_db(graph, items, actions, computation):
    # Remembers normalization coefficient.
    computation.normalization = graph.normaliz
    # Fills users' fileds.
    for act in actions:
        u = act.user
        user_k = graph.get_user(u.id)
        u.sk_reliab_raw = user_k.reliability_raw
        u.sk_reliab = user_k.reliability
    # Detects and mark frozen items. Fills items' fileds.
    for it in items:
        it.sk_frozen = False
        # item_k represents item "it" in the algorithm, it contains spam info.
        item_k = graph.get_item(it.id)
        it.sk_weight = item_k.weight
        # Marks spam, ham, or marks for metamoderation.
        su.mark_spam_ham_or_mm(it, algo_type=su.ALGO_KARGER)
        # Marks off items actions from offline computation
        if (it.sk_weight > THRESHOLD_DEFINITELY_HAM or
            it.sk_weight < THRESHOLD_DEFINITELY_SPAM):
            it.sk_frozen = True
        # Saves reliability of a spam karma user related to an author of the item
        k_user = graph.get_user('-' + it.author.id)
        it.author.sk_karma_user_reliab = k_user.reliability

    # Some items were marked to be excluded in future offline computations,
    # based on it we need to mark corresponding action and update base
    # spam reliability for users who performed actions.
    for act in actions:
        u = act.user
        it = act.item
        if it.sk_frozen:
            act.sk_frozen = True
            if act.type == ACTION_FLAG_SPAM:
                act_val = -1
            elif act.type == ACTION_FLAG_HAM or act.type == ACTION_UPVOTE:
                act_val = 1
            else:
                continue
            if it.is_spam:
                u.sk_base_reliab += act_val * (-BASE_SPAM_INCREMENT)
                it.author.sk_karma_user_base_reliab += act_val * (-BASE_SPAM_INCREMENT)
            if it.is_ham:
                u.sk_base_reliab += act_val * BASE_SPAM_INCREMENT
                it.author.sk_karma_user_base_reliab += act_val * BASE_SPAM_INCREMENT


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
        - spam_flag is a flag we want to reverse, i.e. if we want to reverse
        spam flag then spam_flag=True; spam_flag=False for reverting ham flag.
    """
    answr = -1 if spam_flag else 1
    if item.sk_frozen:
        # The item is known as spam/ham.
        val = np.sign(item.sk_weight) * answr * BASE_SPAM_INCREMENT
        user.sk_base_reliab -= val
        return
    # Okay, item participate in offline spam detection.
    # Updating weight of the item
    val = item.sk_weight
    item.sk_weight -= answr * user.sk_reliab
    # Updating user's raw/regular spam reliability.
    user.sk_reliab_raw -= answr * val
    if gk.USE_ASYMPTOTIC_FUNC:
        user.sk_reliab = gk.asympt_func(user.sk_reliab_raw)
    else:
        user.sk_reliab = user.sk_reliab_raw
    # Normalization!
    comp = ComputationMixin.cls.get(COMPUTATION_SK_NAME, session)
    user.sk_reliab /= comp.normalization
    # Marks the item as spam or ham, or marks for metamoderation.
    su.mark_spam_ham_or_mm(item, algo_type=su.ALGO_KARGER)
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
    user.sk_reliab_raw += answr * val
    if gk.USE_ASYMPTOTIC_FUNC:
        user.sk_reliab = gk.asympt_func(user.sk_reliab_raw)
    else:
        user.sk_reliab = user.sk_reliab_raw
    # Normalization!
    comp = ComputationMixin.cls.get(COMPUTATION_SK_NAME, session)
    user.sk_reliab /= comp.normalization
    # Marks the item as spam or ham, or marks for metamoderation.
    su.mark_spam_ham_or_mm(item, algo_type=su.ALGO_KARGER)
    session.flush()


def _delete_spam_action(act, session):
    """ Deletes spam action from the db, it takes care of spam flag counter. """
    if act is None:
        return
    act.item.spam_flag_counter -= 1
    session.delete(act)


def fetch_n_items_for_mm(n, session):
    session.query(ItemMixin.cls).filter_by().order_by(func.rand()).limit(n)


def delete_spam_item_by_author(item, session):
    """ If item is deleted by author then there is no reputation damage to the
    author, plus users who flagged it receive boost to base reliability.
    """
    actions = ActionMixin.cls.get_actions_on_item(item.id, session)
    if item.sk_frozen:
        # If the item is frozen then users who flagged it already got changes
        # to their spam reliability.
        # In this case the user's karma user also has changes to its reliability
        # But it is unlikely case. We want to not damage user's reputation
        # only if delete the item fast enough.
        session.delete(item)
        for act in actions:
            if act.type == ACTION_FLAG_SPAM or act.type == ACTION_FLAG_HAM:
                session.delete(act)
        session.flush()
        return
    for act in actions:
        if act.type == ACTION_FLAG_SPAM:
            # Increases spam reliability
            act.user.sk_base_reliab += BASE_SPAM_INCREMENT
            session.delete(act)
        elif act.type == ACTION_FLAG_HAM:
            # Reduces spam reliability of the author
            act.user.sk_base_reliab -= BASE_SPAM_INCREMENT
            session.delete(act)
        else:
            pass
    session.delete(item)
    session.flush()
