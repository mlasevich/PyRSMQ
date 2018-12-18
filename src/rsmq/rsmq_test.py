'''
Baseline Unit Test
'''
import os.path
import unittest

import fakeredis

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class TestUnitTests(unittest.TestCase):
    ''' Unit Test RedisSMQ'''

    def setUp(self):
        ''' Setup '''

    def test_unittest(self):
        ''' Check Unit Test Framework '''
        unittest_loaded = True
        self.assertTrue(unittest_loaded)

    def 

if __name__ == '__main__':
    unittest.main()
