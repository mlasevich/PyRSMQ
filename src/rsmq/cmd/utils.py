''' Utilities '''
import random


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
        charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    string = ''
    for _ in range(length):
        string += random.choice(charset)
    return string


def make_message_id(secs, msecs=0):
    ''' Create a message id based on redis time '''
    message_id = baseXencode("%010d%06d" % (secs, msecs))
    return message_id + random_string(22)


if __name__ == "__main__":
    import time
    now = time.time()
    seconds = int(now)
    ms = int((now - seconds) * 1000000)
    print("TS: %s :: %s" % (now, make_message_id(seconds, ms)))
    import uuid
    print("UUID: %s" % uuid.uuid4().hex)
