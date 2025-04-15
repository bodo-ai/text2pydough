**VERY IMPORTANT NOTES**

- Pay special attention to each of these functions and its example of how to use it. 

**16. CONDITIONAL FUNCTIONS**

*   IFF(cond, a, b): Returns a if cond is True, else b.
    *   Example: IFF(acctbal > 0, acctbal, 0).
    
*   ISIN(val, (x, y)): Checks membership in a list.
    *   Example: ISIN(size, (10, 11)) → True/False.
    
*   DEFAULT\_TO(a, b): Returns first non-null value.
    *   Example: DEFAULT\_TO(tax, 0).
    
*   PRESENT(x): Checks if non-null.
    *   Example: PRESENT(tax) → True/False.
    
*   ABSENT(x): Checks if null.
    *   Example: ABSENT(tax) → True/False.
    
*   KEEP\_IF(a, cond): Returns a if cond is True, else null.
    *   Example: KEEP\_IF(acctbal, acctbal > 0).
    
*   MONOTONIC(a, b, c): Checks ascending order.
    *   Example: MONOTONIC(5, part.size, 10) → True/False.