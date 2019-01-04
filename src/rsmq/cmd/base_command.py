'''
Base Command for all the commands
'''

import logging
import re

from .. import const
from .exceptions import CommandNotImplementedException
from .exceptions import InvalidParameterValue
from .exceptions import QueueDoesNotExist
from .exceptions import RedisSMQException
from .utils import validate_int


# REGEX matching invalid QNAME characters
QNAME_INVALID_RE = re.compile(const.QNAME_INVALID_CHARS_RE)


class BaseRSMQCommand():
    ''' Base for all RQMS commands '''

    PARAMS = {'qname': {'required': True,
                        'value': None},
              'quiet': {'required': False,
                        'value': False}
              }

    def __init__(self, rsmq, **kwargs):
        self.log = logging.getLogger('rsmq.cmd.%s' % self.__class__.__name__)
        self.parent = rsmq
        self._params = {}
        # Load Defaults
        for name, value in self._param_defaults().items():
            self._params[name] = value
        # load args
        for name, value in kwargs.items():
            self._set_param(name, value)
        self.__exceptions = None

    @property
    def popMessageSha1(self):
        ''' popMessageSha1 '''
        return self.parent.popMessageSha1

    @property
    def receiveMessageSha1(self):
        ''' receiveMessageSha1 '''
        return self.parent.receiveMessageSha1

    @property
    def changeMessageVisibilitySha1(self):
        ''' changeMessageVisibilitySha1 '''
        return self.parent.changeMessageVisibilitySha1

    @property
    def _exceptions(self):
        ''' Returns true if exceptions are enabled'''
        if self.__exceptions is None:
            return self.parent.options.get('exceptions', True)
        return self.__exceptions

    def exceptions(self, enabled=True):
        ''' Control exceptions '''
        self.__exceptions = enabled != False
        return self

    @property
    def client(self):
        ''' Get Redis client '''
        return self.parent.client

    def _param_defaults(self):
        ''' Get dict of default parameters and their values '''
        defaults = {}
        for name, value in self.PARAMS.items():
            defaults[name] = value.get('value', None)
        return defaults

    def _required_params(self):
        ''' List of parameters that are required '''
        return [param
                for param, definition in self.PARAMS.items()
                if definition.get('required', False) == True]

    def config(self, key, default_value):
        ''' Get value from global config '''
        return self.parent.options.get(key, default_value)

    @property
    def namespace(self):
        ''' Get namespace '''
        namespace = self.config('ns', '')
        if namespace:
            return namespace + ':'
        return ''

    @property
    def queue_base(self):
        ''' Get base name of the queue '''
        return self.namespace + self.get_qname

    @property
    def queue_key(self):
        ''' Get Full queue name '''
        return self.queue_base + const.QUEUE_SUFFUX

    @property
    def queue_set(self):
        ''' Get Full Queue Set '''
        return self.namespace + const.QUEUES

    def param_get(self, param, default_value=None):
        ''' Get parameter by name '''
        return self._params.get(param, self.PARAMS[param].get('default', default_value))

    def __getattr__(self, name):
        ''' 
        Create setters for parameters on the fly 
        '''
        if name in self.PARAMS:
            def setter(value):
                if self._validate_param(name, value):
                    self._params[name] = value
                elif self._exceptions:
                    raise InvalidParameterValue(name, value)
                elif self.get_quiet is not True:
                    self.log.info("Invalid value for '%s': '%s'", name, value)
                return self
            return setter
        elif name.startswith('get_'):
            param = name[4:]
            if param in self.PARAMS:
                return self.param_get(param, default_value=None)

        raise AttributeError("'%s' object has no attribute '%s'" %
                             (self.__class__.__name__, name))

    def _validate_param(self, name, value):
        ''' Validate parameter value '''
        if hasattr(self, "_validate_%s" % name):
            validator = getattr(self, "_validate_%s" % name)
            return validator(value)
        return self._default_validator(name, value)

    def _default_validator(self, name, value):
        ''' Default Validator '''
        if not name:
            return False
        if not value:
            return False
        return True

    def _validate_qname(self, qname):
        ''' Validate Queue Name '''
        # Check we have a value at all
        if not qname:
            return False
        # check length
        if len(qname) > const.QNAME_MAX_LEN:
            return False
        # check if we have invalid characters
        if ':' in qname:
            print('Detected :')
            return False
        return True

    def _validate_vt(self, vt):
        ''' Validate visibility timeout parameter '''
        return validate_int(vt, const.VT_MIN, const.VT_MAX, logger=self.log, name="vt")

    def _validate_delay(self, delay):
        ''' Validate delay  parameter '''
        return validate_int(delay, const.DELAY_MIN, const.DELAY_MAX, logger=self.log, name="delay")

    def _validate_maxsize(self, maxsize):
        ''' Validate maxsize parameter '''
        return maxsize == -1 or validate_int(maxsize, const.MAXSIZE_MIN, const.MAXSIZE_MAX,
                                             logger=self.log, name="maxsize")

    def _set_param(self, name, value):
        ''' set parameter, with validation '''
        if name in self.PARAMS:
            if self._validate_param(name, value):
                self._params[name] = value
                return True
        return False

    def ready(self):
        ''' Check if we are ready to execute '''
        for param in self._required_params():
            if not self._validate_param(param, self._params[param]):
                self.log.info("Invalid value for parameter '%s'", param)
                return False
        return True

    def execute(self):
        ''' Execute Command '''
        if self._exceptions:
            return self._exec()
        try:
            ret = self._exec()
        except RedisSMQException as ex:
            if self.get_quiet is not True:
                self.log.warning("%s: Exception while processing %s: %s", ex.__class__.__name__,
                                 self.__class__.__name__, ex)
            return False
        return ret

    def _exec(self):
        if self.ready():
            return self.exec_command()
        return False

    def exec_command(self):
        ''' Execute Command '''
        raise CommandNotImplementedException()

    def queue_def(self):
        ''' Get Queue Definition '''
        queue_key = self.queue_key
        tx = self.client.pipeline(transaction=True)
        tx.hmget(queue_key, "vt", "delay", "maxsize")
        tx.time()

        results = tx.execute()

        if not results or results[0][0] is None:
            raise QueueDoesNotExist(self.get_queue)
        stats = results[0]
        redisTime = results[1]

        ts_usec = redisTime[0] * 1000000 + redisTime[1]
        ts = int(ts_usec / 1000)

        return {
            'qname': self.get_qname,
            "vt": stats[0],
            "delay": stats[1],
            "maxsize": stats[2],
            'ts': ts,
            'ts_usec': ts_usec
        }
