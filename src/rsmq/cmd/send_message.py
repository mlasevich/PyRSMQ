'''

'''

from .base_command import BaseRSMQCommand
from .utils import make_message_id, encode_message


class SendMessageCommand(BaseRSMQCommand):
    '''
    Create Queue if does not exist
    '''

    PARAMS = {'qname': {'required': True,
                        'value': None},
              'message': {'required': True,
                          'value': None},
              'delay': {'required': False,
                        'value': None},
              'quiet': {'required': False,
                        'value': False},
              'encode': {'required': False,
                         'value': False}
              }

    def exec_command(self):
        ''' 
        Execute command

        @raise QueueDoesNotExist if queue does not exist
        '''
        queue = self.queue_def()
        message_id = make_message_id(queue.get('ts_usec', None))

        queue_key = self.queue_key
        queue_base = self.queue_base

        ts = int(queue['ts'])

        delay = self.get_delay
        if delay is None:
            delay = queue.get('delay', 0)
        delay = float(delay or 0)

        message = self.get_message
        if self.get_encode or not isinstance(message, (str, bytes)):
            message = encode_message(message)
            self.log.debug("Encoded message: %s", message)

        tx = self.client.pipeline(transaction=True)
        timestamp = ts + int(round(delay * 1000))
        self.log.debug("tx.zadd(%s, %s, %s)",
                       queue_base, timestamp, message_id)
        tx.zadd(queue_base, {message_id: timestamp})

        tx.hset(queue_key, message_id, message)
        tx.hincrby(queue_key, "totalsent", 1)
        _results = tx.execute()

        return message_id
