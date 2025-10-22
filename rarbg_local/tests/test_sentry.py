from ..sentry.statsig import StatsigIntegration


def test_statsig_integration() -> None:
    StatsigIntegration.setup_once()
    assert StatsigIntegration.identifier == "statsig-python-core"
