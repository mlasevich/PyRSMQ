'''

'''

from .base_command import BaseRSMQCommand
from .exceptions import NoMessageInQueue


class PopMessageCommand(BaseRSMQCommand):
    '''
    Receive Message and delete it
    '''

    PARAMS = {'qname': {'required': True,
                        'value': None},
              'quiet': {'required': False,
                        'value': False}
              }

    def exec_command(self):
        ''' Execute '''
        client = self.client

        queue_base = self.queue_base
        queue = self.queue_def()

        ts = int(queue['ts'])
        result = client.evalsha(self.popMessageSha1, 2, queue_base, ts)
        if not result:
            raise NoMessageInQueue(self.get_qname)
        [message_id, message, rc, ts] = result
        return {'id': message_id, 'message': message, 'rc': rc, 'ts': int(ts)}
