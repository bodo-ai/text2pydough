import pandas as pd
from evaluator_agent import compare_df, normalize_table

def test_compare_df():
    # Test case 1: Same data, different column names and order
    print("\nTest Case 1: Same data, different column names and order")
    df1 = pd.DataFrame({
        'market_segment': ['AUTOMOBILE', 'BUILDING', 'FURNITURE', 'HOUSEHOLD', 'MACHINERY'],
        'average_discount': [0.049986, 0.049948, 0.049997, 0.050002, 0.050064]
    })

    df2 = pd.DataFrame({
        'mktsegment': ['MACHINERY', 'HOUSEHOLD', 'FURNITURE', 'AUTOMOBILE', 'BUILDING'],
        'avg_discount': [0.050064, 0.050002, 0.049997, 0.049986, 0.049948]
    })
    
    df2 = pd.DataFrame({
        'market_segment': ['MACHINERY', 'HOUSEHOLD', 'FURNITURE', 'AUTOMOBILE', 'BUILDING'],
        'average_discount': [0.050064, 0.050002, 0.049997, 0.049986, 0.049948]
    })

    result = compare_df(df1, df2, "order_by", "Show average discount by market segment")
    print(f"Comparison result: {result}")
    print("\nDF1 after normalization:")
    print(normalize_table(df1, "order_by", "Show average discount by market segment"))
    print("\nDF2 after normalization:")
    print(normalize_table(df2, "order_by", "Show average discount by market segment"))

    # Test case 2: Different data
    print("\nTest Case 2: Different data")
    df3 = pd.DataFrame({
        'market_segment': ['AUTOMOBILE', 'BUILDING', 'FURNITURE', 'HOUSEHOLD', 'MACHINERY'],
        'average_discount': [0.049986, 0.049948, 0.049997, 0.050002, 0.050064]
    })

    df4 = pd.DataFrame({
        'mktsegment': ['MACHINERY', 'HOUSEHOLD', 'FURNITURE', 'AUTOMOBILE', 'BUILDING'],
        'avg_discount': [0.050064, 0.050002, 0.049997, 0.049986, 0.049947]  # Slightly different value
    })

    result = compare_df(df3, df4, "order_by", "Show average discount by market segment")
    print(f"Comparison result: {result}")

    # Test case 3: Different shapes
    print("\nTest Case 3: Different shapes")
    df5 = pd.DataFrame({
        'market_segment': ['AUTOMOBILE', 'BUILDING', 'FURNITURE'],
        'average_discount': [0.049986, 0.049948, 0.049997]
    })

    result = compare_df(df1, df5, "order_by", "Show average discount by market segment")
    print(f"Comparison result: {result}")

    # Test case 4: With NaN values
    print("\nTest Case 4: With NaN values")
    df6 = pd.DataFrame({
        'market_segment': ['AUTOMOBILE', 'BUILDING', 'FURNITURE', 'HOUSEHOLD', 'MACHINERY'],
        'average_discount': [0.049986, 0.049948, 0.049997, None, 0.050064]
    })

    df7 = pd.DataFrame({
        'mktsegment': ['MACHINERY', 'HOUSEHOLD', 'FURNITURE', 'AUTOMOBILE', 'BUILDING'],
        'avg_discount': [0.050064, None, 0.049997, 0.049986, 0.049948]
    })

    result = compare_df(df6, df7, "order_by", "Show average discount by market segment")
    print(f"Comparison result: {result}")

if __name__ == "__main__":
    test_compare_df() 