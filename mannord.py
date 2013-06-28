from sqlalchemy import create_engine, and_
from datetime import datetime
from models import *


# todo(michael): ahh, I don't like to pass ActionClass to each function!

def bind_engine(engine, session, base, should_create=True):
    # todo(michael): do I need to bind session? I don't use anywhere.
    session.configure(bind=engine)
    base.metadata.bind = engine
    if should_create:
        base.metadata.create_all(engine)


def flag_as_spam(annot, user, timestamp, session, ActionClass):
    """Flag an annotation as a spam.
    The method returns:
            1 on success
            0 when annotation was already flagged as spam by the user
    Arguments:
        - annot is an object of a class which inherited from AnnotationMixin
        - user is an object of a class which inherited from UserMixin
        - timestamp is an object of datetime.datetime
        - session is a session object
        - ActionClass is a class which ingereted from ActionMixin
    """
    # Check whether the annotation was flagged as a spam by the user or not.
    action = ActionClass.get_action(annot.id, user.id, ACTION_FLAG_SPAM,
                                    session)
    if action is not None:
        # The user has already flagged the annotation as spam. Nothing to do.
        return 0

    # Okay, the user flagged the annotation as spam the first time.
    # Add a record about the action to the DB.
    ActionClass.add_action(annot.id, user.id, ACTION_FLAG_SPAM, user.score,
                      timestamp, session)
    # Increases spam counter.
    annot.spam_flag_counter = annot.spam_flag_counter + 1
    session.flush()
    # If the annotation is already spam then there is nothing to do.
    if annot.is_spam:
        return 1
    # Main spam updete logic.
    flag_spam_update_logic(annot, session)
    session.flush()


def flag_spam_update_logic(annot, session):
    # If we have enough evidence, mark the annotation as spam
    # and the author as spammer.
    author = annot.author
    # If an annotation has two or more spam flags then we mark it as spam.
    # If an annotation has only one spam flag and an author has low score, then
    # we mark the annotation as spam.
    if annot.spam_flag_counter == 1:
        # The annotation is probably spam, so make it's weigh smaller
        # then default.
        annot.score = THRESHOLD_SCORE_SPAM
        # If the author of the annotation has low score then the annotation is
        # spam.
        if annot.author.score <= THRESHOLD_SCORE_SPAM:
            # The annotation is spam !!!
            annot.score = 0
            annot.is_spam = True
            author.score = 0
            author.is_spammer = True
    elif annot.spam_flag_counter > 1:
        # The annotation is spam !!!
        annot.score = 0
        annot.is_spam = True
        author.score = 0
        author.is_spammer = True
    session.flush()


def undo_flag_as_spam(annot, user, session, ActionClass):
    """ Returns 0 if the user has not flagged the annotation as spam.
        Returns 1 in case of success.
    """
    # todo(michael): note that undo logic in presence of votes is more complex
    action = ActionClass.get_action(annot.id, user.id, ACTION_FLAG_SPAM,
                                    session)
    if action is None:
        # There is nothing to do
        return 0
    # Deletes the action from the DB.
    session.delete(action)
    # Decrease spam counter on the annotation
    annot.spam_flag_counter = annot.spam_flag_counter - 1
    session.flush()
    if not annot.is_spam:
        # The annotation was not spam, so nothing to do.
        return 1
    # Checks whether we need unmark the annotation as spam
    # and the author as spammer.
    if annot.spam_flag_counter == 0:
        # The annotation does not have any spam flags.
        annot.score = SCORE_DEFAULT
        annot.is_spam = False

    # If the author does not have any other spam annotations then
    # mark him/her as not spammer.
    spam_annot_list = session.query(annot.__class__).filter(
                        and_(annot.__class__.author_id == annot.author_id,
                             annot.__class__.is_spam == True)).all()
    author = annot.author
    if len(spam_annot_list) == 0:
        # Okay the author does not have any spamm annotations.
        author.is_spammer = False
        author.score = SCORE_DEFAULT
    elif len(spam_annot_list) == 1:
        # Well, the author probably a spammer, make his score on threshold level
        author.is_spammer = False
        author.score = THRESHOLD_SCORE_SPAM
    session.flush()
