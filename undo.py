import logging
from collections.abc import Generator
from csv import DictReader
from typing import cast

import sqlglot
from rich.logging import RichHandler
from sqlglot.dialects import Postgres
from sqlglot.expressions import Copy

logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])

dialect = Postgres()
logger = logging.getLogger(__name__)


def parse_sql_backup(file_path: str) -> Generator[tuple[Copy, list[str]]]:
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            if not line.startswith('COPY '):
                continue  # Skip lines that do not start with 'COPY '
            clause = cast(Copy, sqlglot.parse_one(line, dialect))
            group = []
            while True:
                next_line = f.readline()
                if not next_line or next_line.startswith('\\'):
                    break
                group.append(next_line)

            yield (clause, group)


for clause, csv in parse_sql_backup('latest.dump.sql'):
    table = clause.this.this.name
    columns = [expr.name for expr in clause.this.expressions]
    logger.info(
        '%s: %s',
        table,
        [line for line in DictReader(csv, columns, delimiter='\t', quoting=3)],
    )
