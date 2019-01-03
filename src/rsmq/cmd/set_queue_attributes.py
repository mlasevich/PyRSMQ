'''

'''
import time
from .base_command import BaseRSMQCommand


class SetQueueAttributesCommand(BaseRSMQCommand):
    '''
    Get Queue Attributes if does not exist
    '''

    PARAMS = {'qname': {'required': True,
                        'value': None},
              'vt': {'required': False,
                     'value': None},
              'delay': {'required': False,
                        'value': None},
              'maxsize': {'required': False,
                          'value': None},
              'quiet': {'required': False,
                        'value': False}
              }

    def exec_command(self):
        ''' Exec Command '''
        now = int(time.time())

        queue_key = self.queue_key

        tx = self.client.pipeline(transaction=True)
        for param in ['vt', 'delay', 'maxsize']:
            value = self.param_get(param, default_value=None)
            if value is not None:
                tx.hset(queue_key, param, value)
        if tx:
            self.log.debug("Applying queue attribute changes")
            tx.hset(queue_key, "modified", now)
        else:
            self.log.debug("No queue attribute changes")
        _result = tx.execute()

        return self.parent.getQueueAttributes().qname(self.get_qname).execute()
