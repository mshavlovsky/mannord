from sqlalchemy import create_engine, and_
from datetime import datetime
from models import (ActionMixin, UserMixin, ItemMixin,
                    ACTION_FLAG_SPAM, ACTION_UPVOTE,
                    ACTION_DOWNVOTE, THRESHOLD_SCORE_SPAM,
                    SCORE_DEFAULT)


def bind_engine(engine, session, base, should_create=True):
    # todo(michael): do I need to bind session? I don't use anywhere.
    session.configure(bind=engine)
    base.metadata.bind = engine
    if should_create:
        base.metadata.create_all(engine)


def bootstrap(base,engine):
    class Action(ActionMixin, base):
        pass
    base.metadata.create_all(engine)
    ActionMixin.cls = Action


