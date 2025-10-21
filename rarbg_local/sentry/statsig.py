from functools import wraps
from typing import TYPE_CHECKING

from sentry_sdk.feature_flags import add_feature_flag
from sentry_sdk.integrations import Integration, _check_minimum_version
from sentry_sdk.utils import parse_version
from statsig_python_core import statsig as statsig_module
from statsig_python_core.version import __version__ as STATSIG_VERSION

if TYPE_CHECKING:
    pass


class StatsigIntegration(Integration):
    identifier = "statsig"

    @staticmethod
    def setup_once():
        # type: () -> None
        version = parse_version(STATSIG_VERSION)
        _check_minimum_version(StatsigIntegration, version, "statsig")

        # Wrap and patch evaluation method(s) in the statsig module
        old_check_gate = statsig_module.Statsig.check_gate

        @wraps(old_check_gate)
        def sentry_check_gate(
            user: statsig_module.StatsigUser, gate: str, *args, **kwargs
        ):
            enabled = old_check_gate(user, gate, *args, **kwargs)
            add_feature_flag(gate, enabled)
            return enabled

        statsig_module.Statsig.check_gate = sentry_check_gate
