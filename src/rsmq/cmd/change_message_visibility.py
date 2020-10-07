'''

'''

from .base_command import BaseRSMQCommand
from .exceptions import NoMessageInQueue


class ChangeMessageVisibilityCommand(BaseRSMQCommand):
    '''
    Change Message Visibility Timeout Command
    '''

    PARAMS = {'qname': {'required': True,
                        'value': None},
              'id': {'required': True,
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
            self.changeMessageVisibilitySha1, 3, queue_base, self.get_id, vtimeout)
        if not result:
            raise NoMessageInQueue(self.get_qname)
        return result == 1
