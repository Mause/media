import requests

res = requests.post(
    'https://media.mause.me/api/monitor/cron',
    auth=('mause', 'mause'),
)
res.raise_for_status()
