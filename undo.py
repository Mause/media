from io import StringIO
from csv import DictReader, reader
from typing import cast

import pudb
import sqlglot
from sqlglot.dialects import Postgres
from sqlglot.expressions import Copy


def parse_sql_backup(file_path):  # noqa: ANN201
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.startswith('COPY '):
                continue  # Skip lines that do not start with 'COPY '
            clause = cast(Copy, sqlglot.parse_one(line, dialect=Postgres()))
            group = []
            while True:
                next_line = f.readline()
                if not next_line or next_line.startswith('\\'):
                    break
                group.append(next_line)

            yield (
                clause,
                group,
            )  # Yield the COPY clause and the corresponding data group


# Usage

pudb.set_trace()  # Set a breakpoint for debugging
for clause, csv in parse_sql_backup('latest.dump.sql'):
    for line in DictReader(csv, ['a'], delimiter='\t', quoting=3):
        print(line)
    # print(clause)
    # print(csv)
