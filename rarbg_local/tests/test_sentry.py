from ..sentry.statsig import StatsigIntegration


def test_statsig_integration() -> None:
    integration = StatsigIntegration()
    assert integration.name == "StatsigIntegration"
