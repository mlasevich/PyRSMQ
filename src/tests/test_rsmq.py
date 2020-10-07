'''
Baseline Unit Test
'''
import difflib
import os.path
import pprint
import unittest
from unittest.util import safe_repr

import fakeredis

from rsmq.rsmq import RedisSMQ


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class TestUnitTests(unittest.TestCase):
    ''' Unit Test RedisSMQ'''

    def setUp(self):
        ''' Setup '''

    def assertQueueAttributes(self, expected, actual, msg=None):
        ''' assert queue attributes are set '''
        self.assertIsInstance(
            expected, dict, 'First argument is not a dictionary')
        self.assertIsInstance(
            actual, dict, 'Second argument is not a dictionary')
        actual_short = {key: actual[key] for key in expected.keys()}
        if not expected.items() <= actual.items():
            diff = ('\n' + '\n'.join(difflib.ndiff(
                           pprint.pformat(expected).splitlines(),
                           pprint.pformat(actual_short).splitlines())))
            standardMsg = '%s !<= %s' % (
                safe_repr(expected), safe_repr(actual_short))
            standardMsg = self._truncateMessage(standardMsg, diff)
            msg = self._formatMessage(msg, standardMsg)
            raise AssertionError(msg)

    def test_unittest(self):
        ''' Check Unit Test Framework '''
        unittest_loaded = True
        self.assertTrue(unittest_loaded)

    def test_qname_good_validation(self):
        ''' Test Good QName validation '''
        client = fakeredis.FakeStrictRedis(decode_responses=True)
        client.flushall()
        queue = RedisSMQ(client=client, exceptions=False)
        GOOD_QUEUE_NAMES = ['simple', 'with_underscore', 'with-dash', '-start',
                            'with\x01\x02\x03binary']

        for qname in GOOD_QUEUE_NAMES:
            self.assertTrue(queue.getQueueAttributes().qname(qname).ready())

    def test_qname_bad_validation(self):
        ''' Test bad QName validation '''
        client = fakeredis.FakeStrictRedis(decode_responses=True)
        client.flushall()
        queue = RedisSMQ(client=client, exceptions=False)
        BAD_QUEUE_NAMES = ['', None, 'something:else',
                           ':', 'something:', ':else']

        for qname in BAD_QUEUE_NAMES:
            self.assertFalse(queue.getQueueAttributes().qname(qname).ready())

    def test_create_queue_default(self):
        ''' Test Creating of the Queue '''
        client = fakeredis.FakeStrictRedis(decode_responses=True)
        client.flushall()
        queue = RedisSMQ(client=client)
        queue_name = 'test-queue'
        queue_key = 'rsmq:%s:Q' % queue_name
        queue.createQueue().qname(queue_name).execute()
        keys = client.keys('*')
        self.assertListEqual(sorted([queue_key, 'rsmq:QUEUES']), sorted(keys))
        queues = client.smembers('rsmq:QUEUES')
        self.assertSetEqual(set([queue_name]), queues)
        queue_details = client.hgetall(queue_key)
        self.assertTrue(
            {'vt': '30', 'delay': '0', 'maxsize': '65565'}.items() <= queue_details.items())

    def test_create_queue_custom(self):
        ''' Test Creating of the Queue '''
        client = fakeredis.FakeStrictRedis(decode_responses=True)
        client.flushall()
        queue = RedisSMQ(client=client)
        queue_name = 'test-queue-2'
        queue_key = 'rsmq:%s:Q' % queue_name
        queue.createQueue(qname=queue_name, vt=15).delay(10).execute()
        keys = client.keys('*')
        self.assertListEqual(sorted([queue_key, 'rsmq:QUEUES']), sorted(keys))
        queues = client.smembers('rsmq:QUEUES')
        self.assertSetEqual(set([queue_name]), queues)
        queue_details = client.hgetall(queue_key)

        self.assertTrue(
            {'vt': '15', 'delay': '10', 'maxsize': '65565'}.items() <= queue_details.items())

    def test_delete_queue(self):
        ''' Test Deleting of the Queue '''
        client = fakeredis.FakeStrictRedis(decode_responses=True)
        client.flushall()
        queue = RedisSMQ(client=client)
        queue_name = 'test-queue-delete'
        queue_key = 'rsmq:%s:Q' % queue_name
        queue.createQueue().qname(queue_name).execute()
        keys = client.keys('*')
        self.assertListEqual(sorted([queue_key, 'rsmq:QUEUES']), sorted(keys))
        queues = client.smembers('rsmq:QUEUES')
        self.assertSetEqual(set([queue_name]), queues)
        queue_details = client.hgetall(queue_key)
        self.assertTrue(
            {'vt': '30', 'delay': '0', 'maxsize': '65565'}.items() <= queue_details.items())
        result = queue.deleteQueue(qname=queue_name).execute()
        self.assertEqual(result, True)
        queue_details = client.hgetall(queue_key)
        self.assertEqual(queue_details, {})

    def test_queue_attributes(self):
        ''' Test Getting/Setting of the Queue Attribues'''
        client = fakeredis.FakeStrictRedis(decode_responses=True)
        client.flushall()
        queue_name = 'test-queue-attr'
        queue = RedisSMQ(client=client, qname=queue_name)
        queue_key = 'rsmq:%s:Q' % queue_name
        queue.createQueue(vt=15, delay=10).execute()
        keys = client.keys('*')
        self.assertListEqual(sorted([queue_key, 'rsmq:QUEUES']), sorted(keys))
        queues = client.smembers('rsmq:QUEUES')
        self.assertSetEqual(set([queue_name]), queues)
        queue_details = client.hgetall(queue_key)
        self.assertQueueAttributes(
            {'vt': '15', 'delay': '10', 'maxsize': '65565'}, queue_details)
        attributes = queue.getQueueAttributes(qname=queue_name).execute()
        self.assertQueueAttributes({'vt': 15,
                                    'delay': 10,
                                    'maxsize': 65565,
                                    'totalrecv': 0,
                                    'totalsent': 0,
                                    'msgs': 0,
                                    'hiddenmsgs': 0}, attributes)
        attributes_1 = queue.setQueueAttributes(
            vt=30, maxsize=1024, delay=1).execute()
        attributes = queue.getQueueAttributes(qname=queue_name).execute()
        self.assertDictEqual(attributes, attributes_1)
        self.assertQueueAttributes({'vt': 30,
                                    'delay': 1,
                                    'maxsize': 1024,
                                    'totalrecv': 0,
                                    'totalsent': 0,
                                    'msgs': 0,
                                    'hiddenmsgs': 0}, attributes)

    def test_invalid_queue_attributes(self):
        ''' Test Getting/Setting of the Queue Attribues'''
        client = fakeredis.FakeStrictRedis(decode_responses=True)
        client.flushall()
        queue_name = 'test-queue-attr'
        queue = RedisSMQ(client=client, qname=queue_name)
        queue_key = 'rsmq:%s:Q' % queue_name
        queue.createQueue(vt=15, delay=10).execute()
        keys = client.keys('*')
        self.assertListEqual(sorted([queue_key, 'rsmq:QUEUES']), sorted(keys))
        queues = client.smembers('rsmq:QUEUES')
        self.assertSetEqual(set([queue_name]), queues)
        queue_details = client.hgetall(queue_key)
        self.assertQueueAttributes(
            {'vt': '15', 'delay': '10', 'maxsize': '65565'}, queue_details)
        attributes = queue.getQueueAttributes(qname=queue_name).execute()
        self.assertQueueAttributes({'vt': 15,
                                    'delay': 10,
                                    'maxsize': 65565,
                                    'totalrecv': 0,
                                    'totalsent': 0,
                                    'msgs': 0,
                                    'hiddenmsgs': 0}, attributes)
        attributes_1 = queue.setQueueAttributes(
            vt=-3, maxsize=-2, delay=-1).execute()
        attributes = queue.getQueueAttributes(qname=queue_name).execute()
        self.assertDictEqual(attributes, attributes_1)
        self.assertQueueAttributes({'vt': 15,
                                    'delay': 10,
                                    'maxsize': 65565,
                                    'totalrecv': 0,
                                    'totalsent': 0,
                                    'msgs': 0,
                                    'hiddenmsgs': 0}, attributes)


if __name__ == '__main__':
    unittest.main()
