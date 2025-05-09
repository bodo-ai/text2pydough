**VERY IMPORTANT NOTES:

1. Ensure `levels` ≤ depth of ancestry (e.g., `Customers` have no ancestors beyond their direct parent).  
2. Always specify `by` to avoid undefined behavior.  
3. Use `allow_ties=True` when duplicates are expected (e.g., dates).  

**8. WINDOW FUNCTIONS**  

- **RANKING:**  
  - **Syntax**: RANKING(by=field.DESC(), levels=1, allow_ties=False)  
  - *   Parameters:
    
    *   by: Ordering criteria (e.g., acctbal.DESC()).
        
    *   levels: Hierarchy level (e.g., levels=1 for per-nation ranking).
        
    *   allow\_ties (default False): Allow tied ranks.
        
    *   dense (default False): Use dense ranking.
        
  - *   Example:Nations.customers(r = RANKING(by=acctbal.DESC(), levels=1))

  - **Example**: Rank customers by balance per nation:  
    Customers(r=RANKING(by=acctbal.DESC(), levels=1))  

- **PERCENTILE:**  

  - **Syntax**: PERCENTILE(by=field.ASC(), n_buckets=100)  
  - *   Parameters:
    
    *   by: Ordering criteria.
        
    *   levels: Hierarchy level.
        
    *   n\_buckets (default 100): Number of percentile buckets.
        
  - *   Example:Customers.WHERE(PERCENTILE(by=acctbal.ASC(), n\_buckets=1000) == 1000).
  
  - **Example**: Filter top 5% by account balance:  
    Customers.WHERE(PERCENTILE(by=acctbal.ASC()) > 95)

 ## **Best Practices**  
 1. **Pre-Sort Data**: Use `CALCULATE` to precompute sort keys for clarity.  
   ```  
   ranked = Customers.CALCULATE(balance_rank=RANKING(by=acctbal.DESC()))  
   ```  
 2. **Validate Levels**: Check ancestry hierarchy before using `levels`.  
 3. **Test Edge Cases**: Verify ties and bucket boundaries with sample data.