import logging
from contextvars import ContextVar
from logging import Handler

local_appender: ContextVar[list[logging.LogRecord]] = ContextVar[
    list[logging.LogRecord]
]('local_appender')


class Appender(Handler):
    def emit(self, record: logging.LogRecord) -> None:
        appender = local_appender.get(None)
        if appender is not None:
            appender.append(record)


logging.getLogger().addHandler(Appender())
