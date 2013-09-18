from sqlalchemy import create_engine, and_
from datetime import datetime
import numpy as np
from models import (ActionMixin, UserMixin, ItemMixin, ComputationMixin,
                    COMPUTATION_SK_NAME,
                    ACTION_UPVOTE, ACTION_DOWNVOTE,
                    ACTION_FLAG_SPAM, ACTION_FLAG_HAM)


import spam_utils as su
import spam_detection_karger as sdk
import spam_detection_dirichlet as sdd
import hitsDB

SPAM_ALGO = su.ALGO_DIRICHLET

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
    if algo_name != su.ALGO_KARGER and algo_name != su.ALGO_DIRICHLET:
        raise Exception("Unknown algorithm !")


def run_offline_spam_detection(algo_name, session):
    """ Method runs offline spam detection. """
    name_check(algo_name)
    # Obtains class names to perform db querries later.
    if algo_name == su.ALGO_KARGER:
        sdk.run_offline_computations(session)
    else:
        sdd.run_offline_computations(session)
        pass
    session.flush()


def raise_spam_flag(item, user, session, algo_name=su.ALGO_KARGER):
    timestamp = datetime.utcnow()
    if algo_name == su.ALGO_KARGER:
        sdk.flag_spam(item, user, timestamp, session)
    else:
        sdd.flag_spam(item, user, timestamp, session)


def raise_ham_flag(item, user, session, algo_name=su.ALGO_KARGER):
    timestamp = datetime.utcnow()
    if algo_name == su.ALGO_KARGER:
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


def get_n_items_for_spam_mm_randomly(n, session):
   return ItemMixin.cls.get_n_items_for_spam_mm_randomly(n, session)


def delete_spam_item_by_author(item, session, algo_name=su.ALGO_KARGER):
    """ If item is deleted by author then there is no reputation damage to the
    author, plus users who flagged it receive boost to base reliability.
    """
    if item.action_twin is not None:
        # If the item is also an action, delete the action first.
        if item.action_twin.type == ACTION_UPVOTE:
            item.parent.author.mm_vote_counter -= 1
            item.parent.author.vote_counter -= 1
        elif item.action_twin.type == ACTION_DOWNVOTE:
            item.parent.author.mm_vote_counter += 1
            item.parent.author.vote_counter += 1
        else:
            raise Exception("Unknown action: %s" % item.action_twin)
        session.delete(item.action_twin)
        session.flush()
    # Okay, deletes the item.
    if algo_name == su.ALGO_KARGER:
        sdk.delete_spam_item_by_author(item, session)
    elif algo_name == su.ALGO_DIRICHLET:
        sdd.delete_spam_item_by_author(item, session)
    else:
        raise Exception("Unknown algorithm!")


def add_item(page_url, item_id, user, session, parent_id=None, action_type=None,
             spam_detect_algo=su.ALGO_KARGER):
    """ Creates an item and adds it to the db."""
    annot = ItemMixin.cls(page_url, item_id, user, parent_id=parent_id,
                          spam_detect_algo=spam_detect_algo)
    session.add(annot)
    session.flush()
    # If the annotation is action, then create and bind the action.
    if action_type is not None:
        if parent_id is None:
            raise Exception("New annotation which is action should have a parent!")
        act = ActionMixin.cls(parent_id, user.id, action_type,
                              datetime.utcnow(), item_twin_id=annot.id)
        item = ItemMixin.cls.get_item(parent_id, session)
        if action_type == ACTION_UPVOTE:
            item.author.mm_vote_counter += 1
            item.author.vote_counter += 1
        elif action_type == ACTION_DOWNVOTE:
            item.author.mm_vote_counter -= 1
            item.author.vote_counter -= 1
        else:
            raise Exception("Action should be whether upvote or donwvote!")
        session.add(act)
        session.flush()
    return annot


def get_add_item(page_url, item_id, user, session, parent_id=None,
             action_type=None, spam_detect_algo=su.ALGO_KARGER):
    annot = ItemMixin.cls.get_item(item_id, session)
    # If annotation does not exist then create it.
    if annot is None:
        annot = add_item(page_url, item_id, user, session, parent_id=parent_id,
                     action_type=action_type, spam_detect_algo=spam_detect_algo)
    return annot

def delete_item(item, session):
    # If the item is action, then delete this action and then delete the item.
    if item.children is not None and len(item.children) != 0:
        # We cannot delete the item, it has subitems
        print 'childred', item.children
        print 'inside'
        return
    if item.action_twin is not None:
        if item.action_twin.type == ACTION_UPVOTE:
            item.parent.author.mm_vote_counter -= 1
            item.parent.author.vote_counter -= 1
        elif item.action_twin.type == ACTION_DOWNVOTE:
            item.parent.author.mm_vote_counter += 1
            item.parent.author.vote_counter += 1
        else:
            raise Exception("Unknown action: %s" % item.action_twin)
        session.delete(item.action_twin)
    session.delete(item)
    session.flush()

def upvote(item, user, session):
    # Checks whether the user has upvoted the item
    upvote = ActionMixin.cls.get_action(item.id, user.id, ACTION_UPVOTE, session)
    if upvote is not None:
        # The item has been upvoted by the user.
        return
    # Undo downvote if it exists.
    undo_downvote(item, user, session)
    # Okay, upvoting fresh
    act = ActionMixin.cls(item.id, user.id, ACTION_UPVOTE, datetime.utcnow())
    # Increase item author's vote counter.
    item.author.vote_counter += 1
    raise_ham_flag(item, user, session)
    session.add(act)
    session.flush()


def downvote(item, user, session):
    downvote = ActionMixin.cls.get_action(item.id, user.id, ACTION_DOWNVOTE, session)
    if downvote is not None:
        return
    # Undo upvote is it exists.
    undo_upvote(item, user, session)
    # Downvoting
    act = ActionMixin.cls(item.id, user.id, ACTION_DOWNVOTE, datetime.utcnow())
    # Decrease item author's vote counter
    item.author.vote_counter -= 1
    session.add(act)
    session.flush()


def undo_upvote(item, user, session):
    upvote = ActionMixin.cls.get_action(item.id, user.id, ACTION_UPVOTE, session)
    if upvote is None:
        # Nothing to do
        return
    item.author.vote_counter -= 1
    if SPAM_ALGO == su.ALGO_KARGER:
        sdk._undo_spam_ham_flag(item, user, session, spam_flag==False)
    elif SPAM_ALGO == su.ALGO_DIRICHLET:
        sdd._undo_spam_ham_flag(item, user, session, spam_flag==False)
    else:
        raise Exception("unknown algorithm")
    session.delete(upvote)
    session.flush()


def undo_downvote(item, user, session):
    downvote = ActionMixin.cls.get_action(item.id, user.id, ACTION_DOWNVOTE, session)
    if downvote is None:
        # Nothing to do
        return
    item.author.vote_counter += 1
    session.delete(downvote)
    session.flush()
