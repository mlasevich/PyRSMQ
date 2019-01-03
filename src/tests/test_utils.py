'''
Unit Tests for utils
'''
import logging
import os
import unittest

from rsmq.cmd import utils


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


ENCODE_TESTS = {
    'a': 'a',
    '{"a": "b"}': {'a': 'b'}
}

# Each test is value, min, max, sucess
VALIDATE_INT_TESTS = [
    (0, 0, 100, True),
    (1, 0, 100, True),
    (1, 0, 1, True),
    (-1, -100, 0, True),
    (0, -100, 0, True),
    (1, -100, 0, False),
    (1, 0, 1, True),
    (0, 1, 2, False),
]

# Base charsets
BASE_10 = '0123456789'
BASE_16 = '0123456789ABCDEF'
BASE_36 = '0123456789abcdefghijklmnopqrstuvwxyz'

# Each test is (raw, encoded, base_charset)
BASE_X_ENCODED_TESTS = [
    (10000, "10000", BASE_10),
    (10000, "2710", BASE_16),
    (10000, "7ps", BASE_36),
    (10000000, "5yc1s", BASE_36),
]


class MockLogger(object):

    def __init__(self):
        self.last_level = None
        self.last_msg = None

    def reset(self):
        self.last_level = None
        self.last_msg = None

    def log(self, level, msg, *params):
        self.last_level = level
        self.last_msg = msg % params

    def debug(self, msg, *params):
        self.log(logging.DEBUG, msg, *params)

    def info(self, msg, *params):
        self.log(logging.INFO, msg, *params)


class CmdUtilsUnitTests(unittest.TestCase):
    ''' Unit Tests for utils'''

    def setUp(self):
        ''' Setup '''

    def test_encode_object(self):
        ''' Check Encode Message '''
        for string, obj in ENCODE_TESTS.items():
            self.assertEqual(string, utils.encode_message(obj))

    def test_encode_string(self):
        ''' Check Encode String Message '''
        for string, _obj in ENCODE_TESTS.items():
            self.assertEqual(string, utils.encode_message(string))

    def test_decode_object(self):
        ''' Check Decode Message Object '''
        for _string, obj in ENCODE_TESTS.items():
            self.assertEqual(obj, utils.decode_message(obj))

    def test_decode_string(self):
        ''' Check Decode Message String '''
        for string, obj in ENCODE_TESTS.items():
            self.assertEqual(obj, utils.decode_message(string))

    def test_validate_int(self):
        ''' Test validate_int '''
        for value, min_value, max_value, expected in VALIDATE_INT_TESTS:
            self.assertEqual(expected, utils.validate_int(
                value, min_value, max_value))

    def test_validate_int_invalid(self):
        ''' Test validate_int '''
        self.assertFalse(utils.validate_int(None, 0, 100))
        self.assertFalse(utils.validate_int("A", 0, 100))

    def test_validate_int_logging_none(self):
        ''' Test validate_int '''
        logger = MockLogger()
        self.assertFalse(utils.validate_int(None, 0, 100, logger, "testname"))
        self.assertEqual("testname value is not set", logger.last_msg)

    def test_validate_int_logging_too_low(self):
        ''' Test validate_int '''
        logger = MockLogger()
        self.assertFalse(utils.validate_int(-1, 0, 100, logger, "testname"))
        self.assertEqual(
            "testname value -1 is less than minimum (0)", logger.last_msg)

    def test_validate_int_logging_too_high(self):
        ''' Test validate_int '''
        logger = MockLogger()
        self.assertFalse(utils.validate_int(101, 0, 100, logger, "testname"))
        self.assertEqual("testname value 101 is greater than maximum (100)",
                         logger.last_msg)

    def test_validate_int_logging_invalid(self):
        ''' Test validate_int '''
        logger = MockLogger()
        self.assertFalse(utils.validate_int("A", 0, 100, logger, "testname"))
        self.assertEqual(
            "testname value (A) is not an integer", logger.last_msg)

    def test_random_string(self):
        ''' Test random_string '''
        charset_default = set(utils.DEFAULT_CHARSET)
        charset1 = "abcdefgh"
        charset1_set = set(charset1)

        for i in range(32):
            for _ in range(10):
                rstr = utils.random_string(i, charset1)
                self.assertEqual(
                    i, len(rstr), "Expected length is %s, got %s" % (i, len(rstr)))
                self.assertLessEqual(
                    set(rstr), charset1_set, "Expected all characters to be in set")
            for _ in range(10):
                rstr = utils.random_string(i)
                self.assertEqual(
                    i, len(rstr), "Expected length is %s, got %s" % (i, len(rstr)))
                self.assertLessEqual(
                    set(rstr), charset_default, "Expected all characters to be in set")

    def test_make_message_id(self):
        ''' Test make_message_id '''
        for _ in range(32):
            mid = utils.make_message_id(10000000)
            # length is always 22 plus encoded value of 10000000 = which is
            self.assertEqual(27, len(mid))

    def test_baseXencode(self):
        ''' Test baseXencode '''
        for (raw, encoded, charset) in BASE_X_ENCODED_TESTS:
            self.assertEqual(encoded, utils.baseXencode(
                raw, charset), "Invalid encoded value for base %s" % len(charset))


if __name__ == '__main__':
    unittest.main()
