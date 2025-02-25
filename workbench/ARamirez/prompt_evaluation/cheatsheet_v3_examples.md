**PYDOUGH CHEAT SHEET**  

**1. COLLECTIONS & SUB-COLLECTIONS**  

- **Syntax**: Access collections/sub-collections using dot notation.  

- **Examples**:  
  - `People` → Access all records in the 'People' collection.  
  - `People.current_address` → Access current addresses linked to people.  
  - `Packages.customer` → Access customers linked to packages.  

- **Warnings**:  
  - Sub-collections must exist in the metadata graph (e.g., `People.packages` is valid; undefined sub-collections like `People.orders` are invalid).  
  - Avoid reassigning collection names to variables (e.g., `Addresses = 42` breaks subsequent access).  

**2. CALC EXPRESSIONS**  

- **Purpose**: Derive new fields or rename existing ones.  

- **Syntax**:  
  Collection(field=expression, ...)  

- **Examples**:  

  - **Select fields**:  
    People(first_name, last_name)  

  - **Derived fields**:  
    Packages(  
        customer_name=JOIN_STRINGS(' ', customer.first_name, customer.last_name),  
        cost_per_unit=package_cost / quantity  
    )  

- **Rules**:  
  - Use aggregation functions (e.g., SUM, COUNT) for plural sub-collections.  
  - Positional arguments must precede keyword arguments.

**3. FILTERING (WHERE)**  

- **Syntax**: .WHERE(condition)  

- **Examples**:  

  - **Filter people with negative account balance**:  
    People.WHERE(acctbal < 0)  

  - **Filter packages ordered in 2023**:  
    Packages.WHERE(YEAR(order_date) == 2023)  

  - **Filter addresses with occupants**:  
    Addresses.WHERE(HAS(current_occupants))  

- **Warnings**:  
  - Use & (AND), | (OR), ~ (NOT) instead of and, or, not.  
  - Avoid chained comparisons (e.g., replace a < b < c with (a < b) & (b < c)).

**4. SORTING (ORDER_BY)**  

- **Syntax**: .ORDER_BY(field.ASC()/DESC(), ...)  

- **Examples**:  

  - **Alphabetical sort**:  
    People.ORDER_BY(last_name.ASC(), first_name.ASC())  

  - **Most expensive packages first**:  
    Packages.ORDER_BY(package_cost.DESC())  

- **Parameters**:  

  .ASC(na_pos='last') → Sort ascending, nulls last.  

  .DESC(na_pos='first') → Sort descending, nulls first.

**5. SORTING (TOP_K)**  

- **Select top k records.**

- **Syntax:**  
  .TOP_K(k, by=field.DESC())

- **Example:**  
  Top 10 customers by orders count:  
  customers.TOP_K(10, by=COUNT(orders).DESC())

**6. AGGREGATION FUNCTIONS**  

- **COUNT(collection)**: Count non-null records.  
  Example: COUNT(People.packages)  

- **SUM(collection)**: Sum values.  
  Example: SUM(Packages.package_cost)  

- **AVG(collection)**: Average values.  
  Example: AVG(Packages.quantity)  

- **MIN/MAX(collection)**: Min/Max value.  
  Example: MIN(Packages.order_date)  

- **NDISTINCT(collection)**: Distinct count equivalent to COUNT(DISTINCT).  
  Example: NDISTINCT(Addresses.state)  

- **HAS(collection)**: True if ≥1 record exists.  
  Example: HAS(People.packages)

- **HASNOT(collection)**: True if collection is empty.
  Example: HASNOT(orders)

**Rules**: Aggregation functions does not support calling aggregation functions within other aggregation functions. Avoid to do: `SUM(NDISTINCT(nations.customers))`.

**7. grouping (GROUP_BY)**  

- **Purpose**: Group records by keys.  

- **Syntax**: GROUP_BY(Collection, name='group_name', by=(key1, key2))  

- **Good Examples**:  

  - **Group addresses by state and count occupants**:  
    GROUP_BY(Addresses, name='addrs', by=state)(  
        state,  
        total_occupants=COUNT(addrs.current_occupants)  
    )  

  - **Group packages by year/month**:  
    GROUP_BY(Packages, name='packs', by=(YEAR(order_date), MONTH(order_date)))  

- **Bad Examples**:
  - **group by people by their birth year to find the number of people born in each year**: Invalid because the email property is referenced, which is not one of the properties accessible by the group by.
    GROUP_BY(People(birth_year=YEAR(birth_date)), name=\"ppl\", by=birth_year)(
        birth_year,
        email,
        n_people=COUNT(ppl)
    )

  - **Count how many packages were ordered in each year**: Invalid because YEAR(order_date) is not allowed to be used as a group by term (it must be placed in a CALC so it is accessible as a named reference).
    GROUP_BY(Packages, name=\"packs\", by=YEAR(order_date))(
        n_packages=COUNT(packages)
    )

  - **Count how many people live in each state**: Invalid because current_address.state is not allowed to be used as a group by term (it must be placed in a CALC so it is accessible as a named reference).
    GROUP_BY(People, name=\"ppl\", by=current_address.state)(
        n_packages=COUNT(packages)
    )

