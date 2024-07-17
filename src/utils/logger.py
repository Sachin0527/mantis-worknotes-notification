import logging

from src.config.config import read_config


# Custom Logging Class
class CustomLogger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CustomLogger, cls).__new__(cls)
            cls._instance._initialize_logger(*args, **kwargs)
        return cls._instance

    # Initialize the logger with logging file, level, format etc
    def _initialize_logger(self, config_file):
        self.config = read_config(config_file,'logging')
        self.log_file = self.config['logging_file']
        self.log_level = getattr(logging, self.config['logging_level'].upper())
        self.formatter = self.config['logging_format']
        self.logger = logging.getLogger()
        self.logger.setLevel(self.log_level)
        if not self.logger.hasHandlers():
            # File handler
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.log_level)

            # Formatter
            formatter = logging.Formatter(self.formatter)
            file_handler.setFormatter(formatter)

            # Add handlers to the logger
            self.logger.addHandler(file_handler)

    # returns the initialized logger
    def get_logger(self):
        return self.logger