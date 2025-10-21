from functools import wraps

from sentry_sdk.feature_flags import add_feature_flag
from sentry_sdk.integrations import Integration, _check_minimum_version
from sentry_sdk.utils import parse_version
from statsig_python_core import (
    FeatureGateEvaluationOptions,
    Statsig,
    StatsigBasePy,
    StatsigUser,
)
from statsig_python_core.version import __version__ as STATSIG_VERSION


class StatsigIntegration(Integration):
    identifier = "statsig"

    @staticmethod
    def setup_once() -> None:
        version = parse_version(STATSIG_VERSION)
        _check_minimum_version(StatsigIntegration, version, "statsig")

        # Wrap and patch evaluation method(s) in the statsig module
        old_check_gate = Statsig.check_gate

        @wraps(old_check_gate)
        def sentry_check_gate(
            self: StatsigBasePy,
            user: StatsigUser,
            gate: str,
            options: FeatureGateEvaluationOptions | None = None,
        ) -> bool:
            enabled = old_check_gate(self, user, gate, options)
            add_feature_flag(gate, enabled)
            return enabled

        Statsig.check_gate = sentry_check_gate  # type: ignore[method-assign]
