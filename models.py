from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        ForeignKey, DateTime, Sequence, and_)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr


# todo(michael): there is an issue when using foreign keys.
# We don't know tables' and classes' names of tables.
# For now I use global constants to keep these names, if that okay then
# it makes sence to move constants into a config file.

# Constants
USER_TABLE_ID_FIELD = 'user.id'
USER_CLASS_NAME = 'User'
ITEM_TABLE_ID_FIELD = 'annotation.id'
ITEM_CLASS_NAME = 'ModeratedAnnotation'
ITEM_TABLE_NAME = 'annotation'
ACTION_TABLE_NAME = 'action'

ACTION_UPVOTE = 'upvote'
ACTION_DOWNVOTE = 'downvote'
ACTION_FLAG_SPAM = 'flag_spam'
ACTION_FLAG_HAM = 'flag_ham'

THRESHOLD_SCORE_SPAM = 0.1
SCORE_DEFAULT = 0.5


class UserMixin(object):

    @declared_attr
    def id(cls):
        return Column(Integer, autoincrement=True, primary_key=True)

    @declared_attr
    def is_spammer(cls):
        return Column(Boolean, default=False)

    # score is "internal" reputation and it is a real value between 0 and 1,
    # We trust 100% to a user with a score 1 and we don't trust to a user with
    # score 0.
    @declared_attr
    def score(cls):
        return Column(Float, default=0.5)

    # Parameters of a score distribution.
    @declared_attr
    def score_distr_param_a(cls):
        return Column(Float, default=0)

    @declared_attr
    def score_distr_param_b(cls):
        return Column(Float, default=0)

    # Reputation of a user. This value is exposed to users.
    @declared_attr
    def reputation(cls):
        return Column(Float, default=0)

    @declared_attr
    def base_reliability_for_karma_user(cls):
        """ This field is a base reliability for a karma user ("null" user) who
        always votes positively for the user's annotation."""
        return Column(Float, default=0)

    @declared_attr
    def base_reliability_for_spam_detection(cls):
        """ This field is a base raliability of a user for spam detecting task.
        """
        return Column(Float, default=0)

class ItemMixin(object):
    """ Item is an object like annotation, post, etc. Moderation actions
    are perfored on items.
    """

    __tablename__ = ITEM_TABLE_NAME

    @declared_attr
    def id(cls):
        return Column(String, primary_key=True)

    @declared_attr
    def is_spam(cls):
        return Column(Boolean, default=False)

    @declared_attr
    def spam_flag_counter(cls):
        return Column(Integer, default=0)

    # Score of an item is between 0 and 1. It is the items's weight.
    # The item is more important if it has higher score.
    @declared_attr
    def score(cls):
        return Column(Float, default=0.5)

    # Parameters of a score distribution.
    @declared_attr
    def score_distr_param_a(cls):
        return Column(Float, default=0)

    @declared_attr
    def score_distr_param_b(cls):
        return Column(Float, default=0)

    # Authors's id
    @declared_attr
    def author_id(cls):
        return Column(Integer, ForeignKey(USER_TABLE_ID_FIELD))

    @declared_attr
    def author(cls):
        return relationship(USER_CLASS_NAME)

    @declared_attr
    def weight_spam_k(cls):
        """ weight_spam_k is a weight of an item wich computed in Karger's
        algorithm. Negative weight indicates spam.
        """
        return Column(Float)

    @declared_attr
    def participate_offline_spam_detection(cls):
        return Column(Boolean, default=True)

    @declared_attr
    def mark_for_mm(cls):
        """Mark the item fot metamoderation."""
        return Column(Boolean, default=False)

    @classmethod
    def get_items_offline_spam_detection(cls, session):
        items = session.query(cls).filer(
                     cls.participate_offline_spam_detection == True).all()
        return items

    @classmethod
    def get_add_item(cls, item_id, user_id, session):
        """ Method returns an item record. If it does not exist,
        it created a record in the table.
        """
        annot = session.query(cls).filter_by(id = item_id).first()
        if annot is None:
            annot = cls(item_id, user_id)
            session.add(annot)
            session.flush()
        return annot

    @classmethod
    def get_item(cls, item_id, session):
        annot = session.query(cls).filter_by(id = item_id).first()
        return annot

    @classmethod
    def add_item(cls, item_id, user_id, session):
        annot = cls(item_id, user_id)
        session.add(annot)
        session.flush()

    # todo(michiael): If ItemMixin will be used to add tables columns to
    # wider item class, then we need act in the same way as with
    # User table.
    def __init__(self, item_id, user_id):
        self.id = item_id
        self.author_id = user_id


class ActionMixin(object):

    __tablename__ = ACTION_TABLE_NAME
    cls = None

    # Id is an integer from range 1, 2, 3 ... .
    @declared_attr
    def id(cls):
        return Column(Integer, Sequence('action_id_seq', start=1, increment=1),
                      primary_key=True)

    # user_id is an id of an author who did the action.
    @declared_attr
    def user_id(cls):
        return Column(Integer, ForeignKey(USER_TABLE_ID_FIELD))

    @declared_attr
    def user(cls):
        return relationship(USER_CLASS_NAME)

    # item_id is an id of an item on which the action was performed.
    @declared_attr
    def item_id(cls):
        return Column(String, ForeignKey(ITEM_TABLE_ID_FIELD))

    @declared_attr
    def item(cls):
        return relationship(ITEM_CLASS_NAME)

    # Action type: upvote, downvote, flag spam ... .
    @declared_attr
    def type (cls):
        return Column(String)

    @declared_attr
    def value(cls):
        return Column(Float)

    @declared_attr
    def timestamp(cls):
        return Column(DateTime)

    @declared_attr
    def mark_for_mm(cls):
        """Mark the action fot metamoderation."""
        return Column(Boolean, default=False)

    @declared_attr
    def participate_offline_spam_detection(cls):
        """ If the field is true, then the action participate in offline spam
        detection."""
        return Column(Boolean, defauld=True)

    @classmethod
    def get_action(cls, item_id, user_id, action_type, session):
        action = session.query(cls).filter(and_(cls.user_id == user_id,
                                    cls.item_id == item_id,
                                    cls.type == action_type)).first()
        return action

    @classmethod
    def get_actions_offline_spam_detection(cls, session):
        actions = session.query(cls).filer(
                     cls.participate_offline_spam_detection == True).all()
        return actions

    @classmethod
    def add_action(cls, item_id, user_id, action_type, value,
                   timestamp, session):
        action = cls(item_id, user_id, action_type, value, timestamp)
        session.add(action)
        session.flush()

    # todo(michael): I assume that a class which inherits this mixin
    # will call next constructor.
    def __init__(self, item_id, user_id, action_type, value, timestamp):
        self.item_id = item_id
        self.user_id = user_id
        self.type = action_type
        self.value = value
        self.timestamp = timestamp


class ComputationMixin(object):
    """ After running offline computations for vandalism detection
    using Karger's algorithm, I need to store normalization coefficient.
    As for now, I am planning to store it in this table.
    """

    __tablename__ = "computation"
    cls = None

    @declared_attr
    def name(cls):
        return Column(String, primary_key=True)

    @declared_attr
    def normalization(cls):
        return Column(Float)
