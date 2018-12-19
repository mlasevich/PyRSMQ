'''

'''

#import random
import uuid

from .base_command import BaseRSMQCommand


class SendMessageCommand(BaseRSMQCommand):
    '''
    Create Queue if does not exist
    '''

    PARAMS = {'qname': {'required': True,
                        'value': None},
              'message': {'required': True,
                          'value': None},
              'delay': {'required': False,
                        'value': None}
              }

    def _make_message_id(self):
        ''' generate a message id for message '''
        return uuid.uuid4().hex

    def exec_command(self):
        ''' Execute '''
        queue = self.queue_def()
        message_id = self._make_message_id()

        queue_key = self.queue_key
        queue_base = self.queue_base

        ts = int(queue['ts'])

        delay = self.get_delay
        if delay is None:
            delay = queue.get('delay', 0)
        delay = int(delay or 0)

        tx = self.client.pipeline(transaction=True)
        timestamp = ts + delay * 1000
        self.log.debug("tx.zadd(%s, %s, %s)",
                       queue_base, timestamp, message_id)
        tx.zadd(queue_base, {message_id: timestamp})
        tx.hset(queue_key, message_id, self.get_message)
        tx.hincrby(queue_key, "totalsent", 1)
        _results = tx.execute()

        return message_id
