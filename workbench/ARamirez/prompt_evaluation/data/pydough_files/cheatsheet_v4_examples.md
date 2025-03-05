# PYDOUGH CHEAT SHEET

**1. COLLECTIONS & SUB-COLLECTIONS**  

- **Syntax**: Access collections/sub-collections using dot notation.  

- **Examples**:  
  - `People` → Access all records in the 'People' collection.  
  - `People.current_address` → Access current addresses linked to people.  
  - `Packages.customer` → Access customers linked to packages.  

- **Warnings**:  
  - Sub-collections must exist in the metadata graph (e.g., `People.packages` is valid; undefined sub-collections like `People.orders` are invalid).  
  - Avoid reassigning collection names to variables (e.g., `Addresses = 42` breaks subsequent access).

**2. CALCULATE EXPRESSIONS**  

- **Purpose**: Derive new fields, rename existing ones or select specific fields.  
  The value of one of these terms in a `CALCULATE` must be expressions that are singular with regards to the current context. That can mean:
  - Referencing one of the scalar properties of the current collection.
  - Creating a literal.
  - Referencing a singular expression of a sub-collection of the current collection that is singular with regards to the current collection.
  - Calling a non-aggregation function on more singular expressions.
  - Calling an aggregation function on a plural expression.
- **Syntax**:  
  Collection.CALCULATE(field=expression, ...)  

- **Examples**:  

  - **Select fields**:  
    People.CALCULATE(first_name=first_name, last_name=last_name)  

  - **Derived fields**:  
    Packages.CALCULATE(  
        customer_name=JOIN_STRINGS(' ', customer.first_name, customer.last_name),  
        cost_per_unit=package_cost / quantity  
    )  

**Good Example #1**: For every person, fetch just their first name and last name.

People.CALCULATE(first_name, last_name)

**Good Example #2**: For every package, fetch the package id, the first and last name of the person who ordered it, and the state that it was shipped to. Also, include a field named `secret_key` that is always equal to the string `"alphabet soup"`.

Packages.CALCULATE(
    package_id,
    first_name=customer.first_name,
    last_name=customer.last_name,
    shipping_state=shipping_address.state,
    secret_key="alphabet soup",
)

**Good Example #3**: For every person, find their full name (without the middle name) and count how many packages they purchased.

People.CALCULATE(
    name=JOIN_STRINGS("", first_name, last_name),
    n_packages_ordered=COUNT(packages),
)

**Good Example #4**: For every person, find their full name including the middle name if one exists, as well as their email. Notice that two CALCs are present, but only the terms from the second one are part of the answer.

People.CALCULATE(
    has_middle_name=PRESENT(middle_name)
    full_name_with_middle=JOIN_STRINGS(" ", first_name, middle_name, last_name),
    full_name_without_middle=JOIN_STRINGS(" ", first_name, last_name),
).CALCULATE(
    full_name=IFF(has_middle_name, full_name_with_middle, full_name_without_middle),
    email=email,
)

**Good Example #5**: For every person, find the year of the most recent package they purchased and the year of their first package purchase.

People.CALCULATE(
    most_recent_package_year=YEAR(MAX(packages.order_date)),
    first_ever_package_year=YEAR(MIN(packages.order_date)),
)

**Good Example #6**: Count how many people, packages, and addresses are known in the system.

GRAPH.CALCULATE(
    n_people=COUNT(People),
    n_packages=COUNT(Packages),
    n_addresses=COUNT(Addresses),
)

**Good Example #7**: For each package, list the package id and whether the package was shipped to the current address of the person who ordered it.

Packages.CALCULATE(
    package_id,
    shipped_to_curr_addr=shipping_address.address_id == customer.current_address.address_id
)

**WRONG USES:**
**Bad Example #1**: For each person, list their first name, last name, and phone number. This is invalid because `People` does not have a property named `phone_number`.

People.CALCULATE(first_name, last_name, phone_number)

**Bad Example #2**: For each person, list their combined first & last name followed by their email. This is invalid because a positional argument is included after a keyword argument.

People.CALCULATE(
    full_name=JOIN_STRINGS(" ", first_name, last_name),
    email
)

**Bad Example #3**: For each person, list the address_id of packages they have ordered. This is invalid because `packages` is a plural property of `People`, so its properties cannot be included in a `CALCULATE` term of `People` unless aggregated.

People.CALCULATE(packages.address_id)

