from ..sentry.statsig import StatsigIntegration


def test_statsig_integration() -> None:
    integration = StatsigIntegration()
    integration.setup_once()
    assert integration.identifier == "statsig-python-core"
