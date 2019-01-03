'''

'''
import time

from .. import const
from .base_command import BaseRSMQCommand
from .exceptions import QueueAlreadyExists


class CreateQueueCommand(BaseRSMQCommand):
    '''
    Create Queue if does not exist
    '''

    PARAMS = {'qname': {'required': True,
                        'value': None},
              'vt': {'required': True,
                     'value': const.VT_DEFAULT},
              'delay': {'required': True,
                        'value': const.DELAY_DEFAULT},
              'maxsize': {'required': True,
                          'value': const.MAXSIZE_DEFAULT},
              'quiet': {'required': False,
                        'value': False}
              }

    def exec_command(self):
        ''' Exec Command '''
        client = self.client
        now = int(time.time())

        key = self.queue_key
        tx = client.pipeline(transaction=True)
        tx.hsetnx(key, "vt", self.get_vt)
        tx.hsetnx(key, "delay", self.get_delay)
        tx.hsetnx(key, "maxsize", self.get_maxsize)
        tx.hsetnx(key, "created", now)
        tx.hsetnx(key, "modified", now)
        results = tx.execute()
        if True not in results:
            raise QueueAlreadyExists(self.get_qname)
        client.sadd(self.queue_set, self.get_qname)
        return True
