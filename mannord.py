from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import ConfigParser
from models import *


# todo(michael): take care of cases when request info on nonexisting item.
# todo(michael): substitute exceptions with logging.


def bind_engine(engine, session, base):
    session.configure(bind=engine)
    Session = session
    base.metadata.bind = engine
    base.metadata.create_all(engine)

# Action - a module level class which inherits from ActionMixin
Action = ActionMixin

# Binding Action
def bind_action_class(actionclass):
    Action = actionclass

def flag_as_spam(annotation, user, timestamp, session):
    """ Action - flag a annotation as a spam.
    The method returns:
            1 on success
            0 when annotation was already flagged as spam by the user
    Arguments:
        - annotation is an object of a class which inherits from AnnotationMixin
        - user is an object of a class which inherits from UserMixin
        - timestamp is an object of datetime.datetime
        - session is a session object
        - ActionClass is a class object which inherits
    """
    # Now check whether the annotation was flagged as a spam by the user or not.
    action = Action.get_action(annotation.id, user.id, ACTION_FLAG_SPAM,session)
    if action is not None:
        # The user has already flagged the annotation as spam. Nothing to do.
        return 0

    # Okay, the user flagged the annotation as spam the first time.
    # Add a record about the action to the DB.
    Action.add_action(annotation.id, user.id, ACTION_FLAG_SPAM, user.score,
                      timestamp, session)
    # Now, if we have enough evidence, mark the annotation as spam
    # and the author as spammer.
    # If the annotation is already spam then there is nothing to do.
    if is_annotation_spam(annotation, session):
        return 1



    # todo(michael): continue from here
    # Update the annotation recored after it was flagged as spam.
    flag_spam_update_logic(annotation, session)
    session.flush()


def flag_spam_update_logic(annotation, session):
    # Counts how many times the annotation was flagged as a spam and then
    # make desicion whether the annotation is spam or not.
    action_list = session.query(Action).filter(
                            and_(Action.annotation_id == annot.id,
                                 Action.type == ACTION_FLAG_SPAM)).all()
    flag_count = len(action_list)
    author = annot.author
    # Simple spam flag logic.
    if flag_count == 1:
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
    elif flag_count > 1:
        # The annotation is spam !!!
        annot.score = 0
        annot.is_spam = True
        author.score = 0
        author.is_spammer = True
    session.commit()


def undo_flag_spam_logic(annot, session):
    """Call this function when a user removes spam flag from an annotation."""
    # todo(michael): undo logic in precence of votes should be more elaborated.
    # Original action was deleted from the db.
    action_list = session.query(Action).filter(
                            and_(Action.annotation_id == annot.id,
                                 Action.type == ACTION_FLAG_SPAM)).all()
    flag_count = len(action_list)
    if flag_count == 0:
        # The annotation does not have any spam flags.
        annot.score = SCORE_DEFAULT
        annot.is_spam = False
        # If the author does not have any other spam annotations then
        # mark him/her as not spammer.
        spam_annot_list = session.query(Annotation).filter(
                                and_(Annotation.author_id == annot.author_id,
                                     Annotation.id != annot.id,
                                     Annotation.is_spam == True)).all()
        if len(spam_annot_list) == 0:
            # Okay the author does not have any spamm annotations.
            author = annot.author
            author.is_spammer = False
            author.score = SCORE_DEFAULT
    session.commit()


def undo_flag_as_spam(annotation_id, user_id):
    session = Session()
    # Retreivning annoataion and user objects.
    annot = session.query(Annotation).filter_by(id=annotation_id).first()
    user = session.query(User).filter_by(id=user_id).first()
    if annot is None:
        raise Exception("There is no annotaion with id %s" % annotation_id)
    if user is None:
        raise Exception("There is no user with id %s" % user_id)
    # Deleting previous action from the DB.
    session.query(Action).filter(and_(Action.user_id == user_id,
                                 Action.annotation_id == annotation_id,
                                 Action.type == ACTION_FLAG_SPAM)).delete()
    session.flush()
    undo_flag_spam_logic(annot, session)
    session.commit()
    session.close()


def is_annotation_spam(annotation, session):
    """ Return whether an annotation is spam or not."""
    return annotation.is_annotation_spam(annotation.id, session)


def is_user_spammer(user_id):
    """ Returns whether a user is spammer or not."""
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()
    session.close()
    return user.is_spammer


def get_annotation_score(annotation_id):
    """ Returns annotation score which is between zero and one.
    An annotation is more important if it has higher score.
    """
    session = Session()
    annot = session.query(Annotation).filter_by(id=annotation_id).first()
    session.close()
    return annot.score
