# Spam detection algorithm in spirit of belief propagation (like Karger's algo).
# Use's reliability is computed using Dirichlet dist.
import numpy as np

ALGO_DIRICHLET_KARMA_USER_VOTE = 0.1

DEBUG = False


def compute_percentile_dirichlet(neg, pos, percentile):
    """ Numerically computes percentile of Dirichlet distribution.
    Percentile is between 0 and 1.
    """
    # alpha is a number of "Truth"
    # beta is a number of "False"
    alpha, beta = pos, abs(neg)
    # Sanity check for testing purposes.
    if alpha > 1000000 or beta > 1000000:
        raise Exception("Alpha or Beta is too big!!!")
    # First, numerically compute unnormalised probability mass function.
    delta = 0.0001
    x = np.arange(0 + delta, 1, delta)
    y = x ** (alpha) * (1 - x) ** (beta)
    # Integral approximation based on trapezoidal rule.
    y1 = y[:-1]
    y2 = y[1:]
    integral_vec = (y2 + y1) / 2 * delta
    integral = np.sum(integral_vec)
    cumsum = np.cumsum(integral_vec)
    threshold = (1 - percentile) * integral
    idx = cumsum.searchsorted(threshold)
    val = idx * delta
    return val


def get_reliability(u_n, u_p):
    perc = 0.8
    # todo(michael): mid_point determines what is default attitude towards
    # a user. If it is 0 then we treat user with no feedback positively.
    # If we compute mod_point as percentile of 0,0 case, then user would
    # have any impact only if it has some agreement with other users.
    # todo(michael): Another important property in a case when a new user
    # has zero reliability is that user's reliability converges to zero.
    # Understand better this behaviour.

    #mid_point = compute_percentile_dirichlet(0, 0, perc)
    mid_point = 0
    val = compute_percentile_dirichlet(u_n, u_p, perc)
    val = max(0, val - mid_point)
    val = (val / (1 - mid_point)) ** 2
    return val


def get_item_weight(c_n, c_p):
    perc = 0.8
    mid_point = compute_percentile_dirichlet(0, 0, perc)
    val = compute_percentile_dirichlet(c_n, c_p, perc)
    return val - mid_point


def neg_first(val1, val2):
    """A helper function which returns a tuple of original values.
    It puts negative item on the first place"""
    # Sanity check.
    if val1 * val2 > 0:
        raise Exception("Number should have opposite sign.")
    if val1 < 0:
        return val1, val2
    if val2 < 0:
        return val2, val1
    # If we reached this point than one values is at leas zero and
    # it should go first.
    if val1 > 0:
        return val2, val1
    return val1, val2


class Item(object):

    def __init__(self, item_id):
        self.id = item_id
        # c_p is a sum of positive signals sent towards the item
        self.c_p = 0
        # c_n is a sum of negative signals sent towards the item
        self.c_n = 0
        self.weight = 0
        # A list of messages from users.
        self.msgs = []

    def __repr__(self):
        return '<Item %s, weight %s >' % (self.id, self.weight)


class User(object):

    def __init__(self, user_id, base_u_n=0, base_u_p=0):
        self.id = user_id
        self.base_u_n = base_u_n
        self.base_u_p = base_u_p
        self.u_n = base_u_n
        self.u_p = base_u_p
        self.reliability = get_reliability(base_u_n, base_u_p)
        # answers is a dictionary of user's flags/votes: it maps item id to
        # answer A by the user.
        # In terms of spam/ham: if A is positive then the item is ham and if A
        # is negative it is spam.
        self.answers = {}
        # A list of messages from items.
        self.msgs = []

    def __repr__(self):
        return '<User %s, reliability %s>' % (self.id, self.reliability)


class Message_to_user(object):
    """ A message from item to user."""

    def __init__(self, item_id, c_n, c_p):
        self.item_id = item_id
        self.c_n = c_n
        self.c_p = c_p

    def __repr__(self):
        return "Message from item %s, c_n = %s, c_p = %s" % (self.item_id,
                                                    self.c_n, self.c_p)

