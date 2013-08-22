from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import (Column, Integer, Float, String, Boolean,
                        ForeignKey, DateTime, Sequence, and_)


class UserDirichletMixin(object):
    """ Field of this class contains information necessary for spam detection
    according to dirichlet method."""

    @declared_attr
    def sd_base_u_n(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_base_u_p(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_reliab(cls):
        """ Spam detection reliability is computed based on u_n and u_p."""
        return Column(Float, default=0)

    @declared_attr
    def sd_u_n(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_u_p(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_karma_user_base_u_n(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_karma_user_base_u_p(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_karma_user_reliab(cls):
        """ Spam detection reliability"""
        return Column(Float, default=0)

    @declared_attr
    def sd_karma_user_u_n(cls):
        return Column(Float, default=0)

    @declared_attr
    def sd_karma_user_u_p(cls):
        return Column(Float, default=0)


class ItemDirichletMixin(object):
    """ Item fields which contains information necessary for spam detection
    according to Dirichlet algorithm."""

    @declared_attr
    def sd_c_n(cls):
        """ 'Number' of negative votes for the item"""
        return Column(Float, default=0)

    @declared_attr
    def sd_c_p(cls):
        """ 'Number' of positive votes for the item"""
        return Column(Float, default=0)

    @declared_attr
    def sd_weight(cls):
        """ weight_spam_k is a weight of an item wich computed in Karger's
        algorithm. Negative weight indicates spam.
        """
        return Column(Float)

    @declared_attr
    def sd_frozen(cls):
        return Column(Boolean, default=False)

    @classmethod
    def sd_get_items_offline_spam_detect(cls, session):
        items = session.query(cls).filter(
                     cls.sd_frozen == False).all()
        return items

class ActionDirichletMixin(object):

    @declared_attr
    def sd_frozen(cls):
        """ If the field is true, then the action participate in offline spam
        detection."""
        return Column(Boolean, default=False)

    @classmethod
    def sd_get_actions_offline_spam_detect(cls, session):
        actions = session.query(cls).filter(
                     cls.sd_frozen == False).all()
        return actions


class UserKargerMixin(object):
    """ Fileds of this class contains information necessary for spam detection
    according to the algorithm by Karger."""

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

class ItemKargerMixin(object):

    @declared_attr
    def sk_weight(cls):
        """ weight_spam_k is a weight of an item wich computed in Karger's
        algorithm. Negative weight indicates spam.
        """
        return Column(Float, default=0)

    @declared_attr
    def sk_frozen(cls):
        return Column(Boolean, default=False)

    @classmethod
    def sk_get_items_offline_spam_detect(cls, session):
        items = session.query(cls).filter(
                     cls.sk_frozen == False).all()
        return items

class ActionKargerMixin(object):

    @declared_attr
    def sk_frozen(cls):
        """ If the field is true, then the action does not participate in
        offline spam detection."""
        return Column(Boolean, default=False)

    @classmethod
    def sk_get_actions_offline_spam_detect(cls, session):
        actions = session.query(cls).filter(
                     cls.sk_frozen == False).all()
        return actions
