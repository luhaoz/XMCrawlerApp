import logging


def logger(name):
    _logger = logging.getLogger(name)

    _stream_handler = logging.StreamHandler()
    _stream_handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    _stream_handler.setLevel(logging.INFO)

    _logger.addHandler(_stream_handler)

    return _logger