**Bad Example #4**: For each person, list their first/last name followed by the concatenated city/state name of their current address. This is invalid because `current_address` is a plural property of `People`, so its properties cannot be included in a `CALCULATE` term of `People` unless aggregated.

People.CALCULATE(
    first_name,
    last_name,
    location=JOIN_STRINGS(", ", current_address.city, current_address.state),
)

**Bad Example #5**: For each address, find whether the state name starts with `"C"`. This is invalid because it calls the builtin Python `.startswith` string method, which is not supported in PyDough (should have instead used a defined PyDough behavior, like the `STARTSWITH` function).

Addresses.CALCULATE(is_c_state=state.startswith("c"))

**Bad Example #6**: For each address, find the state bird of the state it is in. This is invalid because the `state` property of each record of `Addresses` is a scalar expression, not a subcolleciton, so it does not have any properties that can be accessed with `.` syntax.

Addresses.CALCULATE(state_bird=state.bird)

**Bad Example #7**: For each current occupant of each address, list their first name, last name, and city/state they live in. This is invalid because `city` and `state` are not properties of the current collection (`People`, accessed via `current_occupants` of each record of `Addresses`).

Addresses.current_occupants.CALCULATE(first_name, last_name, city, state)

**Bad Example #8**: For each person include their ssn and current address. This is invalid because a collection cannot be a `CALCULATE` term, and `current_address` is a sub-collection property of `People`. Instead, properties of `current_address` can be accessed.

People.CALCULATE(ssn, current_address)

**Bad Example #9**: For each person, list their first name, last name, and the sum of the package costs. This is invalid because `SUM` is an aggregation function and cannot be used in a `CALCULATE` term without specifying the sub-collection it should be applied to.

People.CALCULATE(first_name, last_name, total_cost=SUM(package_cost))

**Bad Example #9**: For each person, list their first name, last name, and the ratio between the cost of all packages they apply ordered and the number of packages they ordered. This is invalid the `total_cost` and `n_packages` are used to define `ratio` in the same `CALCULATE` where they are defined.

People.CALCULATE(
    first_name,
    last_name,
    total_cost=SUM(packages.package_cost),
    n_packages=COUNT(packages),
    ratio=total_cost/n_packages,
)

**Bad Example #10**: Find the total orders placed by region in 1996. This is invalid since `customers` has no field called `orders_1996`. The variable `orders_1996` can only be used to substitute in a contextless expression, not to access a subcollection of a current context. 

orders_1996 = orders.WHERE(YEAR(order_date) == 1996)
total_orders_in_1996 = regions.CALCULATE(
    region_name=name,
    total_orders=COUNT(nations.customers.orders_1996)
).TOP_K(1, by=total_orders.DESC())

**Bad Example #11**: Find the total orders placed and total discount by region in 1996. This is invalid since `customers` has no field called `orders_1996`. The variable `orders_1996` can only be used to substitute in a contextless expression, not to access a subcollection of a current context. 

orders_1996 = orders.WHERE(YEAR(order_date) == 1996)
total_orders_in_1996 = regions.CALCULATE(
    region_name=name,
    total_orders=COUNT(nations.customers.orders_1996)
    total_discount=SUM(nations.customers.orders_1996.lines.discount)
).TOP_K(1, by=total_orders.DESC())

- **Rules**:  
  - Use aggregation functions (e.g., SUM, COUNT) for plural sub-collections.
  - Positional arguments must precede keyword arguments.
  - Terms defined in a CALCULATE do not take effect until after the CALCULATE completes.
  - Existing terms not included in a CALCULATE can still be referenced but are not part of the final result unless included in the last CALCULATE clause.
  - A CALCULATE on the graph itself creates a collection with one row and columns corresponding to the properties inside the CALCULATE.
  - Avoid using collections directly in a CALCULATE term

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
   
- **Params:**
  k= the number of records to return
  by= he field to sort by, with optional sorting order
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

- **NDISTINCT(collection)**: Distinct count.  
  Example: NDISTINCT(Addresses.state)  

- **HAS(collection)**: True if ≥1 record exists.  
  Example: HAS(People.packages)

- **HASNOT(collection)**: True if collection is empty.
  Example: HASNOT(orders)

**Rules**: Aggregations Function does not support calling aggregations inside of aggregations

**7. grouping (GROUP_BY)**  

- **Purpose**: Group records by keys.  

- **Syntax**: GROUP_BY(Collection, name='group_name', by=(key1, key2))  

