# Implementation of Karger's algorithm with modifications.
import numpy as np

class Item(object):

    def __init__(self, item_id):
        self.id = item_id
        # weight is a message from item to users in Karger's algorithm
        # in other words it is a sum over all users j: A_ij * y_ji
        # where A_ij is vote/flag of user j to annotatio i, y_ji is reliability
        # of user j
        # todo(michael): connect default weight with null user in case of few votes?
        self.weight = 0
        # A list of messages from users.
        self.msgs = []
        self.users = []


class User(object):

    def __init__(self, user_id):
        self.id = user_id
        # Base reliability is the constant wich we add to user's reliability
        # on each iteration. We change base reliability whe user votes/flags on
        # item which is already defined as spam/ham and this item
        # does not participate in main Kargers's algorithm to reduce workload.
        self.base_reliability = 0
        # reliability is a sum over i of A_ij * x_ij, where i is item on which
        # the user provided feedback A_ij
        self.reliability = 0
        # answers is a dictionary of user's flags/votes: it maps item id to
        # answer A by the user.
        # In terms of spam/ham: if A is positive then the item is ham and if A
        # is negative it is spam.
        self.answers = {}
        # A list of messages from items.
        self.msgs = []
        self.items = []


class Msg(object):
    """ Class represents a message. Source_id is an id of a user or an item."""

    def __init__(self, source_id, value):
        self.source_id = source_id
        self.value = value


class Graph(object):

    def __init__(self):
        self.users = users
        self.items = items
        self.item_dict = {}
        self.user_dict = {}
        # normalization is to normalize user's reliability.
        self.normaliz = 1


def _propagate_from_users(self):
    for it in self.items:
        it.msgs = []

    for u in self.users:
        u.reliability = u.base_reliability
        # Computes user unnormalized reliability
        for msg in u.msgs:
            u.reliability += msg.value * u.answers[msg.source_id]
        # Computes list of values to obtain normalization coefficient later.
        reliab_list = []
        for msg in u.msgs:
            val = u.reliability - msg.value * u.answers[msg.source_id]
            reliab_list.append(val)
    # Computes normalization coefficient
    self.normaliz = np.sum(np.array(reliab_list) ** 2)
    self.normaliz /= float(len(reliab_list))
    self.normaliz = self.normaliz ** 0.5
    # Okay, now we send messages to items and compute user reliability
    for u in self.users:
        # Sends messages to items.
        for msg in u.msgs:
            val = u.reliability - msg.value * u.answers[msg.source_id]
            val /= self.normaliz
            it = self.items_dict[msg.source_id]
            it.msgs.append(Msg(u.id, val))
        # Computes normalized reliability
        u.reliability /= self.normaliz


def _propagate_from_items(self):
    for u in self.users:
        u.msgs = []

    for it in self.items:
        # todo(michael): Think through whether we need base weigh for
        # annotations in the same way we have base reliability.
        # todo(michael: Another point is that, after user's base reliability
        # reaches enough threshold, we want to cap it so it
        # would not screw (make very small) other values after normalization.
        it.weight = 0
        for msg in it.msgs:
            u = self.users_dict[msg.source_id]
            it.weight += msg.value * u.answers[it.id]
        # Sends messages to users.
        for msg in it.msgs:
            u = self.users_dict[msg.source_id]
            val = it.weight - msg.value * u.answers[it.id]
            u.msgs.append(Msg(it.id, val))
