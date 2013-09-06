KARGER_THRESHOLD_SPAM = -1
KARGER_THRESHOLD_HAM = 5
DIRICHLET_THRESHOLD_SPAM = -0.001
DIRICHLET_THRESHOLD_HAM = 0.03
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
