![RSMQ: Redis Simple Message Queue for Node.js](https://img.webmart.de/rsmq_wide.png)

[![Build Status](https://travis-ci.org/mlasevich/PyRSMQ.svg?branch=master)](https://travis-ci.org/mlasevich/PyRSMQ)
[![Coverage Status](https://coveralls.io/repos/github/mlasevich/PyRSMQ/badge.svg?branch=master)](https://coveralls.io/github/mlasevich/PyRSMQ?branch=master)

# Redis Simple Message Queue

A lightweight message queue for Python that requires no dedicated queue server. Just a Redis server.

Python implementation of https://github.com/smrchy/rsmq.


## PyRSMQ Release Notes

* 0.1.0 - initial version
    * Initial port
    * Missing "Realtime" mode
    * Missing unit tests

## Quick Intro to RSMQ

RSMQ is trying to emulate Amazon's SQS-like functionality, where there is a named queue (name 
consists of "namespace" and "qname") that is backed by Redis. Queue must be created before used. 
Once created, _Producers_ will place messages in queue and _Consumers_ will retrieve them. 
Messages have a property of "visibility" - where any "visible" message may be consumed, but 
"invisbile" messages stay in the queue until they become visible or deleted.

Once queue exists, a _Producer_ can push messages into it. When pushing to queue, message gets a
unique ID that is used to track the message. The ID can be used to delete message by _Producer_ or
_Consumer_ or to control its "visibility"

During insertion, a message may have a `delay` associated with it. "Delay" will mark message 
"invisible" for specified delay duration, and thus prevent it from being consumed. Delay may be 
specified at time of message creation or, if not specified, default value set in queue attributes
is used.

_Consumer_ will retrieve next message in queue via either `receiveMessage()` or `popMessage()` 
command. If we do not care about reliability of the message beyond delivery, a good and simple way
to retrieve it is via `popMessage()`.  When using `popMessage()` the message is automatically
deleted at the same time it is received.

However in many cases we want to ensure that the message is not only received, but is also
processed before being deleted. For this, `receiveMessage()` is best. When using `receiveMessage()`,
the message is kept in the queue, but is marked "invisible" for some amount of time. The amount of 
time is specified by queue attribute `vt`(visibility timeout), which may also be overridden by 
specifying a custom `vt` value in `receiveMessage()` call. When using  `receiveMessage()`, 
_Consumer_' is responsible for deleting the message before `vt` timeout occurs, otherwise the
message may be picked up by another _Consumer_. _Consumer_ can also extend the timeout if it needs
more time, or clear the timeout if processing failed.

A "Realtime" mode can be specified when using the RSMQ queue. "Realtime" mode adds a Redis PUBSUB
based notification that would allow _Consumers_ to be notified whenever a new message is added to 
the queue. This can remove the need for _Consumer_ to constantly poll the queue when it is empty
(*NOTE:* as of this writing, "Realtime" is not yet implemented in python version)

## Python Implementation Notes

This version is heavily based on Java version (https://github.com/igr/jrsmq), which in turn is based on 
the original Node.JS version.

### API
To start with, best effort is made to maintain same method/parameter/usablity named of both version
(which, admittedly, resulted in a not very pythonic API)

Although much of the original API is still present, some alternatives are added to make life a bit 
easier.

For example, while you can set any available parameter to command using the "setter" method, you can 
also simply specify the parameters when creating the command. So these two commands do same thing:

    rqsm.createQueue().qname("my-queue").vt(20).exec()

    rqsm.createQueue(qname="my-queue", vt=20).exec()

In addition, when creating a main controller, any non-controller parameters specified will become 
defaults for all commands created via this controller - so, for example, you if you plan to work with
only one queue using this controller, you can specify the qname parameter during creation of the controller
and not need to specify it in every command.

### General Usage Approach

As copied from other versions, the general approach is to create a controller object and use that
object to create, configure and then execute commands

### Error Handling

Commands follow the pattern of other versions and throw exceptions on error. 

Exceptions are all extending `RedisSMQException()` and include:

* `InvalidParameterValue()` - Invalid Parameter specified
* `QueueAlreadyExists()` - attempt to create queue which already exists
* `QueueDoesNotExist()` - attempt to use/delete queue that does not exist
* `NoMessageInQueue()` - attempt to retrieve message from queue that has no visible messaged

However, if you do not wish to use exceptions, you can turn them off on per-command or 
per-controller basis by using `.exceptions(False)` on the relevant object. For example, the
following will create Queue only if it does not exist without throwing an exception:

    rsmq.createQueue().exceptions(False).exec()


## Usage

### Example Usage

In this example we will create a new queue named "my-queue", deleting previous version, if one
exists, and then send a message with a 2 second delay. We will then demonstrate both the lack of
message before delay expires and getting the message after timeout


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
    queue.deleteMessage(id=msg['id'])
    
    pprint({'queue_status': queue.getQueueAttributes().exec()})
    # delete our queue
    queue.deleteQueue().exec()
    
    # No action
    queue.quit()


    
### RedisSMQ Controller API Usage

Usage: `rsmq.rqsm.RedisSMQ([options])`

* Options (all options are provided as keyword options):
    * Redis Connection arguments:
        * `client` - provide an existing, configured redis client
        or
        * `host` - redis hostname (Default: `127.0.0.1`)
        * `port` - redis port (Default: `6379`)
        * `options` - additional redis client options. Defaults:
            * `encoding`: `utf-8`
            * `decode_responses`: `True`
    * Controller Options
        * `ns` - namespace - all redis keys are prepended with `<ns>:`. Default: `rsmq`
        * `realtime` - if set to True, enables realtime option. Default: `False`
        * `exceptions` - if set to True, throw exceptions for all commands. Default: `True`
    * Default Command Options. Anything else is passed to each command as defaults. Examples:
        * `qname` - default Queue Name

#### Controller Methods

* `exceptions(True/False` - enable/disable exceptions
* `setClient(client)` - specify new redis client object
* `ns(namespace)` - set new namespace
* `quit()` - disconnect from redis. This is mainly for compatibility with other versions. Does not do much

#### Controller Commands

* `createQueue()` - Create new queue
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `vt` - default visibility timeout in seconds. Default: `30`
        * `delay` - default delay (visibility timeout on insert). Default: `0`
        * `maxsize` - maximum message size (1024-65535, Default: 65535)
    * **Returns**:
        * `True` if queue was created

* `deleteQueue()` - Delete Existing queue
   * Parameters:
        * `qname` - (Required) name of the queue
    * **Returns**:
        * `True` if queue was deleted

* `setQueueAttributes()` - Update queue attributes. If value is not specified, it is not updated.
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `vt` - default visibility timeout in seconds. Default: `30`
        * `delay` - default delay (visibility timeout on insert). Default: `0`
        * `maxsize` - maximum message size (1024-65535, Default: 65535)
    * **Returns**:
        * output of `getQueueAttributes()` call

* `getQueueAttributes()` - Get Queue Attributes and statistics
   * Parameters:
        * `qname` - (Required) name of the queue
    * **Returns** a dictionary with following fields:
        * `vt` -  default visibility timeout
        * `delay` - default insertion delay
        * `maxsize` -  max size of the message
        * `totalrecv` - number of messages consumed. Note, this is incremented each time message is retrieved, so if it was not deleted and made visible again, it will show up here multiple times.
        * `totalsent` - number of messages sent to queue.
        * `created` -  unix timestamp (seconds since epoch) of when the queue was created
        * `modified` -  unix timestamp (seconds since epoch) of when the queue was last updated
        * `msgs` -  Total number of messages currently in the queue
        * `hiddenmsgs` - Number of messages in queue that are not visible

* `listQueues()` - List all queues in this namespace
    * **Parameters:**
    * **Returns**:
        * All queue names in this namespace as a `set()`

* `changeMessageVisibility()` - Change Message Visibility
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `id` - (Required) message id
        * ???
    * **Returns**:
        * ???

* `sendMessage()` - Send message into queue
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `message` - (Required) message id
        * `delay` - Optional override of the `delay` for this message (If not specified, default for queue is used)
    * **Returns**:
        * message id of the sent message

* `receiveMessage()` - Receive Message from queue and mark it invisible
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `vt` - Optional override for visibility timeout for this message (If not specified, default for queue is used)
    * **Returns** dictionary for following fields:
        * `uid` - message id
        * `message` - message content
        * `rc` - receive count - how many times this message was received
        * `ts` - unix timestamp of when the message was originally sent

* `popMessage()` -  Receive Message from queue and delete it from queue
    * **Parameters:**
        * `qname` - (Required) name of the queue
    * **Returns** dictionary for following fields:
        * `uid` - message id
        * `message` - message content
        * `rc` - receive count - how many times this message was received
        * `ts` - unix timestamp of when the message was originally sent

* `deleteMessage()` -  Delete Message from queue
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `id` - (Required) message id
    * **Returns**:
        * `True` if message was deleted
