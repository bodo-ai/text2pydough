# Ensure pandas is available; otherwise provide a clear error message.
try:
    import pandas as pd
except ModuleNotFoundError as exc:
    raise SystemExit(
        "The 'pandas' package is required to run this test script. Install it via 'pip install pandas'."
    ) from exc

# Import the compare_df function from the project with a robust fallback
try:
    from .eval import compare_df  # When executed via `python -m` inside the package
except ImportError:
    # Stand-alone execution: add the current directory to sys.path and import directly
    import os
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from eval import compare_df

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
    # 9. Numeric data represented as strings vs integers ---------------------------------
    (
        pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
        pd.DataFrame({"a": ["1", "2", "3"], "b": ["4", "5", "6"]}),
        True,
    ),
    # 10. Datetime objects vs ISO-formatted strings ---------------------------------------
    (
        pd.DataFrame({"date": [pd.Timestamp("2021-01-01"), pd.Timestamp("2021-01-02")]}),
        pd.DataFrame({"date": ["2021-01-01", "2021-01-02"]}),
        True,
    ),
    # 11. Boolean vs. Integer equivalence -------------------------------------------
    (
        pd.DataFrame({"col_bool": [True, False, True]}),
        pd.DataFrame({"col_int": [1, 0, 1]}),
        True,
    ),
    # 12. Mixed numeric representations (string/int/float) -------------------------
    # Gold is object dtype due to mix, Gen is float dtype
    (
        pd.DataFrame({"mix_num": ["10", 20.0, "30.0"]}),
        pd.DataFrame({"mix_num": [10.0, 20.0, 30.0]}),
        True,
    ),
    # 13. Numeric strings with leading zeros vs. integers ---------------------------
    # Gold is object dtype, Gen is int dtype
    (
        pd.DataFrame({"leading_zero_str": ["01", "007", "02.0"]}),
        pd.DataFrame({"numeric_val": [1, 7, 2.0]}),
        True,
    ),
    # 14. Both DataFrames empty (0x0) -----------------------------------------------
    (
        pd.DataFrame(), 
        pd.DataFrame(), 
        True
    ),
    # 15. df_gold empty (0x0), df_gen not (1x1) -------------------------------------
    (
        pd.DataFrame(), 
        pd.DataFrame({"a": [1]}), 
        False
    ),
    # 16. df_gold Rx0, df_gen Rx0 (e.g., 2x0) ---------------------------------------
    (
        pd.DataFrame(index=range(2)), # Creates a 2x0 DataFrame
        pd.DataFrame(index=range(2)), # Creates a 2x0 DataFrame
        True
    ),
    # 17. df_gold Rx0, df_gen Sx0 (R != S) ------------------------------------------
    (
        pd.DataFrame(index=range(2)), # 2x0 DataFrame
        pd.DataFrame(index=range(3)), # 3x0 DataFrame
        False
    ),
    # 18. df_gen has more rows than df_gold, content matches for df_gold rows -------
    # Tests if compare_df correctly identifies df_gold as a subset of df_gen row-wise for matched columns
    (
        pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}),
        pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}),
        True,
    ),
    # 19. Column name case insensitivity (content matches) ---------------------------
    # secondary_check should match by content, ignoring case differences in names
    (
        pd.DataFrame({"COL_A": [10, 20], "col_b": [30, 40]}),
        pd.DataFrame({"col_a": [10, 20], "COL_B": [30, 40]}),
        True,
    ),
    # 20. Duplicate column content in df_gen (unique in df_gold) -------------------
    # _remove_duplicate_columns in secondary_check should handle extra identical columns in df_gen
    (
        pd.DataFrame({"key": ["k1", "k2"], "val": [100, 200]}),
        pd.DataFrame({"key_col": ["k1", "k2"], "val_col": [100, 200], "val_col_dup": [100, 200]}),
        True,
    ),
]

# Add better display options for prettier DataFrame output
pd.set_option('display.width', 120)
pd.set_option('display.max_columns', None)

def run_tests() -> None:
    """Execute each test case sequentially and report results."""

    failures = 0

    # Using generic placeholders for the parameters not under test.
    query_category = "select"
    question = "dummy question"

    for idx, (df_gold, df_gen, expected) in enumerate(TEST_CASES, start=1):
        # Pretty-print the input DataFrames for easier visual inspection
        print(f"\n======= Test Case {idx} =======")
        print("Gold DataFrame:")
        print(df_gold.to_string(index=False))
        print("\nGenerated DataFrame:")
        print(df_gen.to_string(index=False))
        print("==============================\n")
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