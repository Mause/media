import os
from functools import lru_cache
from urllib.parse import urlparse

import pika


@lru_cache()
def get_parameters():
    url_str = os.environ['CLOUDAMQP_URL']
    url = urlparse(url_str)
    return pika.ConnectionParameters(
        host=url.hostname,
        virtual_host=url.path[1:],
        credentials=pika.PlainCredentials(url.username, url.password),
    )
