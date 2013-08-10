from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        ForeignKey, DateTime, Sequence, and_)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
import graph_k as gk
import graph_d as gd


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

# Explanation of prefixes of column names.
#   - sk - a field related to spam detection using karger's algorithm
#   - sd - a filed related to spam detection based on Dirichlet distribution


# Notes: A spam karma user always votes "not spam" on annotations
# created by a user. Reliability of the spam karma user reflects whether user
# is spammer or not. If it has negative reliability then the user is spammer.


class UserMixin(object):

    cls = None

    @declared_attr
    def id(cls):
        return Column(Integer, autoincrement=True, primary_key=True)

    @declared_attr
    def is_spammer(cls):
        return Column(Boolean, default=False)

    # Fields related to spam detection using Karger's algorithm (sk_ prefix)
    @declared_attr
    def sk_base_reliab(cls):
        """ This field is a base raliability of a user for spam detection task.
        """
        return Column(Float, default=0)

    @declared_attr
    def sk_reliab(cls):
        """ Spam detection reliability"""
        return Column(Float, default=0)

    @declared_attr
    def sk_reliab_raw(cls):
        """ Raw reliability is user's reliability before applying asymptotic
        function or normalization. We need it to perform online update.
        """
        return Column(Float, default=0)

    @declared_attr
    def sk_karma_user_base_reliab(cls):
        """ This field is a base reliability for a karma user ("null" user) who
        always votes positively for the user's annotation."""
        return Column(Float, default=0)

    @declared_attr
    def sk_karma_user_reliab(cls):
        return Column(Float, default=0)

    # Fields related to spam detection using Dirichlet distribution (sd_ prefix)
    @declared_attr
    def sd_reliab(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_u_n(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_u_p(cls):
        return Column(Float, default=0)

    def sd_karma_user_reliab(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_karma_user_u_n(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_karma_user_u_p(cls):
        return Column(Float, default=0)


class ItemMixin(object):
    """ Item is an object like annotation, post, etc. Moderation actions
    are perfored on items.
    """

    __tablename__ = ITEM_TABLE_NAME
    cls = None

    @declared_attr
    def id(cls):
        return Column(String, primary_key=True)

    @declared_attr
    def parent_id(cls):
        return Column(String, ForeignKey(ITEM_TABLE_ID_FIELD))

    @declared_attr
    def parent(cls)
        return relationship(ITEM_CLASS_NAME)

    # Authors's id
    @declared_attr
    def author_id(cls):
        return Column(Integer, ForeignKey(USER_TABLE_ID_FIELD))

    @declared_attr
    def author(cls):
        return relationship(USER_CLASS_NAME)

    @declared_attr
    def is_spam(cls):
        return Column(Boolean, default=False)

    @declared_attr
    def is_ham(cls):
        return Column(Boolean, default=False)

    @declared_attr
    def spam_flag_counter(cls):
        return Column(Integer, default=0)

    @declared_attr
    def marked_for_mm(cls):
        """If the filed is true then the item is marked for metamoderation."""
        return Column(Boolean, default=False)

    # Fields related to spam detection using Karger's algorithm (sk_ prefix)
    @declared_attr
    def sk_weight(cls):
        """ weight_spam_k is a weight of an item wich computed in Karger's
        algorithm. Negative weight indicates spam.
        """
        return Column(Float)

    @declared_attr
    def sk_frozen(cls):
        return Column(Boolean, default=False)

    @classmethod
    def sk_get_items_offline_spam_detect(cls, session):
        items = session.query(cls).filer(
                     cls.sk_frozen == False).all()
        return items

    @declared_attr
    def sd_weight(cls):
        """ weight_spam_k is a weight of an item wich computed in Karger's
        algorithm. Negative weight indicates spam.
        """
        return Column(Float)

    # Fields related to spam detection using Dirichlet distribution (sd_ prefix)
    @declared_attr
    def sd_frozen(cls):
        return Column(Boolean, default=False)

    @classmethod
    def sd_get_items_offline_spam_detect(cls, session):
        items = session.query(cls).filer(
                     cls.sd_frozen == False).all()
        return items

    @classmethod
    def get_add_item(cls, item_id, user, session):
        """ Method returns an item record. If it does not exist,
        it created a record in the table.
        """
        annot = cls.get_item(item_id, session)
        if annot is None:
            annot = cls.add_item(item_id, user, session)
        return annot

    @classmethod
    def get_item(cls, item_id, session):
        annot = session.query(cls).filter_by(id = item_id).first()
        return annot

    @classmethod
    def add_item(cls, item_id, user, session):
        annot = cls(item_id, user.id)
        # Computes initial spam weight of the item according do Karger's algo.
        val = user.sk_reliab_karma_user * gk.ALGO_KARGER_KARMA_USER_VOTE
        val = gk.asympt_func(val)
        annot.sk_weight = val
        # Computes initial spam weight of the item according do Dirichelt
        u_n = user.sd_karma_user_u_n
        u_p = user.sd_karma_user_u_p
        annot.sd_weight = gd.get_item_weight(u_n, u_p)
        session.add(annot)
        session.flush()
        return annot

    # todo(michiael): If ItemMixin will be used to add tables columns to
    # wider item class, then we need act in the same way as with
    # User table.
    def __init__(self, item_id, user_id):
        self.id = item_id
        self.author_id = user_id


class ActionMixin(object):
    # todo(michael): some annotation correspond to action. We need to take care
    # of it.

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
    def timestamp(cls):
        return Column(DateTime)

    @declared_attr
    def mark_for_mm(cls):
        """Mark the action fot metamoderation."""
        return Column(Boolean, default=False)

    @classmethod
    def get_action(cls, item_id, user_id, action_type, session):
        action = session.query(cls).filter(and_(cls.user_id == user_id,
                                    cls.item_id == item_id,
                                    cls.type == action_type)).first()
        return action

    # Fields related to spam detection using Karger's algorithm (sk_ prefix)
    @declared_attr
    def sk_frozen(cls):
        """ If the field is true, then the action participate in offline spam
        detection."""
        return Column(Boolean, defauld=True)

    @classmethod
    def sk_get_actions_offline_spam_detect(cls, session):
        actions = session.query(cls).filer(
                     cls.sk_frozen == False).all()
        return actions

    # Fields related to spam detection using Dirichlet distribution (sd_ prefix)
    @declared_attr
    def sd_frozen(cls):
        """ If the field is true, then the action participate in offline spam
        detection."""
        return Column(Boolean, defauld=True)

    @classmethod
    def sd_get_actions_offline_spam_detect(cls, session):
        actions = session.query(cls).filer(
                     cls.sd_frozen == False).all()
        return actions

    @classmethod
    def add_action(cls, item_id, user_id, action_type, value,
                   timestamp, session):
        action = cls(item_id, user_id, action_type, value, timestamp)
        session.add(action)
        session.flush()

    # todo(michael): I assume that a class which inherits this mixin
    # will call next constructor.
    def __init__(self, item_id, user_id, action_type, timestamp):
        self.item_id = item_id
        self.user_id = user_id
        self.type = action_type
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
