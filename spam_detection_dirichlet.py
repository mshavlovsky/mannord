from models import (ActionMixin, UserMixin, ItemMixin,
                    ACTION_FLAG_SPAM, ACTION_FLAG_HAM,
                    ACTION_UPVOTE, ACTION_DOWNVOTE)

import graph_d as gd

K_MAX = 10

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
    _add_spam_info_to_graph_k(graph, items, actions)
    # Runs vandalism detection!
    graph.compute_answers(K_MAX)
    # Puts information back to the db.
    _from_graph_to_db(graph, items, actions)
    # Saves information back to the DB
    session.flush()


def _add_spam_info_to_graph_k(graph, items, actions)
    pass


def _from_graph_to_db(graph, items, actions)
    pass


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
    pass


def _raise_spam_ham_flag_fresh(item, user, timestamp, session, spam_flag=True):
    pass


def _undo_spam_ham_flag(item, user, session, spam_flag=False):
    pass


def _delete_spam_action(act, session):
    """ Deletes spam action from the db, it takes care of spam flag counter. """
    if act is None:
        return
    act.item.spam_flag_counter -= 1
    session.delete(act)
