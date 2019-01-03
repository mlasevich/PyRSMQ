''' Utilities '''
import json
import random

DEFAULT_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def validate_int(value, min_value=None, max_value=None, logger=None, name=None):
    ''' Validate value is integer and between min and max values (if specified) '''
    if value is None:
        if logger and name:
            logger.debug("%s value is not set", name)
        return False
    try:
        int_value = int(value)
        if min_value is not None and int_value < min_value:
            if logger and name:
                logger.debug(
                    "%s value %s is less than minimum (%s)", name, int_value, min_value)
            return False
        if max_value is not None and int_value > max_value:
            if logger and name:
                logger.debug(
                    "%s value %s is greater than maximum (%s)", name, int_value, max_value)
            return False
    except ValueError:
        if logger and name:
            logger.debug("%s value (%s) is not an integer", name, value)
        return False
    return True


def baseXencode(value, chars='0123456789abcdefghijklmnopqrstuvwxyz'):
    '''
    Converts an integer to a base X string using charset. 
    Base is implied by charset = base36 by default 

    Based on: https://en.wikipedia.org/wiki/Base36

    raises ValueError if value cannot be converted to integer
    '''

    base = len(chars)
    integer = int(value)
    sign = '-' if integer < 0 else ''
    integer = abs(integer)
    result = ''

    while integer > 0:
        integer, remainder = divmod(integer, base)
        result = chars[remainder] + result

    return sign + result


def random_string(length, charset=None):
    ''' generate a random string of characters from charset '''
    if not charset:
        charset = DEFAULT_CHARSET

    string = ''
    for _ in range(length):
        string += random.choice(charset)
    return string


def make_message_id(usec):
    ''' Create a message id based on Redis time '''
    return baseXencode(usec) + random_string(22)


def encode_message(msg):
    ''' Encode message to JSON if not already string '''
    if isinstance(msg, str):
        return msg
    return json.dumps(msg)


def decode_message(msg):
    ''' Decode message from JSON if decodable, else return message as is '''
    if isinstance(msg, str):
        try:
            return json.loads(msg)
        except json.decoder.JSONDecodeError:
            pass
    return msg
