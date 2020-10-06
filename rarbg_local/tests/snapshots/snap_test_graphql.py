# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_main 1'] = {'detail': 'Method Not Allowed'}

snapshots['test_mutation 1'] = {'detail': 'Method Not Allowed'}
