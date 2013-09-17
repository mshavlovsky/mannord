import os
import ConfigParser
from pkg_resources import resource_string, resource_filename


# Reads config file
file_path_config = resource_filename(__name__, 'mannord.conf')
ini_config = ConfigParser.ConfigParser()
ini_config.readfp(open(file_path_config))

KARGER_THRESHOLD_SPAM = ini_config.get('constants','KARGER_THRESHOLD_SPAM')
KARGER_THRESHOLD_HAM = ini_config.get('constants','KARGER_THRESHOLD_HAM')
DIRICHLET_THRESHOLD_SPAM = ini_config.get('constants','DIRICHLET_THRESHOLD_SPAM')
DIRICHLET_THRESHOLD_HAM = ini_config.get('constants','DIRICHLET_THRESHOLD_HAM')
ALGO_KARGER = 'karger'
ALGO_DIRICHLET = 'dirichlet'


def mark_spam_ham_or_mm(item, algo_type=ALGO_KARGER):
    if algo_type == ALGO_KARGER:
        item.is_spam = False
        item.is_ham = False
        item.marked_for_mm = False
        if item.sk_weight < KARGER_THRESHOLD_SPAM:
            item.is_spam = True
        elif item.sk_weight > KARGER_THRESHOLD_HAM:
            item.is_ham = True
        else:
            # If we don't know whether the annotation is spam or ham,
            # then mark it for metamoderation.
            item.marked_for_mm = True
    elif algo_type == ALGO_DIRICHLET:
        item.is_spam = False
        item.is_ham = False
        item.marked_for_mm = False
        if item.sd_weight < DIRICHLET_THRESHOLD_SPAM:
            item.is_spam = True
        elif item.sd_weight > DIRICHLET_THRESHOLD_HAM:
            item.is_ham = True
        else:
            item.marked_for_mm = True
    else:
        raise Exception("Unknown type of algorithm!")
