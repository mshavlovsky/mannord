# Classic hits algorithm.
import numpy as np



class Item(object):
    def __init__(self, item_id):
        self.id = item_id
        self.auth_weight = 1
        self.links = {}

    def __repr__(self):
        return "<Item %s, auth_weight %s>" % (self.id, self.auth_weight)


class User(object):
    def __init__(self, user_id):
        self.id = user_id
        self.hub_weight = 1
        self.links = {}

    def __repr__(self):
        return "<User %s, hub_weight %s>" % (self.id, self.hub_weight)


class Graph(object):

    def __init__(self):
        self.items = []
        self.users = []
        self.item_dict = {}
        self.user_dict = {}


    def __repr__(self):
        s = "Graph\n"
        for it in self.items:
            s = "%s %s\n" % (s, it)
        for u in self.users:
            s = "%s %s\n" % (s, u)
        return s


    def add_link(self, user_id, item_id, value):
        it = self.item_dict.get(item_id)
        if not it:
            it = Item(item_id)
            self.items.append(it)
            self.item_dict[item_id] = it
        u = self.user_dict.get(user_id)
        if not u:
            u = User(user_id)
            self.users.append(u)
            self.user_dict[user_id] = u
        it.links[user_id] = value
        u.links[item_id] = value


    def get_item(self, item_id):
        return self.item_dict.get(item_id)


    def get_user(self, user_id):
        return self.user_dict.get(user_id)


    def hubs_and_authorities(self, k_max):
        # Users are hubs and pages are authorities.
        for i in xrange(k_max):
            # Computes authority for all pages.
            norm = 0
            for it in self.items:
                it.auth_weight = 0
                for u_id in it.links:
                    u = self.get_user(u_id)
                    it.auth_weight += it.links[u_id] * u.hub_weight
                norm += it.auth_weight ** 2
            norm = norm ** 0.5
            for it in self.items:
                it.auth_weight /= norm
            # Computes hub weight for all users.
            norm = 0
            for u in self.users:
                u.hub_weight = 0
                for item_id in u.links:
                    it = self.get_item(item_id)
                    u.hub_weight += u.links[item_id] * it.auth_weight
                    norm += u.links[item_id] * it.auth_weight
            norm = norm ** 0.5
            for u in self.users:
                u.hub_weight /= norm


    def get_n_top_users(self, n, author_id):
        """ Returns top n users exclusive the author."""
        l = [(user.hub_weight, user.id) for user in self.users if user.id != author_id]
        # Sorting tuples from largest to smalles based on the first number.
        l.sort(reverse=True)
        n_users = [l[i][1] for i in xrange(min(n, len(l)))]
        return n_users


    def get_n_top_items(self, n):
        l = [(item.auth_weight, item.id) for item in self.items]
        l.sort(reverse=True)
        n_items = [l[i][1] for i in xrange(min(n, len(l)))]
        return n_items
