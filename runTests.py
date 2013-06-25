#!/usr/bin/python

from mannord_api import *
from datetime import datetime
import unittest


class TestSpamFlag(unittest.TestCase):

    def test_flag(self):
        engine = create_engine('sqlite:///:memory:')
        Session = sessionmaker()
        bind_engine(engine, Session, Base)
        add_user('user_1')
        add_user('user_2')
        add_user('user_3')
        add_annotation('annot_1', 'user_1')
        # First spam flag.
        flag_as_spam('annot_1', 'user_2', datetime.utcnow())
        annot1_score = get_annotation_score('annot_1')
        self.assertTrue(annot1_score == THRESHOLD_SCORE_SPAM)
        is_spam = is_annotation_spam('annot_1')
        self.assertTrue(is_spam == False)
        # Second spam flag.
        flag_as_spam('annot_1', 'user_3', datetime.utcnow())
        is_spam = is_annotation_spam('annot_1')
        self.assertTrue(is_spam == True)
        is_spammer = is_user_spammer('user_1')
        # Adding second annotatio by the same aythor.
        # Now only one vote is enough for marking annotation as a spam
        add_annotation('annot_2', 'user_1')
        is_spam = is_annotation_spam('annot_2')
        self.assertTrue(is_spam == False)
        flag_as_spam('annot_2', 'user_2', datetime.utcnow())
        is_spam = is_annotation_spam('annot_2')
        self.assertTrue(is_spam == True)


if __name__ == '__main__':
    unittest.main()
