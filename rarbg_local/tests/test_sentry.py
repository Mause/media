from typing import cast

import sentry_sdk
from sentry_sdk.integrations.statsig import StatsigIntegration
from sentry_sdk.types import Event
from statsig import StatsigOptions, StatsigUser, statsig


def test_sentry_config() -> None:
    events: list[Event] = []
    sentry_sdk.init(
        spotlight=True,
        integrations=[StatsigIntegration()],
        before_send=lambda event, hint: events.append(event),
    )

    client = sentry_sdk.get_client()

    try:
        assert client.get_integration(StatsigIntegration)

        statsig.initialize('server-secret-key', StatsigOptions(local_mode=True))  #
        statsig.check_gate(StatsigUser("my-user-id"), "my-feature-gate")
        sentry_sdk.capture_exception(Exception("Something went wrong!"))
    finally:
        client.close()

    assert events
    assert len(events) == 1
    event = cast(Event, events[0])
    values = cast(list[dict], event['contexts']['flags']['values'])
    assert 'my-feature-gate' in {flag['flag'] for flag in values}
