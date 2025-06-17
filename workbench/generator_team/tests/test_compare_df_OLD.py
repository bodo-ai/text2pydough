# Ensure pandas is available; otherwise provide a clear error message.
try:
    import pandas as pd
except ModuleNotFoundError as exc:
    raise SystemExit(
        "The 'pandas' package is required to run this test script. Install it via 'pip install pandas'."
    ) from exc

# Import the compare_df function from the project
from generator_team.agents.evaluation.function.eval import compare_df

# This script can be executed directly (e.g., `python test_compare_df.py`) to run the
# embedded test cases without relying on the `pytest` framework.  Each case will
# raise an `AssertionError` with a helpful message if it fails; otherwise, a short
# success summary will be printed at the end.

# ---------------------------------------------------------------------------------
# Test cases: list of tuples (df_gold, df_gen, expected_boolean)
# ---------------------------------------------------------------------------------

TEST_CASES = [
    # 1. Identical DataFrames -------------------------------------------------------
    (
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
        True,
    ),
    # 2. Column order differs -------------------------------------------------------
    (
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
        pd.DataFrame({"b": [4, 5, 6], "a": [1, 2, 3]}),
        True,
    ),
    # 3. Numeric tolerance check (float/int mix) -----------------------------------
    (
        pd.DataFrame({"a": [1.0000001, 2.0000001], "b": [3.0, 4.0]}),
        pd.DataFrame({"a": [1.0, 2.0], "b": [3, 4]}),
        True,
    ),
    # 4. Row order differs ----------------------------------------------------------
    (
        pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}),
        pd.DataFrame({"a": [3, 1, 2], "b": ["z", "x", "y"]}),
        True,
    ),
    # 5. NaN / None / pd.NA equivalence --------------------------------------------
    (
        pd.DataFrame({"a": [1, None, 3], "b": [pd.NA, 5, 6]}),
        pd.DataFrame({"a": [1, pd.NA, 3], "b": [None, 5, 6]}),
        True,
    ),
    # 6. Extra column in generated df should still match ----------------------------
    (
        pd.DataFrame({"a": [1, 2], "b": [3, 4]}),
        pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [9, 9]}),
        True,
    ),
    # 7. Duplicate columns handled by deduplication --------------------------------
    (
        pd.DataFrame([[1, 1, 3], [2, 2, 4]], columns=["a", "a", "b"]),
        pd.DataFrame({"b": [3, 4], "a": [1, 2]}),
        True,
    ),
    # 8. Different data not equal ---------------------------------------------------
    (
        pd.DataFrame({"a": [1, 2, 3]}),
        pd.DataFrame({"a": [4, 5, 6]}),
        False,
    ),
]


def run_tests() -> None:
    """Execute each test case sequentially and report results."""

    failures = 0

    # Using generic placeholders for the parameters not under test.
    query_category = "select"
    question = "dummy question"

    for idx, (df_gold, df_gen, expected) in enumerate(TEST_CASES, start=1):
        result = compare_df(df_gold, df_gen, query_category=query_category, question=question)

        if result is expected:
            print(f"✅  Case {idx}: PASSED")
        else:
            failures += 1
            print(
                f"❌  Case {idx}: FAILED — Expected {expected} but got {result}")

    if failures == 0:
        print("\nAll tests passed! 🎉")
    else:
        raise AssertionError(f"{failures} test case(s) failed.")


# ---------------------------------------------------------------------------------
# Entry-point guard ----------------------------------------------------------------
# ---------------------------------------------------------------------------------

if __name__ == "__main__":
    run_tests() 