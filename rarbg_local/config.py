import os
from urllib.parse import urlparse

import pika

url_str = os.environ['CLOUDAMQP_URL']
url = urlparse(url_str)
parameters = pika.ConnectionParameters(
    host=url.hostname,
    virtual_host=url.path[1:],
    credentials=pika.PlainCredentials(url.username, url.password),
)