- **Good Examples**:  

  - **Group addresses by state and count occupants**:  
    GROUP_BY(Addresses, name='addrs', by=state).CALCULATE(  
        state,  
        total_occupants=COUNT(addrs.current_occupants)  
    )  

  - **Group packages by year/month**:  
    GROUP_BY(Packages, name='packs', by=(YEAR(order_date), MONTH(order_date)))  

- **WRONG USES**:
  - **group by people by their birth year to find the number of people born in each year**: Invalid because the email property is referenced, which is not one of the properties accessible by the group by.
     
    GROUP_BY(People(birth_year=YEAR(birth_date)), name=\"ppl\", by=birth_year).CALCULATE(
        birth_year,
        email,
        n_people=COUNT(ppl)
    )
    

  - **Count how many packages were ordered in each year**: Invalid because YEAR(order_date) is not allowed to be used as a group by term (it must be placed in a CALCULATE so it is accessible as a named reference).
     
     GROUP_BY(Packages, name=\"packs\", by=YEAR(order_date)).CALCULATE(
        n_packages=COUNT(packages)
    ) 
    

  - **Count how many people live in each state**: Invalid because current_address.state is not allowed to be used as a group by term (it must be placed in a CALCULATE so it is accessible as a named reference).
     
    GROUP_BY(People, name='ppl', by=current_address.state).CALCULATE(
        n_packages=COUNT(packages)
    ) 

     suppliers_with_brass_parts = GROUP_BY(suppliers, name='supplier_group', by=(name, nation.name)).CALCULATE(
        supplier_name=name,
        nation_name=nation.name,
        total_quantity=SUM(supplier_group.supply_records.part.WHERE(CONTAINS(part_type, 'BRASS')).lines.quantity)
    ).WHERE(total_quantity > 1000) 
    

- **Rules**:  
  - GROUP_BY keys must be scalar fields from the collection. 
  - You must use Aggregation functions to call plural values inside GROUP_BY. 
  - Within a group_by, you must use the `name` argument to be able to access any property or subcollections. 
  - Functions, expressions, or transformations (e.g., YEAR(order_date)) cannot be used directly in GROUP_BY Instead, create a named reference using CALCULATE before using it in GROUP_BY.
  - Directly referencing nested attributes (e.g., table.column.subfield) in GROUP_BY is not allowed. 
  - Assign the nested value to a named reference using CALCULATE before grouping.
  - All terms in a grouping or grouping expression must be singular. Plural expressions, such as lines.part.name, refer to multiple values and cannot be used directly. Instead, aggregate the datas
  
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

  is_february = MONTH(order_date) == 2

  february_value = KEEP_IF(package_cost, is_february)
  aug_packages = packages.CALCULATE(
      is_february=is_february,
      february_value=february_value,
      is_valentines_day=is_february & (DAY(order_date) == 14)
  )
  n_feb_packages = SUM(aug_packages.is_february)
  People.CALCULATE(
      ssn,
      total_february_value=SUM(aug_packages.february_value),
      n_february_packages=n_feb_packages,
      most_expensive_february_package=MAX(aug_packages.february_value),
      pct_valentine=n_feb_packages / SUM(aug_packages.is_valentines_day)
  )
- **Rules**:
  - Only use them in contexts where all referenced fields exist.
  - Use variables only as expression substitutes, not for accessing non-existent subcollections.
  - Each contextless expression should represent a complete calculation.
  - Only use with collections containing all required fields.
  - Using a contextless expression should work the same as writing the code directly in-context.
  - Don't use to define standalone collection operations without proper context.

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

* DATETIME: The DATETIME function is used to build/augment date/timestamp values. The first argument is the base date/timestamp, and it can optionally take in a variable number of modifier arguments.
  
    - The base argument can be one of the following: A string literal indicating that the current timestamp should be built, which has to be one of the following: `now`, `current_date`, `current_timestamp`, `current date`, `current timestamp`. All of these aliases are equivalent, case-insensitive, and ignore leading/trailing whitespace.
    - A column of datetime data.

  The modifier arguments can be the following (all of the options are case-insensitive and ignore leading/trailing/extra whitespace):

  - A string literal in the format `start of <UNIT>` indicating to truncate the datetime value to a certain unit, which can be the following:
    - Years: Supported aliases are "years", "year", and "y".
    - Months: Supported aliases are "months", "month", and "mm".
    - Days: Supported aliases are "days", "day", and "d".
    - Hours: Supported aliases are "hours", "hour", and "h".
    - Minutes: Supported aliases are "minutes", "minute", and "m".
    - Seconds: Supported aliases are "seconds", "second", and "s".

  - A string literal in the form `±<AMT> <UNIT>` indicating to add/subtract a date/time interval to the datetime value. The sign can be `+` or `-`, and if omitted the default is `+`. The amount must be an integer. The unit must be one of the same unit strings allowed for truncation. For example, "Days", "DAYS", and "d" are all treated the same due to case insensitivity.

  If there are multiple modifiers, they operate left-to-right.
  Usage examples:
  
  # Returns the following datetime moments:
  # 1. The current timestamp
  # 2. The start of the current month
  # 3. Exactly 12 hours from now
  # 4. The last day of the previous year
  # 5. The current day, at midnight
  TPCH.CALCULATE(
    ts_1=DATETIME('now'),
    ts_2=DATETIME('NoW', 'start of month'),
    ts_3=DATETIME(' CURRENT_DATE ', '12 hours'),
    ts_4=DATETIME('Current Timestamp', 'start of y', '- 1 D'),
    ts_5=DATETIME('NOW', '  Start  of  Day  '),
  )

  # For each order, truncates the order date to the first day of the year
  Orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))
  

