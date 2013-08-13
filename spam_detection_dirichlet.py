from models import (ActionMixin, UserMixin, ItemMixin,
                    ACTION_FLAG_SPAM, ACTION_FLAG_HAM,
                    ACTION_UPVOTE, ACTION_DOWNVOTE)

import graph_d as gd


def run_offline_computations(session):
    """ The function
                - fetches action infromation from the db
                - given action information it runs Karger's algorithm
                - it marks anctions and annotations based on the output
                - it writes information back to the db
    """
    pass


def flag_spam(item, user, timestamp, session):
    pass


def flag_ham(item, user, timestamp, session):
    pass
