'''
Python Redis Simple Queue Manager
'''

from redis import Redis

from . import const
from .cmd import ChangeMessageVisibilityCommand
from .cmd import CreateQueueCommand, DeleteQueueCommand, ListQueuesCommand
from .cmd import DeleteMessageCommand
from .cmd import SendMessageCommand, ReceiveMessageCommand, PopMessageCommand
from .cmd import SetQueueAttributesCommand, GetQueueAttributesCommand


DEFAULT_REDIS_OPTIONS = {
    'encoding': 'utf-8',
    'decode_responses': True
}

DEFAULT_OPTIONS = {
    'ns': 'rsmq',
    'realtime': False,
    'exceptions': True
}


class RedisSMQ():
    '''
    Redis Simple Message Queue implementation in Python
    '''

    def __init__(self, client=None, host="127.0.0.1", port="6379", options=None, **kwargs):
        '''
        Constructor:

        @param client: if provided, redis client object to use
        @param host: if client is not provided, redis hostname
        @param port: if client is not provided, redis port
        @param options: if client is not provided, additional options for redis client creation

        Additional arguments:

        @param ns: namespace
        @param realtime: if true, use realtime comms (pubsub)(default is False)
        @param exceptions: if true, throw exceptions on errors, else return False(default is True)

        Remaining params are automatically passed to commands

        '''

        # redis_client
        self._client = client

        # Redis Options
        self.redis_options = dict(DEFAULT_REDIS_OPTIONS)
        self.redis_options['host'] = host
        self.redis_options['port'] = port
        if options:
            self.redis_options.update(options)

        # RSMQ global options
        self.options = dict(DEFAULT_OPTIONS)
        to_remove = []
        for param, value in kwargs.items():
            if param in self.options:
                self.options[param] = kwargs[param]
                to_remove.append(param)
            elif value is None:
                # Remove default set to None
                to_remove.append(param)

        # Remove unnecessary kwargs
        for param in to_remove:
            del kwargs[param]

        # Everything else is passed through to commands
        self._default_params = kwargs

        self._popMessageSha1 = None
        self._receiveMessageSha1 = None
        self._changeMessageVisibilitySha1 = None

    @property
    def popMessageSha1(self):
        ''' Get Pop Message Script SHA1 '''
        if self._popMessageSha1 is None:
            client = self.client
            self._popMessageSha1 = client.script_load(const.SCRIPT_POPMESSAGE)
        return self._popMessageSha1

    @property
    def receiveMessageSha1(self):
        ''' Get Received Message Script SHA1 '''
        if self._receiveMessageSha1 is None:
            client = self.client
            self._receiveMessageSha1 = client.script_load(
                const.SCRIPT_RECEIVEMESSAGE)
        return self._receiveMessageSha1

    @property
    def changeMessageVisibilitySha1(self):
        ''' Get Change Message Visibilities Script SHA1 '''
        if self._changeMessageVisibilitySha1 is None:
            client = self.client
            self._changeMessageVisibilitySha1 = client.script_load(
                const.SCRIPT_CHANGEMESSAGEVISIBILITY)
        return self._changeMessageVisibilitySha1

    @property
    def client(self):
        ''' get Redis client. Create one if one does not exist '''
        if not self._client:
            self._client = Redis(**self.redis_options)
        return self._client

    def exceptions(self, enabled=True):
        ''' Set global exceptions flag '''
        self.options['exceptions'] = enabled == True
        return self

    def setClient(self, client):
        ''' Set Redis Client '''
        self._client = client
        return self

    def _command(self, command, **kwargs):
        ''' Run command '''
        args = dict(self._default_params)
        args.update(kwargs)
        return command(self, **args)

    def createQueue(self, **kwargs):
        ''' Create Queue '''
        return self._command(CreateQueueCommand, **kwargs)

    def deleteQueue(self, **kwargs):
        ''' Create Queue '''
        return self._command(DeleteQueueCommand, **kwargs)

    def setQueueAttributes(self, **kwargs):
        ''' setQueueAttributesCommand() '''
        return self._command(SetQueueAttributesCommand, **kwargs)

    def getQueueAttributes(self, **kwargs):
        ''' getQueueAttributesCommand() '''
        return self._command(GetQueueAttributesCommand, **kwargs)

    def listQueues(self, **kwargs):
        ''' List Queues '''
        return self._command(ListQueuesCommand, **kwargs)

    def changeMessageVisibility(self, **kwargs):
        ''' ChangeMessageVisibilityCommand '''
        return self._command(ChangeMessageVisibilityCommand, **kwargs)

    def sendMessage(self, **kwargs):
        ''' Send Message Command '''
        return self._command(SendMessageCommand, **kwargs)

    def receiveMessage(self, **kwargs):
        ''' Receive Message Command '''
        return self._command(ReceiveMessageCommand, **kwargs)

    def popMessage(self, **kwargs):
        ''' Pop Message Command '''
        return self._command(PopMessageCommand, **kwargs)

    def deleteMessage(self, **kwargs):
        ''' Delete Message Command '''
        return self._command(DeleteMessageCommand, **kwargs)

    def quit(self):
        ''' Quit - here for compatibility purposes '''
        self._client = None
