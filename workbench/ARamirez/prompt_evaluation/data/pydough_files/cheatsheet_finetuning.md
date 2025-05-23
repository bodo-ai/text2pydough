### **PYDOUGH CHEAT SHEET SUMMARY**

#### **General Rules**  
1. **HAS Function**: Verify 1-to-N relationships between tables (e.g., `HAS(customers.orders)==1`).  
2. **TOP_K**: Use instead of `ORDER_BY` for selecting top/bottom records.  
3. **SINGULAR Function**: Required when calculations span multiple years without a specified year.  
4. **CALCULATE**:  
   - Only supports singular expressions.  
   - For plural sub-collections, use aggregation functions (e.g., `SUM`, `COUNT`).  
5. **PARTITION**:  
   - Always requires `name` and `by` parameters.  
   - The `by` parameter must be an expression, not a collection or calculation.  
   - Must be used as a method, not on the collection key.  
6. **Avoid Chained Operations**: Use intermediate `CALCULATE` steps for complex expressions.  

---

#### **Key Functions**  
1. **CALCULATE**:  
   - Derives new fields or renames existing ones.  
   - Example:  
     ```  
     People.CALCULATE(first_name=first_name, last_name=last_name)  
     ```  
   - Rules:  
     - Aggregation functions required for plural sub-collections.  
     - New fields are only accessible after `CALCULATE` completes.  

2. **WHERE**:  
   - Filters records based on conditions.  
   - Example:  
     ```  
     People.WHERE(acctbal < 0)  
     ```  
   - Rules:  
     - Use `&` (AND), `|` (OR), `~` (NOT).  

3. **TOP_K**:  
   - Selects top/bottom `k` records.  
   - Example:  
     ```  
     customers.TOP_K(10, by=COUNT(orders).DESC())  
     ```  

4. **Aggregation Functions**:  
   - `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `NDISTINCT`, `MEDIAN`.  
   - Example:  
     ```  
     SUM(Packages.package_cost)  
     ```  

5. **PARTITION**:  
   - Groups records by keys.  
   - Example:  
     ```  
     Addresses.PARTITION(name="states", by=state).CALCULATE(n_people=COUNT(current_occupants))  
     ```  
   - Rules:  
     - Keys must be scalar fields.  
     - Re-access the collection after partitioning to use partitioned data.  

6. **Window Functions**:  
   - `RANKING`, `PERCENTILE`, `RELSUM`, `RELAVG`, `RELCOUNT`, `RELSIZE`.  
   - Example:  
     ```  
     Customers.CALCULATE(r=RANKING(by=acctbal.DESC(), per="nations"))  
     ```  

7. **SINGULAR**:  
   - Ensures data is treated as singular in sub-collection contexts.  
   - Example:  
     ```  
     most_recent_package.SINGULAR().package_cost  
     ```  

---

#### **Operators & Functions**  
1. **Binary Operators**:  
   - Arithmetic: `+`, `-`, `*`, `/`, `**`.  
   - Comparisons: `<=`, `<`, `==`, `!=`, `>`, `>=`.  
   - Logical: `&` (AND), `|` (OR), `~` (NOT).  

2. **String Functions**:  
   - `LOWER`, `UPPER`, `LENGTH`, `STARTSWITH`, `ENDSWITH`, `CONTAINS`, `LIKE`, `JOIN_STRINGS`.  

3. **Datetime Functions**:  
   - `YEAR`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND`.  
   - `DATEDIFF`: Calculates differences between dates.  
   - `DAYOFWEEK`, `DAYNAME`: Returns day of the week.  

4. **Conditional Functions**:  
   - `IFF`, `ISIN`, `DEFAULT_TO`, `KEEP_IF`, `MONOTONIC`.  

5. **Numerical Functions**:  
   - `ABS`, `ROUND`, `POWER`, `SQRT`.  

---

#### **Example Queries**  
1. **Top 5 States by Average Occupants**:  
   ```  
   Addresses.PARTITION(name="states", by=state).CALCULATE(avg_occupants=AVG(n_occupants)).TOP_K(5, by=avg_occupants.DESC())  
   ```  

2. **Monthly Shipments**:  
   ```  
   Packages.CALCULATE(month=MONTH(order_date), year=YEAR(order_date))  
   ```  

3. **High-Value Customers**:  
   ```  
   customers.WHERE(SUM(orders.total_price) > 1000)  
   ```  

---

#### **General Notes**  
- Use `&`, `|`, `~` instead of `and`, `or`, `not`.  
- Avoid chained inequalities; use `MONOTONIC` or explicit comparisons.  
- Aggregation functions convert plural values to singular.  

This summary captures the essential syntax, rules, and examples from the PyDough cheat sheet. For detailed use cases, refer to the original document.