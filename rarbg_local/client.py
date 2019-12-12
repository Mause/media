from concurrent.futures import Future
from dataclasses import dataclass
from functools import partial
from threading import Thread
from typing import Dict
from uuid import UUID, uuid4

import dill
import pika
from pika.adapters.blocking_connection import BlockingChannel

from .config import parameters

SERVER_QUEUE = 'rpc.server.queue'

_waiting: Dict[UUID, Future] = {}


@dataclass
class Proxy:
    conn: pika.BlockingConnection
    channel: BlockingChannel

    def call(self, method, *args, **kwargs):
        f = Future()
        key = uuid4().hex
        _waiting[key] = f
        self.conn.add_callback_threadsafe(
            lambda: self.channel.basic_publish(
                exchange='',
                routing_key=SERVER_QUEUE,
                body=dill.dumps(
                    {'method': method, 'args': args, 'kwargs': kwargs, 'key': key}
                ),
                properties=pika.BasicProperties(reply_to='amq.rabbitmq.reply-to'),
            )
        )
        return f.result()

    def __getattr__(self, method):
        return partial(self.call, method)


def get_client():
    conn = pika.BlockingConnection(parameters)
    channel = conn.channel()

    def recieve(ch, method_frame, properties, body):
        body = dill.loads(body)
        _waiting[body['key']].set_result(body['body'])

    channel.basic_consume('amq.rabbitmq.reply-to', recieve, auto_ack=True)

    t = Thread(target=channel.start_consuming)
    t.daemon = True
    t.start()

    return Proxy(conn, channel)


def main():
    client = get_client()

    print(client.get_torrents())


if __name__ == '__main__':
    main()