* DATEDIFF: Calling DATEDIFF between 2 timestamps returns the difference in one of the following units of time:     years, months, days, hours, minutes, or seconds.

  - `DATEDIFF("years", x, y)`: Returns the number of full years since `x` that `y` occurred. For example, if `x` is December 31, 2009, and `y` is January 1, 2010, it counts as 1 year apart, even though they are only 1 day apart.
  - `DATEDIFF("months", x, y)`: Returns the number of full months since `x` that `y` occurred. For example, if `x` is January 31, 2014, and `y` is February 1, 2014, it counts as 1 month apart, even though they are only 1 day apart.
  - `DATEDIFF("days", x, y)`: Returns the number of full days since `x` that `y` occurred. For example, if `x` is 11:59 PM on one day, and `y` is 12:01 AM the next day, it counts as 1 day apart, even though they are only 2 minutes apart.
  - `DATEDIFF("hours", x, y)`: Returns the number of full hours since `x` that `y` occurred. For example, if `x` is 6:59 PM and `y` is 7:01 PM on the same day, it counts as 1 hour apart, even though the difference is only 2 minutes.
  - `DATEDIFF("minutes", x, y)`: Returns the number of full minutes since `x` that `y` occurred. For example, if `x` is 7:00 PM and `y` is 7:01 PM, it counts as 1 minute apart, even though the difference is exactly 60 seconds.
  - `DATEDIFF("seconds", x, y)`: Returns the number of full seconds since `x` that `y` occurred. For example, if `x` is at 7:00:01 PM and `y` is at 7:00:02 PM, it counts as 1 second apart.

  - Example:
  
  # Calculates, for each order, the number of days since January 1st 1992 that the order was placed:
  Orders.CALCULATE( 
    days_since=DATEDIFF("days", datetime.date(1992, 1, 1), order_date)
  )
  
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
    
**12. EXAMPLE QUERIES**  

* **Top 5 States by Average Occupants:**  

  addr_info = Addresses.CALCULATE(n_occupants=COUNT(current_occupants))  
  average_occupants=GROUP_BY(addr_info, name="addrs", by=state).CALCULATE(  
      state=state,  
      avg_occupants=AVG(addrs.n_occupants)  
  ).TOP_K(5, by=avg_occupants.DESC())  

* **Monthly Trans-Coastal Shipments:**  

  west_coast = (\"CA\", \"OR\", \"WA\")  
  east_coast = (\"NY\", \"NJ\", \"MA\")  
  monthly_shipments= Packages.WHERE(  
      ISIN(customer.current_address.state, west_coast) &  
      ISIN(shipping_address.state, east_coast)  
  ).CALCULATE(  
      month=MONTH(order_date),  
      year=YEAR(order_date)  
  )

* **Calculates, for each order, the number of days since January 1st 1992**:
  
  orders.CALCULATE( 
   days_since=DATEDIFF("days",datetime.date(1992, 1, 1), order_date)
  )

* **Filter Nations by Name**  
  *Goal: Find nations whose names start with \"A\".*  
  *Code:*  
  nations_startwith = nations.CALCULATE(n_name=name, n_comment=comment).WHERE(STARTSWITH(name, 'A'))  
  nations_like = nations.CALCULATE(n_name=name, n_comment=comment).WHERE(LIKE(name, 'A%'))  

* **Customers in Debt from Specific Region**  
  *Goal: Identify customers in debt (negative balance) with ≥5 orders, from \"AMERICA\" (excluding Brazil).*  
  *Code:*  
  customer_in_debt = customers.CALCULATE(customer_name = name).WHERE(  
      (acctbal < 0) &  
      (COUNT(orders) >= 5) &  
      (nation.region.name == "AMERICA") &  
      (nation.name != "BRAZIL")  
  )

* **For each order, truncates the order date to the first day of the year**:
  
  orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))

