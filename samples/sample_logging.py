import logging
import logging.config

_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "%(asctime)s - %(name)s - %(levelname)-5s - %(message)s"
        }
    },
    'handlers': {
        'console': {
            'level': 'NOTSET',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }
    },
    'root': {
        'level': 'INFO',
        'propagate': False,
        'handlers': ['console']
    },
    'loggers': {
        'pyoctopus': {
            'level': 'DEBUG',
            'propagate': False,
            'handlers': ['console']
        }
    }
}


def setup():
    logging.config.dictConfig(_LOGGING_CONFIG)
