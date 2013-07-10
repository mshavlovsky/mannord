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


def flag_as_spam(item, user, timestamp, session, ActionClass):
    """Flag an item as a spam.
    The method returns:
            1 on success
            0 when the item was already flagged as spam by the user
    Arguments:
        - item is an object of a class which inherited from ItemMixin
        - user is an object of a class which inherited from UserMixin
        - timestamp is an object of datetime.datetime
        - session is a session object
        - ActionClass is a class which ingereted from ActionMixin
    """
    # Check whether the item was flagged as a spam by the user or not.
    action = ActionClass.get_action(item.id, user.id, ACTION_FLAG_SPAM,
                                    session)
    if action is not None:
        # The user has already flagged the item as spam. Nothing to do.
        return 0

    # Okay, the user flagged the item as spam the first time.
    # Add a record about the action to the DB.
    ActionClass.add_action(item.id, user.id, ACTION_FLAG_SPAM, user.score,
                      timestamp, session)
    # Increases spam counter.
    item.spam_flag_counter = item.spam_flag_counter + 1
    session.flush()
    # If the item is already spam then there is nothing to do.
    if item.is_spam:
        return 1
    # Main spam updete logic.
    flag_spam_update_logic(item, session)
    session.flush()


def flag_spam_update_logic(item, session):
    # If we have enough evidence, mark the item as spam
    # and the author as spammer.
    author = item.author
    # If an item has two or more spam flags then we mark it as spam.
    # If an item has only one spam flag and an author has low score, then
    # we mark the item as spam.
    if item.spam_flag_counter == 1:
        # The item is probably spam, so make it's weigh smaller
        # then default.
        item.score = THRESHOLD_SCORE_SPAM
        # If the author of the item has low score then the item is
        # spam.
        if item.author.score <= THRESHOLD_SCORE_SPAM:
            # The item is spam !!!
            item.score = 0
            item.is_spam = True
            author.score = 0
            author.is_spammer = True
    elif item.spam_flag_counter > 1:
        # The item is spam !!!
        item.score = 0
        item.is_spam = True
        author.score = 0
        author.is_spammer = True
    session.flush()


def undo_flag_as_spam(item, user, session, ActionClass):
    """ Returns 0 if the user has not flagged the item as spam.
        Returns 1 in case of success.
    """
    # todo(michael): note that undo logic in presence of votes is more complex
    action = ActionClass.get_action(item.id, user.id, ACTION_FLAG_SPAM,
                                    session)
    if action is None:
        # There is nothing to do
        return 0
    # Deletes the action from the DB.
    session.delete(action)
    # Decrease spam counter on the item
    item.spam_flag_counter = item.spam_flag_counter - 1
    session.flush()
    if not item.is_spam:
        # The item was not spam, so nothing to do.
        return 1
    # Checks whether we need unmark the item as spam
    # and the author as spammer.
    if item.spam_flag_counter == 0:
        # The item does not have any spam flags.
        item.score = SCORE_DEFAULT
        item.is_spam = False

    # If the author does not have any other spam items then
    # mark him/her as not spammer.
    spam_item_list = session.query(item.__class__).filter(
                        and_(item.__class__.author_id == item.author_id,
                             item.__class__.is_spam == True)).all()
    author = item.author
    if len(spam_item_list) == 0:
        # Okay the author does not have any spamm items.
        author.is_spammer = False
        author.score = SCORE_DEFAULT
    elif len(spam_item_list) == 1:
        # Well, the author probably a spammer, make his score on threshold level
        author.is_spammer = False
        author.score = THRESHOLD_SCORE_SPAM
    session.flush()
