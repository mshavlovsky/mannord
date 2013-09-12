import collections
import numpy as np
from models import (ActionMixin, UserMixin, ItemMixin)
import hits

K_MAX = 10

def suggest_n_users_to_review(item, n, session):
    """ Function suggests n users to review targer item."""
    ItemClass = ItemMixin.cls
    ActionClass = ActionMixin.cls
    UserClass = UserMixin.cls
    graph = hits.Graph()
    # Fetches all annotations (items) on the target page
    # annotations.
    users_1, links_1 = get_1neighbors_and_links(item.page_url, session)
    add_links_to_graph(graph, item.page_url, links_1)
    # Adds links for 2-heighbors
    for user_id in users_1:
        pages = get_1neighbors_for_user(user_id, session)
        for p in pages:
            users, links = get_1neighbors_and_links(p, session)
            add_links_to_graph(graph, p, links)
    # Runns hits algorithm
    graph.hubs_and_authorities(K_MAX)
    return graph.get_n_top_users(n, item.author_id)


def add_links_to_graph(graph, page_url, links):
    for user_id in links:
        graph.add_link(user_id, page_url, links[user_id])


def get_1neighbors_for_user(user_id, session):
    """ The method returns a list of pages wich author annotated and
    pages with annotation which the user acted on (voted, flagged, etc.).
    """
    ItemClass = ItemMixin.cls
    ActionClass = ActionMixin.cls
    set_of_pages = set()
    # Fetches items.
    items = ItemClass.get_items_by_author(user_id, session)
    for it in items:
        set_of_pages.add(it.page_url)
    actions = ActionClass.get_actions_by_user(user_id, session)
    for act in actions:
        if act.item_twin is None:
            set_of_pages.add(act.item.page_url)
    return list(set_of_pages)


def get_1neighbors_and_links(page_url, session):
    """ The method returns a list of users who annotated the page or who acted
    on these annotations.
    The method, also, returns a dictionary with links, the dictionary maps
    user id to a number of times the user acted on the page (weight).
    """
    ItemClass = ItemMixin.cls
    ActionClass = ActionMixin.cls
    # A dictionary is initialized with zeros, it is convenient for counting.
    counter_dict = collections.defaultdict(int)
    # Fetches items
    items = ItemClass.get_items_on_page(page_url, session)
    for it in items:
        counter_dict[it.author_id] += 1
    # Fetches actions
    for it in items:
        # Get actions on the item it.
        actions = ActionClass.get_actions_on_item(it.id, session)
        for act in actions:
            # We care only about actions which are not annotations itself,
            # because actions which are annotations were already counted.
            if act.item_twin is None:
                counter_dict[act.user_id] += 1
    return counter_dict.keys(), counter_dict
