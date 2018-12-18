''' Utilities '''


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
