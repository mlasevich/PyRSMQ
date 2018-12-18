
from pprint import pprint
import time

from rsmq.rsmq import RedisSMQ


# Create controller.
# In this case we are specifying the host and default queue name
queue = RedisSMQ(host="127.0.0.1", qname="myqueue")


# Delete Queue if it already exists, ignoring exceptions
queue.deleteQueue().exceptions(False).exec()

# Create Queue with default visibility timeout of 20 and delay of 0
# demonstrating here both ways of setting parameters
queue.createQueue(delay=0).vt(20).exec()

# Send a message with a 2 second delay
message_id = queue.sendMessage(delay=2).message("Hello World").exec()

pprint({'queue_status': queue.getQueueAttributes().exec()})

# Try to get a message - this will not succeed, as our message has a delay and no other
# messages are in the queue
msg = queue.receiveMessage().exceptions(False).exec()

# Message should be False as we got no message
pprint({"Message": msg})

print("Waiting for our message to become visible")
# Wait for our message to become visible
time.sleep(2)

pprint({'queue_status': queue.getQueueAttributes().exec()})
# Get our message
msg = queue.receiveMessage().exec()

# Message should now be there
pprint({"Message": msg})

# Delete Message
queue.deleteMessage(id=msg['uid'])

pprint({'queue_status': queue.getQueueAttributes().exec()})
# delete our queue
queue.deleteQueue().exec()

# No action
queue.quit()
