# Tables definition

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey
from sqlalchemy import DateTime, Sequence
from sqlalchemy.orm import relationship, backref


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    # todo(michael): how long should be id string?
    id = Column(String, primary_key=True)
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

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return "<User(id=%s, is_spammer=%s, score=%s, rep=%s)>"%(self.id,
                                   self.is_spammer, self.score, self.reputation)


class Annotation(Base):
    __tablename__ = 'annotation'

    id = Column(String, primary_key=True)
    is_spam = Column(Boolean, default=False)
    # Score of an annotation is between 0 and 1. It is the annotation's weight.
    # The annotation is more important if it has higher score.
    score = Column(Float, default=0.5)
    # Parameters of a score distribution.
    score_distr_param_a = Column(Float, default=0)
    score_distr_param_b = Column(Float, default=0)
    # An id of the author.
    author_id = Column(String, ForeignKey('user.id'))
    author = relationship('User')

    def __init__(self, id, author_id):
        self.id = id
        self.author_id = author_id

    def __repr__(self):
        return "<Annotation(id=%s, is_spam=%s, score=%s)>" % (self.id,
                                                       self.is_spam, self.score)


class Action(Base):
    __tablename__ = 'action'
    # Id is an integer from range 1, 2, 3 ... .
    id = Column(Integer, Sequence('action_id_seq', start=1, increment=1),
                primary_key=True)
    # user_id is an id of an author who did the action.
    user_id = Column(String, ForeignKey('user.id'))
    user = relationship("User")
    # annotation_id is an id of an annotation on which the action was performed.
    annotation_id = Column(String, ForeignKey('annotation.id'))
    annotation = relationship('Annotation')
    # Action type: upvote, downvote, flag spam ... .
    type = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime)


    def __init__(self, annotation_id, user_id, type, value, timestamp):
        self.annotation_id = annotation_id
        self.user_id = user_id
        self.type = type
        self.value = value
        self.timestamp = timestamp

    def __repr__(self):
        s = "<Action(id=%s, annotation_id=%s, user_id=%s, type=%s, value=%s, timestamp%s)>"
        s = s % (self.id, self.annotation_id, self.user_id, self.type,
                 self.value, self.timestamp)
        return s
