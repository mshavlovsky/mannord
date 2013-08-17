import numpy as np
from models import (ActionMixin, UserMixin, ItemMixin,
                    ACTION_FLAG_SPAM, ACTION_FLAG_HAM,
                    ACTION_UPVOTE, ACTION_DOWNVOTE)

import graph_d as gd

K_MAX = 10
KARMA_USER_VOTE = 0.5

THRESHOLD_SPAM = -0.2
THRESHOLD_HAM = 0.8
THRESHOLD_DEFINITELY_SPAM = - np.inf
THRESHOLD_DEFINITELY_HAM = np.inf
BASE_SPAM_INCREMENT = 10

def run_offline_computations(session):
    """ The function
                - fetches action infromation from the db
                - given action information it runs Karger's algorithm
                - it marks anctions and annotations based on the output
                - it writes information back to the db
    """
    ActionClass = ActionMixin.cls
    ItemClass = ItemMixin.cls
    # Creates graph
    graph = gd.Graph()
    # Fetches all actions
    actions = ActionClass.sd_get_actions_offline_spam_detect(session)
    items = ItemClass.sd_get_items_offline_spam_detect(session)
    # Adds info to the graph object.
    _add_spam_info_to_graph_d(graph, items, actions)
    # Runs vandalism detection!
    graph.compute_answers(K_MAX)
    # Puts information back to the db.
    _from_graph_to_db(graph, items, actions)
    # Saves information back to the DB
    session.flush()


def _add_spam_info_to_graph_d(graph, items, actions)
    for act in actions:
        if act.type == ACTION_FLAG_SPAM:
            # Spam flag!
            graph.add_answer(act.user_id, act.item_id, -1,
              base_u_n = act.user.sd_base_u_n, base_u_p = act.user.sd_base_u_p)
        elif act.type == ACTION_FLAG_HAM or act.type == ACTION_UPVOTE:
            # Ham flag!
            graph.add_answer(act.user_id, act.item_id, 1,
              base_u_n = act.user.sd_base_u_n, base_u_p = act.user.sd_base_u_p)
        else:
            act.sk_frozen = True
            continue
    for it in items:
        # Creates karma user (old "null" user)
        graph.add_answer(-it.author.id, it.id, KARMA_USER_VOTE,
          base_u_n = it.author.sd_base_u_n, base_u_p = it.author.sd_base_u_p)


def _from_graph_to_db(graph, items, actions)
    # Fills users' fileds.
    for act in actions:
        u = act.user
        user_d = graph.get_user(u.id)
        u.sd_u_n = user_d.u_n
        u.sd_u_p = user_d.u_p
        u.sd_reliab = user_d.reliability
    # Detects and mark frozen items. Fills items' fileds.
    for it in items:
        it.is_spam = False
        it.is_ham = False
        it.sd_frozen = False
        # item_d represents item "it" in the algorithm, it contains spam info.
        item_d = graph.get_item(it.id)
        it.sd_weight = item_d.weight
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
        user_d = graph.get_user(-it.author.id)
        it.author.sd_karma_user_reliab = user_d.reliability
        it.author.sd_karma_user_u_n = user_d.u_n
        it.author.sd_karma_user_u_p = user_d.u_p

    # Some items were marked to be excluded in future offline computations,
    # based on it we need to mark corresponding action and update base
    # spam reliability for users who performed actions.
    for act in actions:
        u = act.user
        it = act.item
        if it.sd_frozen:
            act.sd_frozen = True
            if act.type == ACTION_FLAG_SPAM:
                act_val = -1
            elif act.type == ACTION_FLAG_HAM or act.type == ACTION_UPVOTE:
                act_val = 1
            else:
                continue
            if it.is_spam:
                neg_val, pos_val = gd.neg_first(0, act_val * (-BASE_SPAM_INCREMENT))
                u.sd_base_u_n += neg_val
                u.sd_base_u_p += pos_val
                it.author.sd_karma_user_base_u_n += neg_val
                it.author.sd_karma_user_base_u_p += pos_val
            if it.is_ham:
                neg_val, pos_val = gd.neg_first(0, act_val * BASE_SPAM_INCREMENT)
                u.sd_base_u_n += neg_val
                u.sd_base_u_p += pos_val
                it.author.sd_karma_user_base_u_n += neg_val
                it.author.sd_karma_user_base_u_p += pos_val


def flag_spam(item, user, timestamp, session):
    # Check whether the annotation was flagged as spam.
    act = ActionMixin.cls.get_action(item.id, user.id, ACTION_FLAG_SPAM, session)
    if not act is None:
        # Nothing todo.
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


def _raise_spam_ham_flag_fresh(item, user, timestamp, session, spam_flag=True):
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
    # the user's spam base u_n and u_p.
    if item.sd_frozen:
        val = np.sign(item.sd_weight) * answr * BASE_SPAM_INCREMENT
        neg, pos = gd.neg_first(0, val)
        user.sd_base_u_n += neg
        user.sd_base_u_p += pos
        # Mark action to not use in offline spam detection.
        act.sk_frozen = True
        session.flush()
        return
    # Okay, item participate in offline spam detection.
    # Updating weight of the item
    neg, pos = gd.neg_first(0, answr * user.sd_reliab)
    item.sd_c_n += neg
    item.sd_c_p += pos
    # todo(michael): here
    item.sd_weight = 

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
    session.flush()


def _undo_spam_ham_flag(item, user, session, spam_flag=False):
    pass


def _delete_spam_action(act, session):
    """ Deletes spam action from the db, it takes care of spam flag counter. """
    if act is None:
        return
    act.item.spam_flag_counter -= 1
    session.delete(act)
