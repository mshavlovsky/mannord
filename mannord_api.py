from mannord import *


def add_annotation(annotation_id, user_id):
    """ Adds annotation info to the db.
    todo(michael): Clarify what is the best time to create an annotation.
                   we can do it when we call functions on it (like when call
                   flag_as_spam(...)), but then we need to provide all arguments
                   necessary for creating annotation record, which can be
                   annoying. Another option is to call  this function when
                   annotation is created which adds extra code outside the
                   package.
                   """
    add_annotation_(annotation_id, user_id)


def add_user(user_id):
    add_user_(user_id)


def delete_annotation(annotation_id):
    """ Deletes annotation from the DB."""
    delete_annotation_(annotation_id)


def flag_as_spam(annotation_id, user_id, timestamp):
    """ Call this function when a user flags an annotation as spam."""
    return flag_as_spam_(annotation_id, user_id, timestamp)


def undo_flag_as_spam(annotation_id, user_id):
    """Call this function when a user removes spam flag from an annotation."""
    undo_flag_as_spam_(annotation_id, user_id)


def is_annotation_spam(annotation_id):
    """ Return whether an annotation is spam or not."""
    is_annotation_spam_(annotation_id)


def is_user_spammer(user_id):
    """ Returns whether a user is spammer or not."""
    is_user_spammer_(user_id)


def get_annotation_score(annotation_id):
    """ Returns annotation score which is between zero and one.
    An annotation is more important if it has higher score.
    """
    get_annotation_score_(annotation_id)
