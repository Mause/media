#!/usr/bin/env python

import json
import logging

import requests

logger = logging.getLogger(__name__)


def follow():
    with open('promotion.json') as fh:
        promotion = json.load(fh)

    r = requests.get(promotion['build']['output_stream_url'], stream=True)
    for line in r.raw:
        logger.info(line.decode())


if __name__ == "__main__":
    follow()
