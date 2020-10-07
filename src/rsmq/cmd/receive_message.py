'''

'''

from .base_command import BaseRSMQCommand
from .exceptions import NoMessageInQueue


class ReceiveMessageCommand(BaseRSMQCommand):
    '''
    Receive Message
    '''

    PARAMS = {'qname': {'required': True,
                        'value': None},
              'vt': {'required': False,
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
        vt = float(queue['vt'] if self.get_vt is None else self.get_vt)
        vtimeout = ts + int(round(vt * 1000))
        result = client.evalsha(
            self.receiveMessageSha1, 3, queue_base, ts, vtimeout)
        if not result:
            raise NoMessageInQueue(self.get_qname)
        [message_id, message, rc, ts] = result
        return {'id': message_id, 'message': message, 'rc': rc, 'ts': int(ts)}
