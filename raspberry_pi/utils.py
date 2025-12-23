
import logging

class ColorfulFormatter(logging.Formatter):

    grey = "\x1b[90m"        # Bright Black (Debug)
    green = "\x1b[32m"       # Green (Info / Success)
    blue = "\x1b[34m"        # Blue (Alternative for Info)
    yellow = "\x1b[33m"      # Yellow (Warning)
    red = "\x1b[31m"         # Red (Error)
    bold_red = "\x1b[31;1m"  # Bold Red (Critical)
    reset = "\x1b[0m"        # Reset
    FORMAT = "[%(levelname)s] %(message)s"

    FORMATS = {
        logging.DEBUG: yellow + FORMAT + reset,
        logging.INFO: green + FORMAT + reset,
        logging.WARNING: yellow + FORMAT + reset,
        logging.ERROR: red + FORMAT + reset,
        logging.CRITICAL: bold_red + FORMAT + reset
    }
    
    def __init__(self, colorful: bool = True):
        self.colorful = colorful

    def format(self, record):
        if self.colorful:
            log_fmt = self.FORMATS.get(record.levelno)
        else:
            log_fmt = self.FORMAT
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name: str, log_dir: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(ColorfulFormatter())
        logger.addHandler(ch)
        
        if log_dir is None:
            log_dir = './logs'
        ch = logging.FileHandler(f'{log_dir}/{name}.log')
        ch.setFormatter(ColorfulFormatter(colorful=False))
        logger.addHandler(ch)
    return logger
