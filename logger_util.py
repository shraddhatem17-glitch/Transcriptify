from logging import getLogger


log = getLogger(__name__)


def get_logger(name, log_file_name="current.log"):
    import os
    import logging
    from concurrent_log_handler import ConcurrentRotatingFileHandler
    LOG_DIR = 'log/'
    log_format = '%(asctime)s - %(name)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s'
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Prevent adding multiple handlers if logger already configured
    if not logger.handlers:
        # File handler
        one_mb_byte = 2 ** 20
        f_handler = ConcurrentRotatingFileHandler(
            os.path.join(LOG_DIR, log_file_name),
            maxBytes=one_mb_byte * 10,
            backupCount=100
        )
        f_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(f_handler)

        # Console (stream) handler
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(c_handler)

    logger.propagate = False
    return logger
