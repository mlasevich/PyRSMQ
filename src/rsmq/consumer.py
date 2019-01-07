'''
Python Redis Simple Queue Manager Consumer
'''


import logging
from threading import Thread
import time

from rsmq.cmd.exceptions import NoMessageInQueue

from .cmd import utils
from .cmd.exceptions import RedisSMQException
from .rsmq import RedisSMQ
from .rsmq import const


LOG = logging.getLogger(__name__)


class RedisSMQConsumer():
    '''
    RSMQ Consumer Worker
    '''
    # local parameters and their value
    LOCAL_PARAMS = {'retry_delay': 0,
                    'empty_queue_delay': 2.0,
                    'decode': True}

    class VisibilityTimeoutExtender(Thread):
        ''' Thread that keeps the visibility '''

        def __init__(self, consumer, message_id):
            ''' Initialize '''
            self.consumer = consumer
            self.rsqm = consumer.rsqm

            self.vt = consumer.vt
            self.message_id = message_id
            thread_name = "VTExtender:%s" % message_id
            super(RedisSMQConsumer.VisibilityTimeoutExtender,
                  self).__init__(name=thread_name)

            self.daemon = True
            self._request_stop = False

            # How often to check time
            self.interval = self.vt / 4

            self.next_extension = time.time() + self.vt / 2
            self.set_next_extension()

        def set_next_extension(self):
            ''' set next extension '''
            self.next_extension = time.time() + self.vt / 2

        def trace(self, msg, *args):
            ''' Passthrough for trace messages '''
            self.consumer.trace("VisibilityTimeoutExtender: %s" % msg, args)

        def extend(self):
            ''' extend visibility timeout '''
            try:
                self.trace("Extending visibility by %s seconds...", self.vt)
                self.rsqm.changeMessageVisibility(
                    vt=self.vt, id=self.message_id).execute()
                self.set_next_extension()
            except RedisSMQException as ex:
                LOG.warning(
                    "Failed to extend message visibility for %s: %s", self.message_id, ex)

        def stop(self):
            ''' Stop this thread '''
            self._request_stop = True

        def run(self):
            ''' Run'''
            while not self._request_stop:
                time.sleep(self.interval)
                if not self._request_stop and time.time() > self.next_extension:
                    self.extend()
                    self.set_next_extension()

    def __init__(self, qname, processor, **rsmq_params):
        '''
        initialize 

        Required Parameters:

        @param qname: queue name
        @param processor: processor for each item

        Optional Parameters: 
        @param retry_delay: amount of time, in seconds, before failed item is retried
        @param empty_queue_delay: (float) Amount of time, in seconds, to wait if no items in queue  

        Remaining args are passed to RedisSMQ()

        '''
        self._request_stop = False
        self.rsqm = RedisSMQ(qname=qname, **rsmq_params)
        self.qname = qname
        self.processor = processor

        self._trace = rsmq_params.get('trace', False)

        # Separate local params from kwargs
        self.params = {}
        for param, value in self.LOCAL_PARAMS.items():
            self.params[param] = rsmq_params.get(param, value)
            if param in rsmq_params:
                del rsmq_params[param]

        # get vt from kwargs, if set
        self.vt = rsmq_params.get('vt', None)
        # get vt from queue if not set in kwargs and queue exists
        self._get_vt()

    def _param(self, param, default_value=None):
        ''' get local param '''
        return self.params.get(param, self.LOCAL_PARAMS.get(param, default_value))

    @property
    def retry_delay(self):
        ''' retry delay '''
        return self._param('retry_delay')

    @property
    def empty_queue_delay(self):
        ''' empty_queue_delay '''
        return self._param('empty_queue_delay')

    @property
    def decode(self):
        ''' decode, if true, attempt to decode the output from JSON '''
        return self._param('decode')

    def _get_vt(self):
        ''' Get VT from the queue info if not set '''
        if self.vt is None:
            queue_info = self.rsqm.getQueueAttributes().qname(
                self.qname).exceptions(False).execute()
            if queue_info and 'vt' in queue_info:
                self.vt = int(queue_info.get('vt', const.VT_DEFAULT))
            else:
                self.vt = const.VT_DEFAULT

    def stop(self, wait=None):
        ''' Stop '''
        self._request_stop = True
        if wait:
            wait_until = time.time() + wait
            while not time.time() > wait_until:
                time.sleep(0.5)
                if self._request_stop is None:
                    break
        return self._request_stop is None

    def on_success(self, msg):
        ''' Run on success '''
        # delete the item
        if msg and 'id' in msg:
            self.trace("Processed message %s", msg['id'])
            self.rsqm.deleteMessage(qname=self.qname, id=msg['id']).execute()

    def on_failure(self, msg):
        ''' Run on success '''

        if msg and 'id' in msg:
            LOG.warning("Failed to process message %s", msg['id'])
            self.rsqm.changeMessageVisibility(vt=self.retry_delay,
                                              qname=self.qname,
                                              id=msg['id']).execute()

    def create_queue(self):
        ''' Create queue if it does not exists '''
        self.rsqm.createQueue(
            qname=self.qname, quiet=True).exceptions(False).execute()

    def trace(self, fmt, *args):
        ''' Print trace log messages for debugging, if enabled '''
        if self._trace is not False:
            LOG.debug(fmt, *args)

    def run(self):
        ''' main loop of the thread '''
        self.trace("Starting Queue Consumer for %s", self.qname)
        self.create_queue()
        while not self._request_stop:
            try:
                msg = self.rsqm.receiveMessage().execute()
                if msg and 'id' in msg:
                    extender = RedisSMQConsumer.VisibilityTimeoutExtender(
                        self, msg['id'])
                    extender.start()
                    if self.decode and 'message' in msg:
                        msg['message'] = utils.decode_message(msg['message'])
                    if self.processor(**msg):
                        self.on_success(msg)
                    else:
                        self.on_failure(msg)
                    extender.stop()
                else:
                    raise RedisSMQException(
                        "Invalid message in queue '%s': %s" % (self.qname, msg))
            except NoMessageInQueue:
                delay = self.empty_queue_delay
                self.trace("No message in queue, waiting %s seconds", delay)
                if delay:
                    time.sleep(delay)
            except RedisSMQException as ex:
                LOG.warning("Exception while processing queue `%s`: %s",
                            self.qname, ex)
        self._request_stop = None
        self.trace("Ended Queue Consumer for %s", self.qname)


class RedisSMQConsumerThread(RedisSMQConsumer, Thread):
    ''' Version of a RedisSMQConsumer implemented as a self-contained thread '''

    def __init__(self, qname, processor, **rsmq_params):
        ''' Constructor '''
        RedisSMQConsumer.__init__(self, qname, processor, **rsmq_params)
        Thread.__init__(self, name="RedisSMQConsumer:%s" % qname, daemon=True)
