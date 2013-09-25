import os
import ConfigParser
from pkg_resources import resource_string, resource_filename
from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        ForeignKey, DateTime, Sequence, and_)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.expression import func
from spam_detection_mixins import (UserDirichletMixin, ItemDirichletMixin,
                                   ActionDirichletMixin, UserKargerMixin,
                                   ItemKargerMixin, ActionKargerMixin)
import spam_utils as su
import graph_k as gk
import graph_d as gd


# Reads config file
file_path_config = resource_filename(__name__, 'mannord.conf')
ini_config = ConfigParser.ConfigParser()
ini_config.readfp(open(file_path_config))


# Constants
USER_TABLE_ID_FIELD = ini_config.get('names','USER_TABLE_ID_FIELD')
USER_CLASS_NAME =  ini_config.get('names','USER_CLASS_NAME')
ITEM_TABLE_ID_FIELD =  ini_config.get('names', 'ITEM_TABLE_ID_FIELD')
ITEM_CLASS_NAME =  ini_config.get('names', 'ITEM_CLASS_NAME')
ITEM_TABLE_NAME =   ini_config.get('names', 'ITEM_TABLE_NAME')
ACTION_TABLE_NAME =   ini_config.get('names', 'ACTION_TABLE_NAME')
ACTION_TABLE_NAME_ID_FIELD =  ini_config.get('names', 'ACTION_TABLE_NAME_ID_FIELD')
ACTION_CLASS_NAME =   ini_config.get('names', 'ACTION_CLASS_NAME')
ACTION_UPVOTE =   ini_config.get('names', 'ACTION_UPVOTE')
ACTION_DOWNVOTE =   ini_config.get('names', 'ACTION_DOWNVOTE')
ACTION_FLAG_SPAM =   ini_config.get('names', 'ACTION_FLAG_SPAM')
ACTION_FLAG_HAM =    ini_config.get('names', 'ACTION_FLAG_HAM')
COMPUTATION_SK_NAME =   ini_config.get('names', 'COMPUTATION_SK_NAME')


STRING_FIELD_LENGTH = 32
# Explanation of prefixes of column names.
#   - sk - a field related to spam detection using karger's algorithm
#   - sd - a filed related to spam detection based on Dirichlet distribution


# Notes: A spam karma user always votes "not spam" on annotations
# created by a user. Reliability of the spam karma user reflects whether user
# is spammer or not. If it has negative reliability then the user is spammer.


class UserMixin(UserDirichletMixin, UserKargerMixin, object):

    cls = None

    @declared_attr
    def id(cls):
        return Column(Integer, autoincrement=True, primary_key=True)

    @declared_attr
    def is_spammer(cls):
        return Column(Boolean, default=False)

    @declared_attr
    def vote_counter(cls):
        return Column(Integer, default=0)

    @declared_attr
    def mm_vote_counter(cls):
        return Column(Integer, default=0)


class ItemMixin(ItemDirichletMixin, ItemKargerMixin, object):
    """ Item is an object like annotation, post, etc.
    """

    __tablename__ = ITEM_TABLE_NAME
    cls = None

    @declared_attr
    def id(cls):
        return Column(String(STRING_FIELD_LENGTH), primary_key=True)

    # Authors's id
    @declared_attr
    def author_id(cls):
        return Column(Integer, ForeignKey(USER_TABLE_ID_FIELD))

    @declared_attr
    def author(cls):
        return relationship(USER_CLASS_NAME)

    @declared_attr
    def page_url(cls):
        """ page_url is an url of a page where annotation is left."""
        return Column(String(STRING_FIELD_LENGTH))

    # Defines parent-children relation between items.
    @declared_attr
    def parent_id(cls):
        return Column(String(STRING_FIELD_LENGTH), ForeignKey(ITEM_TABLE_ID_FIELD))

    @declared_attr
    def children(cls):
        id = "%s.id" % ITEM_CLASS_NAME
        return relationship(ITEM_CLASS_NAME,
                            backref=backref('parent', remote_side=id))

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
        """Mark the action fot metamoderation."""
        return Column(Boolean, default=False)

