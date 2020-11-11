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
                        'value': None},
              'quiet': {'required': False,
                        'value': False}
              }

    def exec_command(self):
        ''' Exec Command '''
        secs, usecs = self.client.time()
        now = secs * 1000 + int(usecs / 1000)

        queue_base = self.queue_base
        queue_key = self.queue_key

        tx = self.client.pipeline(transaction=True)
        tx.hmget(queue_key, "vt", "delay", "maxsize", "totalrecv", "totalsent", "created",
                 "modified")
        tx.zcard(queue_base)
        tx.zcount(queue_base, now, "+inf")

        results = tx.execute()

        if not results or results[0][0] is None:
            raise QueueDoesNotExist(self.get_qname)

        stats = results[0]

        return {
            "vt": float(stats[0]),
            "delay": float(stats[1]),
            "maxsize": int(stats[2]),
            "totalrecv": int(stats[3] or 0),
            "totalsent": int(stats[4] or 0),
            "created": int(stats[5]),
            "modified": int(stats[6]),
            "msgs": results[1],
            "hiddenmsgs": results[2]
        }
