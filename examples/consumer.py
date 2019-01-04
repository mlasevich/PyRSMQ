'''
Example Consumer for a queue


In this example we create an queue consumer that gets one message at a time, and processes
it using a processor. To emulate some of the complexities, we randomly fail processing and adding
delays to processing.

'''
import argparse
import logging
import random
import sys
from threading import Thread
import time

from rsmq import RedisSMQ
from rsmq.consumer import RedisSMQConsumer


LOG = logging.getLogger("Consumer")


class Processor(object):
    ''' Dummy processor class to fake complexity of a real processor '''

    def __init__(self, delay, success_rate):
        self.delay = delay
        self.success_rate = success_rate

    def random_result(self):
        ''' 
        Produce a random boolean which is True "success_rate" percent of the time

        random.random() produces a float in range [0.0, 1.0)
        '''
        return random.random() < self.success_rate

    def process(self, id, message, rc, ts):
        ''' Actual method that processes the message '''
        LOG.info("Got message: id: %s, retry count: %s, ts: %s, msg: %s" %
                 (id, rc, ts, message))
        result = self.random_result()
        delay = self.delay
        if delay > 0:
            # Add occasional long delay
            # if random.randint(0, 10) == 0:
            #    delay = 60
            LOG.info("Processing message: %s for %s seconds", id, delay)
            time.sleep(delay)
        #LOG.info("Random Result: %s", "Success" if result else "Failure")
        return result


def consume(consumer, long_qname, exit_after):
    ''' Example of consuming using a thread '''
    LOG.info("Starting consumption on queue: %s", long_qname)
    thread = Thread(
        target=consumer.run, name="QueueConumer", daemon=False)
    thread.start()
    end = time.time() + exit_after if exit_after else 0
    while True:
        if exit_after and time.time() > end:
            LOG.info("Attempting to stop the consumer...")
            consumer.stop(15)
            break
    LOG.info("Exited queue consumer for '%s'. Thread is %s",
             long_qname, ("running" if thread.is_alive() else "stopped"))


def probablity(x):
    ''' An arg validator that Require a float number between 0.0 and 1.0 '''
    x = float(x)
    if not (0.0 <= x <= 1.0):
        raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]" % (x,))
    return x


def main(argv=None):
    if argv is None:
        argv = sys.argv
    ''' Parse args and run producer '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--queue", dest="queue", action="store", default="queue",
                        help="queue name [default: %(default)s]")
    parser.add_argument("-n", "--namespace", dest="ns", action="store", default="test",
                        help="queue namespace [default: %(default)s]")

    parser.add_argument("-r", "--success_rate", dest="success_rate", action="store",
                        type=probablity,
                        default=1.0, help="Probability of success when processing messages." +
                        "1.0 means all are successful, 0.0 means all fail" +
                        "[default: %(default)s]")

    parser.add_argument("-e", "--empty_delay", dest="empty_queue_delay", type=float, default=4.0,
                        help="delay in seconds when queue is empty[default: %(default)s]")

    parser.add_argument("-d", "--delay", dest="delay", type=float, default=2.0,
                        help="additional delay in seconds, during consumption[default: %(default)s]")

    parser.add_argument("-x", "--exit_after", dest="exit_after", type=float, default=0.0,
                        help="If set, exit after this many seconds[default: %(default)s]")

    parser.add_argument("-v", "--visibility_timeout", dest="vt", type=int, default=None,
                        help="Visibility Timeout[default: %(default)s]")

    parser.add_argument("--no-trace", dest="trace", action="store_false", default=True,
                        help="If set, hide trace messages")

    parser.add_argument("-H", dest="host", default="127.0.0.1",
                        help="Redis Host [default: %(default)s]")
    parser.add_argument("-P", dest="port", type=int, default=6379,
                        help="Redis Port [default: %(default)s]")

    # Parse command line args`
    args = parser.parse_args()

    # Create Processor
    processor = Processor(delay=args.delay, success_rate=args.success_rate)

    # Create RedisSMQ queue consumer controller
    LOG.info("Creating RedisSMQ Consumer Controller for redis at %s:%s, using queue: %s:%s",
             args.host, args.port, args.ns, args.queue)
    rsqm_consumer = RedisSMQConsumer(qname=args.queue,
                                     processor=processor.process,
                                     host=args.host, port=args.port, ns=args.ns, vt=args.vt,
                                     empty_queue_delay=args.empty_queue_delay, trace=args.trace)

    # Start Consumption
    consume(rsqm_consumer, "%s:%s" % (args.ns, args.queue), args.exit_after)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main(sys.argv)
