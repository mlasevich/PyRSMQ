'''
Baseline Unit Test
'''
import os.path
import unittest

import fakeredis

from .rsmq import RedisSMQ

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class TestUnitTests(unittest.TestCase):
    ''' Unit Test RedisSMQ'''

    def setUp(self):
        ''' Setup '''

    def test_unittest(self):
        ''' Check Unit Test Framework '''
        unittest_loaded = True
        self.assertTrue(unittest_loaded)

    def test_create_queue(self):
        ''' Test Creating of the Queue '''
        client = fakeredis.FakeStrictRedis()
        queue = RedisSMQ(client=client)
        queue.createQueue().qname('test-queue').exec()


if __name__ == '__main__':
    unittest.main()
