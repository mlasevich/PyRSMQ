'''
GetQueueAttributes Command
'''

import time

from .base_command import BaseRSMQCommand
from .exceptions import QueueDoesNotExist


class GetQueueAttributesCommand(BaseRSMQCommand):
    '''
    Get Queue Attributes from existing queue
    '''

    PARAMS = {'qname': {'required': True,
                        'value': None}
              }

    def exec_command(self):
        ''' Exec Command '''
        now = int(time.time())

        queue_base = self.queue_base
        queue_key = self.queue_key

        tx = self.client.pipeline(transaction=True)
        tx.hmget(queue_key, "vt", "delay", "maxsize", "totalrecv", "totalsent", "created",
                 "modified")
        tx.zcard(queue_base)
        tx.zcount(queue_base, "%s000" % now, "+inf")

        results = tx.execute()

        if not results or results[0][0] is None:
            raise QueueDoesNotExist(self.get_qname)

        stats = results[0]

        return {
            "vt": stats[0],
            "delay": stats[1],
            "maxsize": stats[2],
            "totalrecv": stats[3] or 0,
            "totalsent": stats[4] or 0,
            "created": stats[5],
            "modified": stats[6],
            "msgs": results[1],
            "hiddenmsgs": results[2]
        }
