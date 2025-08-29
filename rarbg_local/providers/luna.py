import requests

url = "http://luna-leederville.3cx.com.au:4025/VenueSchedule.json"


def get_venue_schedule():
    response = requests.get(url)
    response.encoding = 'utf-16-le'
    response.raise_for_status()
    return response.json()


breakpoint()
weird = get_venue_schedule()