#    @declared_attr
#    def is_mm(cls):
#        """ True if the action is metamoderation."""
#        return Column(Boolean, default=False)

    @classmethod
    def get_item(cls, item_id, session):
        annot = session.query(cls).filter_by(id = item_id).first()
        return annot

    @classmethod
    def get_items_on_page(cls, page_url, session):
        return session.query(cls).filter_by(page_url = page_url).all()

    @classmethod
    def get_items_by_author(cls, user_id, session):
        return session.query(cls).filter_by(author_id = user_id).all()

    @classmethod
    def get_n_items_for_spam_mm_randomly(cls, n, session):
        return session.query(cls).filter(cls.marked_for_mm == True
                                     ).order_by(func.random()).limit(n).all()


    def __init__(self, page_url, item_id, user, parent_id=None,
                 spam_detect_algo=su.ALGO_KARGER):
        self.page_url = page_url
        self.id = item_id
        self.author_id = user.id
        val = user.sk_karma_user_reliab * gk.KARMA_USER_VOTE
        self.sk_weight = gk.asympt_func(val)
        # Computes initial spam weight of the item according do Dirichelt
        u_n = user.sd_karma_user_u_n
        u_p = user.sd_karma_user_u_p
        self.sd_weight = gd.get_item_weight(u_n, u_p)
        self.parent_id = parent_id
        # Marks for metamoderation if needed.
        su.mark_spam_ham_or_mm(self, algo_type=spam_detect_algo)
        # If an item is also action on another item then create this action.

    def __repr__(self):
        return '<Item %s>' % self.id


class ActionMixin(ActionDirichletMixin, ActionKargerMixin, object):

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
        return Column(String(STRING_FIELD_LENGTH), ForeignKey(ITEM_TABLE_ID_FIELD))

    @declared_attr
    def item(cls):
        """ Item on which the action was performed."""
        item_id = "%s.item_id" % ACTION_CLASS_NAME
        return relationship(ITEM_CLASS_NAME, foreign_keys=item_id)

    # Configuring item which is twin to an action
    @declared_attr
    def item_twin_id(cls):
        return Column(String(STRING_FIELD_LENGTH), ForeignKey(ITEM_TABLE_ID_FIELD))

    @declared_attr
    def item_twin(cls):
        """ Some items can be iterpreted as action.
        item_twin is an item which corresponds to the action."""
        item_twin_id = "%s.item_twin_id" % ACTION_CLASS_NAME
        return relationship(ITEM_CLASS_NAME,
                            backref=backref('action_twin', uselist=False),
                            foreign_keys=item_twin_id)

    # Action type: upvote, downvote, flag spam ... .
    @declared_attr
    def type (cls):
        return Column(String(STRING_FIELD_LENGTH))

    @declared_attr
    def timestamp(cls):
        return Column(DateTime)

    @declared_attr
    def marked_for_mm(cls):
        """Mark the action fot metamoderation."""
        return Column(Boolean, default=False)

    @classmethod
    def get_action(cls, item_id, user_id, action_type, session):
        action = session.query(cls).filter(and_(cls.user_id == user_id,
                                    cls.item_id == item_id,
                                    cls.type == action_type)).first()
        return action


    @classmethod
    def add_action(cls, item_id, user_id, action_type, value,
                   timestamp, session, item_twin_id=None):
        action = cls(item_id, user_id, action_type, value, timestamp,
                                                    item_twin_id = item_twin_id)
        session.add(action)
        session.flush()

    @classmethod
    def get_actions_on_item(cls, item_id, session):
        actions = session.query(cls).filter(cls.item_id == item_id).all()
        return actions

    @classmethod
    def get_actions_by_user(cls, user_id, session):
        actions = session.query(cls).filter(cls.user_id == user_id).all()
        return actions


    # note(michael): I assume that a class which inherits this mixin
    # will call next constructor.
    def __init__(self, item_id, user_id, action_type, timestamp, item_twin_id=None):
        self.item_id = item_id
        self.user_id = user_id
        self.type = action_type
        self.timestamp = timestamp
        # item_id and item_twin_id cannot coinside
        if item_id == item_twin_id:
            raise Exception("An action cannot be performed on an item which represents the action!!!")
        self.item_twin_id = item_twin_id

    def __repr__(self):
        return '<Action of user %s on item %s, type %s>' % (self.user_id,
                                        self.item_id, self.type)


class ComputationMixin(object):
    """ After running offline computations for vandalism detection
    using Karger's algorithm, I need to store normalization coefficient.
    As for now, I am planning to store it in this table.
    """

    __tablename__ = "computation"
    cls = None

    @declared_attr
    def name(cls):
        return Column(String(STRING_FIELD_LENGTH), primary_key=True)

    @declared_attr
    def normalization(cls):
        return Column(Float, default=1.0)

    @classmethod
    def get(cls, name, session):
        comp = session.query(cls).filter(
                     cls.name == name).first()
        if comp is None:
            comp = cls(name)
            session.add(comp)
            session.flush()
        return comp

    def __init__(self, name):
        self.name = name
        self.normalization = 1.0

    def __repr__(self):
        return "<Computation Values %s, normaliz %s>" % (self.name, self.normalization)
