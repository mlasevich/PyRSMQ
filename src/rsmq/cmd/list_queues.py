'''

'''

from .base_command import BaseRSMQCommand


class ListQueuesCommand(BaseRSMQCommand):
    '''
    List Queues.

    On execution returns a set of queues already existing on the redis in this namespace
    '''

    PARAMS = {'quiet': {'required': False,
                        'value': False}}

    def exec_command(self):
        ''' Exec Command '''
        client = self.client
        ret = client.smembers(self.queue_set)
        return ret