- **Rules**:  GROUP_BY keys must be scalar fields from the collection. 
You must use Aggregation functions to call plural values inside GROUP_BY. 
Functions, expressions, or transformations (e.g., YEAR(order_date)) cannot be used directly in GROUP_BY Instead, create a named reference using CALC before using it in GROUP_BY.
Directly referencing nested attributes (e.g., table.column.subfield) in GROUP_BY is not allowed. Assign the nested value to a named reference using CALC before grouping.
All terms in a grouping or grouping expression must be singular. Plural expressions, such as lines.part.name, refer to multiple values and cannot be used directly. Instead, aggregate

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

**9. CONTEXTLESS EXPRESSIONS**   

- **Purpose**: Reusable code snippets.  

- **Example**: Define and reuse filters:  

  is_high_value = package_cost > 1000  
  high_value_packages = Packages.WHERE(is_high_value)

**BINARY OPERATORS****Arithmetic**

*   Operators: +, -, \*, /, \*\* (addition, subtraction, multiplication, division, exponentiation).
    
*   Example:Lineitems(value = (extended\_price \* (1 - (discount \*\* 2)) + 1.0) / part.retail\_price)
    
*   Warning: Division by 0 behavior depends on the database.
    

**Comparisons**

*   Operators: <=, <, ==, !=, >, >=.
    
*   Example:Customers(in\_debt = acctbal < 0, is\_european = nation.region.name == "EUROPE")
    
*   Warning: Avoid chained inequalities (e.g., a <= b <= c). Use (a <= b) & (b <= c) or MONOTONIC.
    

**Logical**

*   Operators: & (AND), | (OR), ~ (NOT).
    
*   Example:Customers(is\_eurasian = (nation.region.name == "ASIA") | (nation.region.name == "EUROPE"))
    
*   Warning: Use &, |, ~ instead of Python’s and, or, not.
    

**UNARY OPERATORS****Negation**

*   Operator: - (flips sign).
    
*   Example:Lineitems(lost\_value = extended\_price \* (-discount))
    

**OTHER OPERATORS****Slicing**

*   Syntax: string\[start:stop:step\].
    
*   Example:Customers(country\_code = phone\[:3\])
    
*   Restrictions: step must be 1 or omitted; start/stop non-negative or omitted.
    

**STRING FUNCTIONS**

*   LOWER(s): Converts string to lowercase.Example: LOWER(name) → "apple".
    
*   UPPER(s): Converts string to uppercase.Example: UPPER(name) → "APPLE".
    
*   LENGTH(s): Returns character count.Example: LENGTH(comment) → 42.
    
*   STARTSWITH(s, prefix): Checks prefix match.Example: STARTSWITH(name, "yellow") → True/False.
    
*   ENDSWITH(s, suffix): Checks suffix match.Example: ENDSWITH(name, "chocolate") → True/False.
    
*   CONTAINS(s, substr): Checks substring presence.Example: CONTAINS(name, "green") → True/False.
    
*   LIKE(s, pattern): SQL-style pattern matching (%, \_).Example: LIKE(comment, "%special%") → True/False.
    
*   JOIN\_STRINGS(delim, s1, s2, ...): Joins strings with a delimiter.Example: JOIN\_STRINGS("-", "A", "B") → "A-B".
    

**DATETIME FUNCTIONS**

*   YEAR(dt): Extracts year.Example: YEAR(order\_date) == 1995.
    
*   MONTH(dt): Extracts month (1-12).Example: MONTH(order\_date) >= 6.
    
*   DAY(dt): Extracts day (1-31).Example: DAY(order\_date) == 1.
    
*   HOUR(dt): Extracts hour (0-23).Example: HOUR(order\_date) == 12.
    
*   MINUTE(dt): Extracts minute (0-59).Example: MINUTE(order\_date) == 30.
    
*   SECOND(dt): Extracts second (0-59).Example: SECOND(order\_date) < 30.
    

**CONDITIONAL FUNCTIONS**

*   IFF(cond, a, b): Returns a if cond is True, else b.Example: IFF(acctbal > 0, acctbal, 0).
    
*   ISIN(val, (x, y)): Checks membership in a list.Example: ISIN(size, (10, 11)) → True/False.
    
*   DEFAULT\_TO(a, b): Returns first non-null value.Example: DEFAULT\_TO(tax, 0).
    
*   PRESENT(x): Checks if non-null.Example: PRESENT(tax) → True/False.
    
*   ABSENT(x): Checks if null.Example: ABSENT(tax) → True/False.
    
