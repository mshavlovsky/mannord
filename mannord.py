from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import ConfigParser
from tables import *


# Constants
ACTION_UPVOTE = 'upvote'
ACTION_DOWNVOTE = 'downvote'
ACTION_FLAG_SPAM = 'flag_spam'

THRESHOLD_SCORE_SPAM = 0.1
SCORE_DEFAULT = 0.5

#todo(michael): move creating engine out of this file.
#todo(michael): take care of cases when request info on nonexisting item.

INIFILE = "config.ini"

# Parcing config file
ini_config = ConfigParser.ConfigParser()
ini_config.readfp(open(INIFILE))
db_user = ini_config.get('postgresql', 'user')
passwd = ini_config.get('postgresql', 'passwd')
host = ini_config.get('postgresql', 'host')
port = int(ini_config.get('postgresql', 'port'))
db_name = ini_config.get('postgresql', 'database')

# Creating an engine
engine = create_engine('postgresql://%s:%s@%s:%s/%s' % (db_user, passwd, host,
                                                                 port, db_name))

def bind_engine(engine, session, base):
    session.configure(bind=engine)
    Session = session
    base.metadata.bind = engine
    base.metadata.create_all(engine)


# todo(michael): substitute exeptions with logging.


def add_user(user_id):
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()
    if user is None:
        user = User(user_id)
        session.add(user)
        session.commit()
    session.close()


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
    session = Session()
    # Checks whether the user exists in the db or not, if not then create it.
    author = session.query(User).filter_by(id=user_id).first()
    if author is None:
        author = User(user_id)
        session.add(author)
        session.flush()
    # Check whether the annotation exists or not.
    annot = session.query(Annotation).filter_by(id=annotation_id).first()
    if annot is not None:
        session.commit()
        session.close()
        return
    # Creates and adds annotation to the DB.
    session.add(Annotation(annotation_id, user_id))
    session.commit()
    session.close()


def delete_annotation(annotation_id):
    session = Session()
    # Checks whether the annotation exists or not.
    annot = session.query(Annotation).filter_by(id=annotation_id).first()
    if annot is None:
        # There is nothing to do.
        session.close()
        return
    # First, delete all actions related to the annotation.
    session.query(Action).filter_by(annotation_id=annotation_id).delete()
    # Then delete the annotation itself.
    session.query(Annotation).filter_by(id=annotation_id).delete()
    session.commit()
    session.close()


def flag_as_spam(annotation_id, user_id, timestamp):
    """ Method returns
            1 on succes
            0 when annotation was already flagged as spam by the user
    """
    session = Session()
    # Checks whether the user and the annotation exist in the DB.
    # todo(michael): move checking to a separate function?
    user = session.query(User).filter_by(id=user_id).first()
    if user is None:
        raise Exception("User with id %s does not exist in the DB" % user_id)
    annot = session.query(Annotation).filter_by(id=annotation_id).first()
    if annot is None:
        raise Exception("Annotation with id %s does not exist in the DB" %
                                                                  annotation_id)

    # Okay, the user and the annotation exist.
    # Now check whether the annotation was flagged as a spam by the user or not.
    action = session.query(Action).filter(and_(Action.user_id == user_id,
                                Action.annotation_id == annotation_id,
                                Action.type == ACTION_FLAG_SPAM)).first()
    if action is not None:
        # The user has already flagged the annotation as spam.
        session.close()
        return 0

    # Okay, the user flagged the annotation as spam the first time.
    # Add a record about the action to the DB.
    action = Action(annotation_id, user_id, ACTION_FLAG_SPAM, user.score,
                                                              timestamp)
    session.add(action)
    session.commit()

    # If the annotation is spam already then there is nothing to do.
    # todo(michael): it is not good that is_annotation_spam_ creates extra
    # session.
    if is_annotation_spam(annotation_id):
        session.close()
        return 1
    # Update the annotation recored after it was flagged as spam.
    flag_spam_update_logic(annot, session)
    session.commit()
    session.close()


def flag_spam_update_logic(annot, session):
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


def is_annotation_spam(annotation_id):
    """ Return whether an annotation is spam or not."""
    session = Session()
    annot = session.query(Annotation).filter_by(id=annotation_id).first()
    session.close()
    return annot.is_spam


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
