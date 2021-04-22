![RSMQ: Redis Simple Message Queue for Node.js](https://img.webmart.de/rsmq_wide.png)

[![Build Status](https://travis-ci.org/mlasevich/PyRSMQ.svg?branch=master)](https://travis-ci.org/mlasevich/PyRSMQ)
[![Coverage Status](https://coveralls.io/repos/github/mlasevich/PyRSMQ/badge.svg?branch=master)](https://coveralls.io/github/mlasevich/PyRSMQ?branch=master)
[![PyPI version](https://badge.fury.io/py/PyRSMQ.svg)](https://badge.fury.io/py/PyRSMQ)

# Redis Simple Message Queue

A lightweight message queue for Python that requires no dedicated queue server. Just a Redis server.

This is a Python implementation of [https://github.com/smrchy/rsmq](https://github.com/smrchy/rsmq))


## PyRSMQ Release Notes
* 0.4.5
  * Re-release to push to PyPi

* 0.4.4
  * Allow extending the transaction for deleteMessage to perform other actions in same transaction ([#9](https://github.com/mlasevich/PyRSMQ/issues/9)) (@yehonatanz)
  * Use redis timestamp in milliseconds instead of local in seconds ([#11](https://github.com/mlasevich/PyRSMQ/pull/11)) (@yehonatanz)
  * Convert queue attributes to numbers when elligible ([#12](https://github.com/mlasevich/PyRSMQ/pull/12)) (@yehonatanz)


* 0.4.3 
  * Don't encode sent message if it is of type bytes ([#6](https://github.com/mlasevich/PyRSMQ/issues/6))  (@yehonatanz)
  * Allow delay and vt to be float (round only after converting to millis) ([#7](https://github.com/mlasevich/PyRSMQ/issues/7)) (@yehonatanz)
  * Convert ts from str/bytes to int in receive/pop message ([#8](https://github.com/mlasevich/PyRSMQ/issues/8)) (@yehonatanz)

* 0.4.2
  * Fix typo in `setClient` method [#3](https://github.com/mlasevich/PyRSMQ/issues/3)
      * Note this is a breaking change if you use this method, (which seems like nobody does)

* 0.4.1
  * Add auto-decode option for messages from JSON (when possible) in Consumer (on by default)

* 0.4.0
  * Ability to import `RedisSMQ` from package rather than from the module (i.e. you can now use `from rsmq import RedisSMQ` instead of `from rsmq.rsmq import RedisSMQ`)
  * Add quiet option to most commands to allow to hide errors if exceptions are disabled
  * Additional unit tests
  * Auto-encoding of non-string messages to JSON for sendMessage
  * Add `RedisSMQConsumer` and `RedisSMQConsumerThread` for easier creation of queue consumers
  * Add examples for simple producers/consumers
  
* 0.3.1
  * Fix message id generation match RSMQ algorithm

* 0.3.0
  * Make message id generation match RSMQ algorithm
  * Allow any character in queue name other than `:`

* 0.2.1
  * Allow uppercase characters in queue names

* 0.2.0 - Adding Python 2 support
  * Some Python 2 support
  * Some Unit tests
  * Change `.exec()` to `.execute()` for P2 compatibility

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

*NOTE* This project is written for Python 3.x. While some attempts to get Python2 support were made
I am not sure how stable it would be under Python 2

This version is heavily based on Java version (https://github.com/igr/jrsmq), which in turn is
based on the original Node.JS version.

### API
To start with, best effort is made to maintain same method/parameter/usablity named of both version
(which, admittedly, resulted in a not very pythonic API)

Although much of the original API is still present, some alternatives are added to make life a bit
easier.

For example, while you can set any available parameter to command using the "setter" method, you can
also simply specify the parameters when creating the command. So these two commands do same thing:

    rqsm.createQueue().qname("my-queue").vt(20).execute()

    rqsm.createQueue(qname="my-queue", vt=20).execute()

In addition, when creating a main controller, any non-controller parameters specified will become
defaults for all commands created via this controller - so, for example, you if you plan to work
with only one queue using this controller, you can specify the qname parameter during creation of
the controller and not need to specify it in every command.

### A "Consumer" Service Utility

In addition to all the APIs in the original RSMQ project, a simple to use consumer implementation
is included in this project as `RedisSMQConsumer` and `RedisSMQConsumerThread` classes.

#### RedisSMQConsumer
The `RedisSMQConsumer` instance wraps an RSMQ Controller and is configured with a processor method
which is called every time a new message is received. The processor method returns true or false 
to indicate if message was successfully received and the message is deleted or returned to the
queue based on that. The consumer auto-extends the visibility timeout as long as the processor is
running, reducing the concern that item will become visible again if processing takes too long and
visibility timeout elapses.

NOTE: Since currently the `realtime` functionality is not implemented, Consumer implementation is
currently using polling to check for queue items. 

Example usage:

```
from rsmq.consumer import RedisSMQConsumer

# define Processor
def processor(id, message, rc, ts):
  ''' process the message '''
  # Do something
  return True

# create consumer
consumer = RedisSMQConsumer('my-queue', processor, host='127.0.0.1')

# run consumer
consumer.run()
```

For a more complete example, see examples directory.


#### RedisSMQConsumerThread

`RedisSMQConsumerThread` is simply a version of `RedisSMQConsumer` that extends Thread class.

Once created you can start it like any other thread, or stop it using `stop(wait)` method, where
wait specifies maximum time to wait for the thread to stop before returning (the thread would still
be trying to stop if the `wait` time expires)

Note that the thread is by default set to be a `daemon` thread, so on exit of your main thread it
will be stopped. If you wish to disable daemon flag, just disable it before starting the thread as
with any other thread

Example usage:

```
from rsmq.consumer import RedisSMQConsumerThread

# define Processor
def processor(id, message, rc, ts):
  ''' process the message '''
  # Do something
  return True

# create consumer
consumer = RedisSMQConsumerThread('my-queue', processor, host='127.0.0.1')

# start consumer
consumer.start()

# do what else you need to, then stop the consumer
# (waiting for 10 seconds for it to stop):
consumer.stop(10)

```

For a more complete example, see examples directory.

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

    rsmq.createQueue().exceptions(False).execute()


## Usage

### Example Usage

In this example we will create a new queue named "my-queue", deleting previous version, if one
exists, and then send a message with a 2 second delay. We will then demonstrate both the lack of
message before delay expires and getting the message after timeout


    from pprint import pprint
    import time

    from rsmq import RedisSMQ


    # Create controller.
    # In this case we are specifying the host and default queue name
    queue = RedisSMQ(host="127.0.0.1", qname="myqueue")


    # Delete Queue if it already exists, ignoring exceptions
    queue.deleteQueue().exceptions(False).execute()

    # Create Queue with default visibility timeout of 20 and delay of 0
    # demonstrating here both ways of setting parameters
    queue.createQueue(delay=0).vt(20).execute()

    # Send a message with a 2 second delay
    message_id = queue.sendMessage(delay=2).message("Hello World").execute()

    pprint({'queue_status': queue.getQueueAttributes().execute()})

    # Try to get a message - this will not succeed, as our message has a delay and no other
    # messages are in the queue
    msg = queue.receiveMessage().exceptions(False).execute()

    # Message should be False as we got no message
    pprint({"Message": msg})

    print("Waiting for our message to become visible")
    # Wait for our message to become visible
    time.sleep(2)

    pprint({'queue_status': queue.getQueueAttributes().execute()})
    # Get our message
    msg = queue.receiveMessage().execute()

    # Message should now be there
    pprint({"Message": msg})

    # Delete Message
    queue.deleteMessage(id=msg['id'])

    pprint({'queue_status': queue.getQueueAttributes().execute()})
    # delete our queue
    queue.deleteQueue().execute()

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

* `exceptions(True/False)` - enable/disable exceptions
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
        * `quiet` - if set to `True` and exceptions are disabled, do not produce error log entries
    * **Returns**:
        * `True` if queue was created

* `deleteQueue()` - Delete Existing queue
   * Parameters:
        * `qname` - (Required) name of the queue
        * `quiet` - if set to `True` and exceptions are disabled, do not produce error log entries
    * **Returns**:
        * `True` if queue was deleted

* `setQueueAttributes()` - Update queue attributes. If value is not specified, it is not updated.
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `vt` - default visibility timeout in seconds. Default: `30`
        * `delay` - default delay (visibility timeout on insert). Default: `0`
        * `maxsize` - maximum message size (1024-65535, Default: 65535)
        * `quiet` - if set to `True` and exceptions are disabled, do not produce error log entries
    * **Returns**:
        * output of `getQueueAttributes()` call

* `getQueueAttributes()` - Get Queue Attributes and statistics
   * Parameters:
        * `qname` - (Required) name of the queue
        * `quiet` - if set to `True` and exceptions are disabled, do not produce error log entries
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
        * `quiet` - if set to `True` and exceptions are disabled, do not produce error log entries
        * ???
    * **Returns**:
        * ???

* `sendMessage()` - Send message into queue
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `message` - (Required) message id
        * `delay` - Optional override of the `delay` for this message (If not specified, default for queue is used)
        * `quiet` - if set to `True` and exceptions are disabled, do not produce error log entries
        * `encode` if set to `True`, force encode message as JSON string. If False, try to auto-detect if message needs to be encoded
    * **Returns**:
        * message id of the sent message

* `receiveMessage()` - Receive Message from queue and mark it invisible
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `vt` - Optional override for visibility timeout for this message (If not specified, default for queue is used)
        * `quiet` - if set to `True` and exceptions are disabled, do not produce error log entries
    * **Returns** dictionary for following fields:
        * `id` - message id
        * `message` - message content
        * `rc` - receive count - how many times this message was received
        * `ts` - unix timestamp of when the message was originally sent

* `popMessage()` -  Receive Message from queue and delete it from queue
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `quiet` - if set to `True` and exceptions are disabled, do not produce error log entries
    * **Returns** dictionary for following fields:
        * `id` - message id
        * `message` - message content
        * `rc` - receive count - how many times this message was received
        * `ts` - unix timestamp of when the message was originally sent

* `deleteMessage()` -  Delete Message from queue
    * **Parameters:**
        * `qname` - (Required) name of the queue
        * `id` - (Required) message id
        * `quiet` - if set to `True` and exceptions are disabled, do not produce error log entries
    * **Returns**:
        * `True` if message was deleted