*   KEEP\_IF(a, cond): Returns a if cond is True, else null.Example: KEEP\_IF(acctbal, acctbal > 0).
    
*   MONOTONIC(a, b, c): Checks ascending order.Example: MONOTONIC(5, part.size, 10) → True/False.
    

**NUMERICAL FUNCTIONS**

*   ABS(x): Absolute value.Example: ABS(-5) → 5.
    
*   ROUND(x, decimals): Rounds to decimals places.Example: ROUND(3.1415, 2) → 3.14.
    
*   POWER(x, exponent): Raises x to a power.Example: POWER(3, 2) → 9.
    
*   SQRT(x): Square root of x.Example: SQRT(16) → 4.
    

**GENERAL NOTES**

*   Use &, |, ~ for logical operations (not and, or, not).
    
*   For chained inequalities, use MONOTONIC or explicit comparisons.
    
*   Aggregation functions convert plural values (e.g., collections) to singular values.
    
**10. EXAMPLE QUERIES**  

* **Top 5 States by Average Occupants:**  

  addr_info = Addresses(n_occupants=COUNT(current_occupants))  
  average_occupants=GROUP_BY(addr_info, name="addrs", by=state)(  
      state,  
      avg_occupants=AVG(addrs.n_occupants)  
  ).TOP_K(5, by=avg_occupants.DESC())  

* **Monthly Trans-Coastal Shipments:**  

  west_coast = (\"CA\", \"OR\", \"WA\")  
  east_coast = (\"NY\", \"NJ\", \"MA\")  
  monthly_shipments= Packages.WHERE(  
      ISIN(customer.current_address.state, west_coast) &  
      ISIN(shipping_address.state, east_coast)  
  )(  
      month=MONTH(order_date),  
      year=YEAR(order_date)  
  )

* **Filter Nations by Name**  
  *Goal: Find nations whose names start with \"A\".*  
  *Code:*  
  nations_startwith = nations(n_name=name, n_comment=comment).WHERE(STARTSWITH(name, 'A'))  
  nations_like = nations(n_name=name, n_comment=comment).WHERE(LIKE(name, 'A%'))  

* **Customers in Debt from Specific Region**  
  *Goal: Identify customers in debt (negative balance) with ≥5 orders, from \"AMERICA\" (excluding Brazil).*  
  *Code:*  
  customer_in_debt = customers(name).WHERE(  
      (acctbal < 0) &  
      (COUNT(orders) >= 5) &  
      (nation.region.name == \"AMERICA\") &  
      (nation.name != \"BRAZIL\")  
  )  

* **Orders per Customer in 1998**  
  *Goal: Count orders per customer in 1998 and sort by activity.*  
  *Code:*  
  customer_order_counts = customers(  
      key, name,  
      num_orders=COUNT(orders.WHERE(YEAR(order_date) == 1998))  
  ).ORDER_BY(num_orders.DESC())  

* **High-Value Customers in Asia**  
  *Goal: Find customers in Asia with total spending > $1000.*  
  *Code:*  
  high_value_customers_in_asia = customers(  
      customer_key=key, customer_name=name,  
      total_spent=SUM(orders.total_price)  
  ).WHERE((total_spent > 1000) & (nation.region.name == \"ASIA\"))  

* **Top 5 Most Profitable Regions**  
  *Goal: Identify regions with highest revenue.*  
  *Code:*  
  selected_regions = nations(  
      region_name=region.name,  
      TOTALREVENUE=SUM(customers.orders.total_price)  
  ).TOP_K(5, TOTALREVENUE.DESC())  

* **Inactive Customers**  
  *Goal: Find customers who never placed orders.*  
  *Code:*  
  customers_without_orders = customers.WHERE(HASNOT(orders))(  
      customer_key=key,  
      customer_name=name  
  )  

* **Customer Activity by Nation**  
  *Goal: Track active/inactive customers per nation.*  
  *Code:*  
  cust_info = customers(is_active=HAS(orders))  
  nation_summary = nations(  
      nation_name=name,  
      total_customers=COUNT(cust_info),  
      active_customers=SUM(cust_info.is_active),  
      inactive_customers=COUNT(cust_info) - SUM(cust_info.is_active)  
  ).ORDER_BY(total_customers.DESC())  

* **High Balance, Low Spending Customers**  
  *Goal: Find top 10% in balance but bottom 25% in orders.*  
  *Code:*  
  customers_in_low_percentiles = customers.WHERE(  
      (PERCENTILE(by=acctbal.DESC()) <= 10) &  
      (PERCENTILE(by=COUNT(orders.key).ASC()) <= 25)  
  )

**GENERAL NOTES**

*   Use &, |, ~ for logical operations (not and, or, not).
    
*   For chained inequalities, use MONOTONIC or explicit comparisons.
    
*   Aggregation functions convert plural values (e.g., collections) to singular values.