# Tables definition

from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        ForeignKey, DateTime, Sequence)
from sqlalchemy.orm import relationship, backref


# todo(michael): there is an issue when using foreign keys.
# We don't know tables' and classes' names of tables.
# For now I use global constants to keep these names, if that okay then
# it makes sence to move constants into a config file.

# Constants
USER_TABLE_ID_FIELD = 'user.id'
USER_CLASS_NAME = 'User'
ANNOTATION_TABLE_ID_FIELD = 'annotation.id'
ANNOTATION_CLASS_NAME = 'Annotation'

ACTION_UPVOTE = 'upvote'
ACTION_DOWNVOTE = 'downvote'
ACTION_FLAG_SPAM = 'flag_spam'

THRESHOLD_SCORE_SPAM = 0.1
SCORE_DEFAULT = 0.5


class UserMixin(object):

    @declared_attr
    def id(cls):
        return Column(String, primary_key=True)

    is_spammer = Column(Boolean)
    # score is "internal" reputation and it is a real value between 0 and 1,
    # We trust 100% to a user with a score 1 and we don't trust to a user with
    # score 0.
    score = Column(Float, default=0.5)
    # Parameters of a score distribution.
    score_distr_param_a = Column(Float, default=0)
    score_distr_param_b = Column(Float, default=0)
    # Reputation of a user. This value is exposed to users.
    reputation = Column(Float, default=0)


class AnnotationMixin(object):

    @declared_attr
    def id(cls):
        return Column(String, primary_key=True)

    is_spam = Column(Boolean, default=False)
    spam_flag_counter = Column(Integer, default=0)
    # Score of an annotation is between 0 and 1. It is the annotation's weight.
    # The annotation is more important if it has higher score.
    score = Column(Float, default=0.5)
    # Parameters of a score distribution.
    score_distr_param_a = Column(Float, default=0)
    score_distr_param_b = Column(Float, default=0)

    # An id of the author.
    @declared_attr
    def author_id(cls):
        return Column(String, ForeignKey(USER_TABLE_ID_FIELD))

    @declared_attr
    def author(cls):
        return relationship(USER_CLASS_NAME)

    @classmethod
    def is_annotation_spam(cls, annotation_id, session):
        annotation = session.query(cls).filter_by(id = annotation_id).first()
        if annotation is not None:
            return annotation.is_spam
        return None

    @classmethod
    def increase_spam_counter(cls, annotation_id, session):
        annotation = session.query(cls).filter_by(id = annotation_id).first()
        annotation.spam_flag_counter = annotation.spam_flag_counter + 1
        session.flush()


class ActionMixin(object):

    # Id is an integer from range 1, 2, 3 ... .
    @declared_attr
    def id(cls):
        return Column(Integer, Sequence('action_id_seq', start=1, increment=1),
                      primary_key=True)

    # user_id is an id of an author who did the action.
    @declared_attr
    def user_id(cls):
        return Column(String, ForeignKey(USER_TABLE_ID_FIELD))

    @declared_attr
    def user(cls):
        return relationship(USER_CLASS_NAME)

    # annotation_id is an id of an annotation on which the action was performed.
    @declared_attr
    def annotation_id(cls):
        return Column(String, ForeignKey(ANNOTATION_TABLE_ID_FIELD))

    @declared_attr
    def annotation(cls):
        return relationship(ANNOTATION_CLASS_NAME)

    # Action type: upvote, downvote, flag spam ... .
    type = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime)

    @classmethod
    def get_action(cls, annotation_id, user_id, action_type, session):
        action = session.query(cls).filter(and_(cls.user_id == user_id,
                                    cls.annotation_id == annotation_id,
                                    cls.type == action_type)).first()
        return action

    @classmethod
    def add_action(cls, annotation_id, user_id, action_type, value,
                   timestamp, session):
        action = cls(annotation_id, user_id, action_type, value, timestamp)
        session.add(action)
        session.flush()


    # todo(michael): I assume that a class whcih will inherit this mixin
    # will use next constructor.
    def __init__(self, annotation_id, user_id, action_type, value, timestamp):
        self.annotation_id = annotation_id
        self.user_id = user_id
        self.type = type
        self.value = value
        self.timestamp = timestamp
