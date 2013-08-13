# Implementation of Karger's algorithm with some modifications.
import numpy as np

USE_ASYMPTOTIC_FUNC = True
DEBUG = False

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

    def __repr__(self):
        return '<Item %s>' % self.id


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
        # Raw reliability is user's reliability before applying asymptotic
        # function or normalization. We need it to perform online update.
        self.reliability_raw = 0
        # answers is a dictionary of user's flags/votes: it maps item id to
        # answer A by the user.
        # In terms of spam/ham: if A is positive then the item is ham and if A
        # is negative it is spam.
        self.answers = {}
        # A list of messages from items.
        self.msgs = []

    def __repr__(self):
        return '<User %s>' % self.id


def asympt_func(val):
    # Asymptote reflects how much one user can be more 'powerfull' than another.
    # For instance, if asymptote is 10 then a user with a high reliability has
    # vote weight as 10 votes of default users.
    # Aymptotic function is applied:
    #   - to value of message from items to users - this way we reduce effect
    #     of one annotation in computing users reliability.
    #   - to value of message from user to items - to reduce influence of
    #     the user.
    asymptote = 10
    return asymptote * (2/np.pi) * np.arctan(val * 1.6 / asymptote)


class Msg(object):
    """ Class represents a message. Source_id is an id of a user or an item."""

    def __init__(self, source_id, value):
        self.source_id = source_id
        self.value = value


class Graph(object):

    def __init__(self):
        self.users = []
        self.items = []
        self.item_dict = {}
        self.user_dict = {}
        # normalization is to normalize user's reliability.
        self.normaliz = 1

    def __repr__(self):
        s = 'Graph \n'
        for u in self.users:
            for it_id in u.answers:
                s = '%s user %s -> item %s, value %s \n' % (s, u.id, it_id,
                                                               u.answers[it_id])
        return s

    @classmethod
    def from_lists(cls, user_list, item_list):
        """ Creates graph from list of users ans items."""
        g = cls()
        for u in user_list:
            g.users.append(u)
            g.user_dict[u.id] = u
        for it in item_list:
            g.items.append(it)
            g.item_dict[it.id] = it
        return g

    def add_answer(self, user_id, item_id, answer, base_reliability=0):
        """ Method adds answer to dictionary user.answers. If user or item
        with give ids does not exist then the method creates it.
        """
        u = self.user_dict.get(user_id)
        if not u:
            u = User(user_id)
            u.base_reliability = base_reliability
            self.users.append(u)
            self.user_dict[user_id] = u
        it = self.item_dict.get(item_id)
        if not it:
            it = Item(item_id)
            self.items.append(it)
            self.item_dict[item_id] = it
        # Adds answer
        u.answers[it.id] = answer

    def get_item(self, item_id):
        return self.item_dict.get(item_id)

    def get_user(self, user_id):
        return self.user_dict.get(user_id)

    def _propagate_from_users(self):
        for it in self.items:
            it.msgs = []

        for u in self.users:
            u.reliability = u.base_reliability
            # Computes user unnormalized reliability
            for msg in u.msgs:
                u.reliability += msg.value# * u.answers[msg.source_id]
            # Computes list of values to obtain normalization coefficient later.
            reliab_list = []
            for msg in u.msgs:
                val = u.reliability - msg.value# * u.answers[msg.source_id]
                reliab_list.append(val)
        # Computes normalization coefficient
        self.normaliz = np.sum(np.array(reliab_list) ** 2)
        self.normaliz /= float(len(reliab_list))
        self.normaliz = self.normaliz ** 0.5
        if self.normaliz == 0:
            # If noramlization is zero then all messages have zero value!
            # In this case we make normalization to 1.
            self.normaliz = 1.0

        # Okay, now we send messages to items and compute user reliability
        for u in self.users:
            # Sends messages to items.
            for msg in u.msgs:
                # todo(michael): reliability should not be multiplied by answer!
                val = u.reliability - msg.value# * u.answers[msg.source_id]
                val = (val + u.base_reliability) * u.answers[msg.source_id]
                if USE_ASYMPTOTIC_FUNC:
                    val = asympt_func(val)
                else:
                    val /= self.normaliz
                it = self.item_dict[msg.source_id]
                it.msgs.append(Msg(u.id, val))

            u.reliability_raw = u.reliability
            if USE_ASYMPTOTIC_FUNC:
                # Applies asymptotic function to user's reliability
                u.reliability = asympt_func(u.reliability)
            else:
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
            # would not screw (make very small) other values after normalization
            it.weight = 0
            for msg in it.msgs:
                u = self.user_dict[msg.source_id]
                it.weight += msg.value# * u.answers[it.id]
            # Sends messages to users.
            for msg in it.msgs:
                u = self.user_dict[msg.source_id]
                val = it.weight - msg.value# * u.answers[it.id]
                val = val * u.answers[it.id]
                if USE_ASYMPTOTIC_FUNC:
                    val = asympt_func(val)
                u.msgs.append(Msg(it.id, val))

    def _aggregate_items(self):
        """ Aggregates information for items """
        for it in self.items:
            it.weight = 0
            for msg in it.msgs:
                u = self.user_dict[msg.source_id]
                it.weight += msg.value# * u.answers[it.id]


    def compute_answers(self, k_max):
        # Sends the initial messages from users to items.
        for it in self.items:
            it.msgs = []
        for u in self.users:
            for it_id in u.answers.iterkeys():
                it = self.item_dict[it_id]
                # todo(michael): is it necessary to randomize initial y's?
                it.msgs.append(Msg(u.id, u.answers[it_id]))# * np.random.normal(1,1)))
        if DEBUG:
            print ""
            print "messages from users"
            for it in self.items:
                for msg in it.msgs:
                    print ('user id=%s -> item id=%s, value=%s' %
                                    (msg.source_id, it.id, msg.value))
        # Runs main iterations.
        for i in xrange(k_max):
            self._propagate_from_items()
            if DEBUG:
                print ""
                print "messages from items"
                for u in self.users:
                    for msg in u.msgs:
                        print ('item id=%s -> user_id= %s, value=%s' %
                                (msg.source_id, u.id,  msg.value))
            self._propagate_from_users()
            if DEBUG:
                print ""
                print "messages from users"
                for it in self.items:
                    for msg in it.msgs:
                        print ('user id=%s -> item id=%s, value=%s' %
                                        (msg.source_id, it.id, msg.value))
        # Aggregating item information.
        self._aggregate_items()
