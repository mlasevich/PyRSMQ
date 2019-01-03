'''
Delete Queue Command
'''

from .base_command import BaseRSMQCommand
from .exceptions import QueueDoesNotExist


class DeleteQueueCommand(BaseRSMQCommand):
    '''
    Delete Queue if it exists
    '''

    PARAMS = {'qname': {'required': True,
                        'value': None},
              'quiet': {'required': False,
                        'value': False}
              }

    def exec_command(self):
        ''' Exec Command '''
        client = self.client

        queue_name = self.queue_base
        queue_key = self.queue_key
        tx = client.pipeline(transaction=True)
        tx.delete(queue_key)
        tx.delete(queue_name)
        tx.srem(self.queue_set, self.get_qname)
        results = tx.execute()
        if True not in results:
            raise QueueDoesNotExist(self.get_qname)
        self.log.debug("Deleted Queue %s", self.queue_base)
        return True