* **Orders per Customer in 1998**  
  *Goal: Count orders per customer in 1998 and sort by activity.*  
  *Code:*  
  customer_order_counts = customers.CALCULATE(  
      key=key, 
      name=name,  
      num_orders=COUNT(orders.WHERE(YEAR(order_date) == 1998))  
  ).ORDER_BY(num_orders.DESC())  

* **High-Value Customers in Asia**  
  *Goal: Find customers in Asia with total spending > $1000.*  
  *Code:*  
  high_value_customers_in_asia = customers.CALCULATE(  
      customer_key=key, 
      customer_name=name,  
      total_spent=SUM(orders.total_price)  
  ).WHERE((total_spent > 1000) & (nation.region.name == "ASIA"))  

* **Top 5 Most Profitable Regions**  
  *Goal: Identify regions with highest revenue.*  
  *Code:*  
  selected_regions = nations.CALCULATE(  
      region_name=region.name,  
      Total_revenue=SUM(customers.orders.total_price)  
  ).TOP_K(5, Total_revenue.DESC())  

* **Inactive Customers**  
  *Goal: Find customers who never placed orders.*  
  *Code:*  
  customers_without_orders = customers.WHERE(HASNOT(orders)).CALCULATE(  
      customer_key=key,  
      customer_name=name  
  )  

* **Customer Activity by Nation**  
  *Goal: Track active/inactive customers per nation.*  
  *Code:*  
  cust_info = customers.CALCULATE(is_active=HAS(orders))  
  nation_summary = nations.CALCULATE(  
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

* **Find the parts that contain "STEEL" in their name and show the total available quantity, ordered by the highest available quantity**
  *Goal: Find the parts that contains STEEL in their name.*          
  *Code:*                                                                                                
  availability_parts= supply_records.WHERE(CONTAINS(part.name, "steel")).CALCULATE(part_name= part.name)
  output= PARTITION(availability_parts, name="supp", by=part_name
              ).CALCULATE(
              part_name= part_name,
              total_available= SUM(supp.availqty)
  ).ORDER_BY(total_available.DESC())

* **For customers with at least 5 total transactions, what is their transaction success rate? Return the customer name and success rate, ordered from lowest to highest success rate**
  *Goal: Determine the transaction success rate for customers who have made at least five transactions*          
  *Code:* 
                      
  customer_transactions  = transactions.CALCULATE(cust_id = customer._id, cust_name = customer.name)
  transaction_summary  = PARTITION(customer_transactions, name="t", by=(cust_id, cust_name)
                ).CALCULATE(cust_name, total_tx = COUNT(t.transaction_id), 
                    success_tx = COUNT(t.WHERE(status == "success"))
                )
  transaction_rate  = transaction_summary.CALCULATE(
                    success_rate = success_tx / total_tx * 100
                    ).WHERE(total_tx >= 5)
  output = transaction_rate.CALCULATE(cust_name, success_rate)
  
**IMPORTANT NOTES**

*  Use &, |, ~ for logical operations (not and, or, not).
    
* For chained inequalities, use MONOTONIC or explicit comparisons.
    
* Aggregation functions convert plural values (e.g., collections) to singular values.

* When using functions like TOP_K, ORDER_BY, you must ALWAYS provide an expression, not a collection. Ensure that the correct type of argument is passed. For example, supp_group.TOP_K(3, total_sales.DESC(na_pos='last')).CALCULATE(supplier_name=supplier_name, total_sales=total_sales) is invalid because TOP_K expects an expression, not a collection. The “by” parameter must never have collections or subcollections 

* GROUP_BY function ALWAYS need 3 parameters `Collection, name and by`. The “by” parameter must never have collections, subcollections or calculations. Any required variable or value must have been previously calculated, because the parameter only accept expressions. GROUP_BY does not support receiving a collection; you must ALWAYS provide an expression, not a collection. For example, you cannot do: `PARTTION(nations, name="nation", by=(name)).CALCULATE(region_name=name, top_suppliers=nations.suppliers.TOP_K(3, by=SUM(lines.extended_price).DESC())` because TOP_K returns a collection. 