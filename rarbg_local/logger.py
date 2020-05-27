import logging

import timber

from .config import TIMBERIO_APIKEY, TIMBERIO_SOURCEID


class CustomTimberHandler(timber.TimberHandler):
    def _is_main_process(self):
        return False


def get_timber_handler():
    timber_handler = CustomTimberHandler(
        api_key=TIMBERIO_APIKEY, source_id=TIMBERIO_SOURCEID, raise_exceptions=True,
    )
    timber_handler.flush_thread.start()
    timber_handler.addFilter(
        lambda record: not (
            'logs.timber.io' in getattr(record, 'message', '')
            and record.levelno == logging.DEBUG
        )
    )
    return timber_handler
