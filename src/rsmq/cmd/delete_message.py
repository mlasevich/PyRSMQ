"""

"""

from .base_command import BaseRSMQCommand


class DeleteMessageCommand(BaseRSMQCommand):
    """
    Delete Message if it exists
    """

    PARAMS = {
        "qname": {"required": True, "value": None},
        "id": {"required": True, "value": None},
        "quiet": {"required": False, "value": False},
    }

    def exec_command(self):
        """Exec Command"""
        result = self.get_transaction().execute()

        # 1 key deleted from zset
        # 3 keys deleted from hash (message itself, receive count, first receive field)
        if int(result[0]) == 1 and int(result[1]) == 3:
            return True

        return False

    def get_transaction(self):
        """Returns a transaction (pipeline), pre-populated with the deleteMessage commands"""
        client = self.client
        queue_base = self.queue_base
        queue_key = self.queue_key
        message_id = self.get_id
        # decode to string when provided as bytes
        if isinstance(message_id, bytes):
            message_id = message_id.decode('utf-8')
        tx = client.pipeline(transaction=True)
        tx.zrem(queue_base, message_id)
        tx.hdel(queue_key, message_id, "%s:rc" % message_id, "%s:fr" % message_id)
        return tx
