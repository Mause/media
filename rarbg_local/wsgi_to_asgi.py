import logging
from asyncio import get_event_loop, new_event_loop, set_event_loop, sleep
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from queue import Empty, Queue
from threading import Event
from typing import Dict

RESPONSE_STATUS_TEXT = {code: str(code) for code in range(100, 600)}
RESPONSE_STATUS_TEXT.update(
    {status.value: "%d %s" % (status.value, status.phrase) for status in HTTPStatus}
)


executor = ThreadPoolExecutor(10)


def call_sync(app, scope, start_response, body):
    async def send(message):
        type_ = message['type']
        logging.info('received message of type %s', type_)

        if type_ == 'http.response.start':
            status = RESPONSE_STATUS_TEXT[message['status']]
            headers = [
                [key.decode('latin-1'), value.decode('latin-1')]
                for key, value in message['headers']
            ]
            start_response(status, headers, None)

            first_event.set()
        elif type_ == 'http.response.body':
            body = message.pop('body', None)
            if body:
                body_queue.put(body)

            if 'more_body' in message:
                if not message['more_body']:
                    last_event.set()
            else:
                last_event.set()
        else:
            raise Exception('unknown message type: ' + type_)

    body = [body.read()]

    async def recieve():
        if body:
            return {'type': 'http.request', 'body': body.pop()}
        elif last_event.is_set():
            return {'type': 'http.disconnect'}
        else:
            await sleep(0)
            return {'type': 'http.*'}

    async def call():
        # breakpoint()
        await app(scope, recieve, send)

    def worker():
        try:
            el = get_event_loop()
        except RuntimeError:
            el = new_event_loop()
            set_event_loop(el)
        el.run_until_complete(call())

    first_event = Event()
    last_event = Event()
    body_queue: Queue[Dict] = Queue()

    def genny():
        while not last_event.is_set():
            try:
                yield body_queue.get_nowait()
            except Empty:
                pass
        while not body_queue.empty():
            yield body_queue.get()

    executor.submit(worker)
    first_event.wait()  # wait until we have the status, headers

    return genny()


class ASGItoWSGIAdapter:
    """
    Expose an WSGI interface, given an ASGI application.

    Based on https://gist.github.com/mtorromeo/f7608efc5dad47299f9e270a069c9159
    """

    def __init__(self, asgi, raise_exceptions=False):
        self.asgi = asgi
        self.raise_exceptions = raise_exceptions

    def __call__(self, environ, start_response):
        message = self.environ_to_message(environ)

        try:
            return call_sync(
                self.asgi, message, start_response, body=environ['wsgi.input']
            )
        except Exception:
            if self.raise_exceptions:
                raise

    def environ_to_message(self, environ):
        """
        WSGI environ -> ASGI message
        """
        message = {
            'type': 'http',
            'method': environ['REQUEST_METHOD'].upper(),
            'root_path': environ.get('SCRIPT_NAME', ''),
            'path': environ.get('PATH_INFO', ''),
            'query_string': environ.get('QUERY_STRING', '').encode('latin-1'),
            'http_version': environ.get('SERVER_PROTOCOL', 'http/1.0').split('/', 1)[
                -1
            ],
            'scheme': environ.get('wsgi.url_scheme', 'http'),
            'raise_exceptions': self.raise_exceptions,  # Not actually part of the ASGI spec
        }

        if 'REMOTE_ADDR' in environ and 'REMOTE_PORT' in environ:
            message['client'] = [environ['REMOTE_ADDR'], int(environ['REMOTE_PORT'])]
        if 'SERVER_NAME' in environ and 'SERVER_PORT' in environ:
            message['server'] = [environ['SERVER_NAME'], int(environ['SERVER_PORT'])]

        headers = []
        if environ.get('CONTENT_TYPE'):
            headers.append([b'content-type', environ['CONTENT_TYPE'].encode('latin-1')])
        if environ.get('CONTENT_LENGTH'):
            headers.append(
                [b'content-length', environ['CONTENT_LENGTH'].encode('latin-1')]
            )
        for key, val in environ.items():
            if key.startswith('HTTP_'):
                key_bytes = key[5:].replace('_', '-').lower().encode('latin-1')
                val_bytes = val.encode()
                headers.append([key_bytes, val_bytes])

        message['headers'] = headers

        return message
