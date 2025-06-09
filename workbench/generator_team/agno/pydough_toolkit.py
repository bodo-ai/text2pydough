# pydough_tools.py
from typing import List
from pathlib import Path

import sqlite3          # swap this for psycopg2, duckdb_engine, etc.
import pandas as pd
from pydough import to_df
from agno.tools import Toolkit            # <- no FunctionTool needed

class PyDoughExecutionToolkit(Toolkit):
    """
    Run PyDough expressions against the configured database and
    return the first *n* rows as JSON for the LLM to reason on.
    """

    def __init__(self, db_url: str | Path, max_rows: int = 20, **kwargs):
        self.db_url = str(db_url)
        self.max_rows = max_rows
        super().__init__(                # important: list the methods you expose
            name="pydough_tools",
            tools=[self.run_pydough_query],
            **kwargs
        )

    # ---------- the single tool ----------
    def run_pydough_query(self, expression: str) -> str:
        """
        Args:
            expression: PyDough DSL string, e.g.
                        "Orders.CALCULATE(total=COUNT(*))\
                        .FILTER(order_date.year == 2024)"
        Returns:
            JSON rows (max `max_rows`).
        """
        print("Running tool!..")
        with sqlite3.connect(self.db_url) as conn:
            df: pd.DataFrame = to_df(expression, conn=conn)

        return df.head(self.max_rows).to_json(orient="records")
