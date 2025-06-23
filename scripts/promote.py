#!/usr/bin/env python

import logging

import requests
from follower import follow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

token = open('token.txt').read().strip()

r = requests.post(
    "https://kolkrabbi.heroku.com/apps/c0ac59e0-1586-49e4-b326-9ddfe8c6656f/github/push",
    headers={"authorization": f"Bearer {token}"},
    json={"branch": "master"},
)
logger.info(
    "Promotion request sent: %s",
    r.text,
)

with open('promotion.json', 'w') as fh:
    fh.write(r.text)

follow()
