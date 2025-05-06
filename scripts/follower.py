#!/usr/bin/env python

import json

import requests


def follow():
    with open('promotion.json') as fh:
        promotion = json.load(fh)

    r = requests.get(promotion['build']['output_stream_url'], stream=True)
    for line in r.raw:
        print(line.decode())


if __name__ == "__main__":
    follow()
