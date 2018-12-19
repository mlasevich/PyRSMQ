'''
Command Exceptions 
'''


class RedisSMQException(Exception):
    ''' Base Exception for all RQSM Commands '''

    def __init__(self, msg=None):
        ''' Default constructor '''
        if msg is None:
            msg = self.__doc__
        super(RedisSMQException, self).__init__(msg)


class CommandNotImplementedException(RedisSMQException):
    ''' Command is not yet implemented '''


class InvalidParameterValue(RedisSMQException):
    ''' Invalid Parameter Value'''

    def __init__(self, name, value):
        ''' Constructor '''
        super(InvalidParameterValue, self).__init__(
            "Value '%s' is not valid for parameter '%s'" % (value, name))


class QueueAlreadyExists(RedisSMQException):
    ''' Queue Already Exists '''

    def __init__(self, name):
        ''' Constructor '''
        super(QueueAlreadyExists, self).__init__(
            "Queue '%s' already exists" % name)


class QueueDoesNotExist(RedisSMQException):
    ''' Queue Already Exists '''

    def __init__(self, name):
        ''' Constructor '''
        super(QueueDoesNotExist, self).__init__(
            "Queue '%s' does not exist" % name)


class NoMessageInQueue(RedisSMQException):
    ''' Queue Already Exists '''

    def __init__(self, name):
        ''' Constructor '''
        super(NoMessageInQueue, self).__init__(
            "Queue '%s' has no messages waiting" % name)
