'''
Example Producer for a queue


In this example we create RedisSMQ controller and using it to send messages to that at
regular intervals

'''
import argparse
import logging
import random
import sys
from threading import Thread
import time

from rsmq import RedisSMQ
from rsmq.consumer import RedisSMQConsumer


LOG = logging.getLogger("Producer")


def create_message(msg_number):
    ''' Create a message to send '''
    return {"item": msg_number,
            "ts": time.time()}


def produce(rsmq, long_qname, count, interval):
    LOG.info("Starting producer for queue '%s' - sending %s messages every %s seconds...",
             long_qname, count, interval)

    msg_count = 0
    while True:
        msg_count += 1
        msg = create_message(msg_count)
        rsmq.sendMessage(message=msg, encode=True).execute()
        if count > 0 and msg_count >= count:
            # Stop if we are done
            break
        LOG.debug("Waiting %s seconds to send next message", interval)
        time.sleep(interval)
    LOG.info("Ended producer after sending %s messages.", msg_count)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    ''' Parse args and run producer '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--queue", dest="queue", action="store", default="queue",
                        help="queue name [default: %(default)s]")
    parser.add_argument("-n", "--namespace", dest="ns", action="store", default="test",
                        help="queue namespace [default: %(default)s]")

    parser.add_argument("-c", "--count", dest="count", action="store", type=int, default=0,
                        help="number of messages to send. If less than 1, send continuously " +
                        "[default: %(default)s]")

    parser.add_argument("-i", "--interval", dest="interval", type=float, default=1.5,
                        help="Interval, in seconds, to send [default: %(default)s]")

    parser.add_argument("-d", "--delay", dest="delay", type=int, default=0,
                        help="delay, in seconds, to send message with [default: %(default)s]")

    parser.add_argument("-v", "--visibility_timeout", dest="vt", type=int, default=None,
                        help="Visibility Timeout[default: %(default)s]")

    parser.add_argument("--delete", dest="delete", action="store_true", default=False,
                        help="If set, delete queue first")

    parser.add_argument("--no-trace", dest="trace", action="store_false", default=True,
                        help="If set, hide trace messages")

    parser.add_argument("-H", dest="host", default="127.0.0.1",
                        help="Redis Host [default: %(default)s]")
    parser.add_argument("-P", dest="port", type=int, default=6379,
                        help="Redis Port [default: %(default)s]")
    # Parse command line args`
    args = parser.parse_args()

    # Create RedisSMQ queue controller
    LOG.info("Creating RedisSMQ controller for redis at %s:%s, using default queue: %s:%s",
             args.host, args.port, args.ns, args.queue)
    rsqm = RedisSMQ(qname=args.queue, host=args.host,
                    port=args.port, ns=args.ns, vt=args.vt,
                    delay=args.delay, trace=args.trace)

    if args.delete:
        rsqm.deleteQueue(qname=args.queue, quiet=True).exceptions(
            False).execute()

    # Create queue if it is missing. Swallow errors if already exists
    rsqm.createQueue(qname=args.queue, quiet=True).exceptions(False).execute()

    # Start Producing
    produce(rsqm, "%s:%s" % (args.ns, args.queue), args.count, args.interval)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main(sys.argv)