class Message_to_item(object):
    """ A message from user to item."""

    def __init__(self, user_id, value):
        self.user_id = user_id
        self.value = value

    def __repr__(self):
        return "Message from user %s, value = %s " % (self.user_id, self.value)


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
            s = '%s %s\n' % (s, u)
        for it in self.items:
            s = '%s %s\n' % (s, it)
        for u in self.users:
            for it_id in u.answers:
                s = '%s user %s -> item %s, value %s \n' % (s, u.id, it_id,
                                                               u.answers[it_id])
        return s

    def add_answer(self, user_id, item_id, answer, base_u_n=0, base_u_p=0):
        """ Method adds answer to dictionary user.answers. If user or item
        with give ids does not exist then the method creates it.
        """
        u = self.user_dict.get(user_id)
        if not u:
            u = User(user_id, base_u_n, base_u_p)
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
        # For each user computes u_n and u_p  over ALL item.
        # To get u_n and u_p for a particular item we need to subtract a value
        # related to the item from u_n and u_p.
        for u in self.users:
            u.u_n = u.base_u_n
            u.u_p = u.base_u_p
            for msg in u.msgs:
                A = u.answers[msg.item_id]
                val_n, val_p = neg_first(msg.c_n * np.sign(A), msg.c_p * np.sign(A))
                u.u_n += val_n
                u.u_p += val_p
            u.reliability = get_reliability(u.u_n, u.u_p)
        # Okay, now we send messages to items and compute user reliability
        for u in self.users:
            # Sends messages to items.
            for msg in u.msgs:
                A = u.answers[msg.item_id]
                val_n, val_p = neg_first(msg.c_n * np.sign(A), msg.c_p * np.sign(A))
                reliab = get_reliability(u.u_n - val_n, u.u_p - val_p)
                # Gets item.
                it = self.item_dict[msg.item_id]
                it.msgs.append(Message_to_item(u.id, A * reliab))


    def _propagate_from_items(self):
        for u in self.users:
            u.msgs = []

        for it in self.items:
            it.c_n, it.c_p = 0, 0
            for msg in it.msgs:
                u = self.user_dict[msg.user_id]
                #val = u.answers[it.id] * u.reliability
                #val = u.answers[it.id] * msg.value
                val = msg.value
                if val < 0:
                    it.c_n += val
                else:
                    it.c_p += val
            # Sends messages to users.
            for msg in it.msgs:
                u = self.user_dict[msg.user_id]
                #val = u.answers[it.id] * u.reliability
                #val = u.answers[it.id] * msg.value
                val = msg.value
                c_n = it.c_n
                c_p = it.c_p
                if val < 0:
                    c_n -= val
                else:
                    c_p -= val
                u.msgs.append(Message_to_user(it.id, c_n, c_p))


    def _compute_items_weight(self):
        for it in self.items:
            it.weight = get_item_weight(it.c_n, it.c_n)


    def _aggregate_items(self):
        """ Aggregates information for items """
        for it in self.items:
            it.c_n, it.c_p = 0, 0
            for msg in it.msgs:
                u = self.user_dict[msg.user_id]
                val = u.answers[it.id] * u.reliability
                if val < 0:
                    it.c_n += val
                else:
                    it.c_p += val
            it.weight = get_item_weight(it.c_n, it.c_p)


    def compute_answers(self, k_max):
        # Sends the initial messages from users to items.
        for it in self.items:
            it.msgs = []
        for u in self.users:
            for it_id in u.answers.iterkeys():
                it = self.item_dict[it_id]
                msg = Message_to_item(u.id, u.answers[it_id])
                it.msgs.append(msg)
        # Runs main iterations.
        if DEBUG:
            for it in self.items:
                for msg in it.msgs:
                    print msg
        for i in xrange(k_max):
            if DEBUG:
                print ''
                print 'iteration', i
            self._propagate_from_items()
            if DEBUG:
                for u in self.users:
                    for msg in u.msgs:
                        print msg
            self._propagate_from_users()
            if DEBUG:
                for it in self.items:
                    for msg in it.msgs:
                        print msg
        # Aggregating item information.
        self._aggregate_items()
