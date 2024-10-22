"""
Utility to handle exp retry delay
"""
import logging
import time

LOG = logging.getLogger(__name__)


class RetryDelayHandler:
    """ Tool to manage exponential retry delays """

    def __init__(self, min_delay: float = 0, max_delay: float = 60):
        """ Initialize """
        self.current_delay = min_delay
        self.min_delay = min_delay
        self.max_delay = max_delay

    def reset(self):
        """ Reset delay """
        self.current_delay = self.min_delay

    def delay(self):
        """ Perform delay """
        if self.current_delay:
            LOG.debug("Retrying in %s seconds", self.current_delay)
            time.sleep(self.current_delay)
            self.current_delay = min(self.current_delay * 2, self.max_delay)
        else:
            self.current_delay = 1.0
