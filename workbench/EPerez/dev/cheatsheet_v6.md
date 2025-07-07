## **PYDOUGH CHEAT SHEET**  
This cheat sheet is a context for learning how to create PyDough code. You must follow all the written rules. Each section represents important features and rules to keep in mind when developing PyDough code. 

### **GENERAL RULES**: 

  - This is NOT SQL, so don't make assumptions about its syntax or behavior.

  - Always use TOP_K instead of ORDER_BY when you need to order but also select a the high, low or an specific "k" number of records.

  - If a query does not specify an specific year, and want that you calculate for all the year, for example “compare year over year”, then the requested calculation must be performed for each year available in TPC: 1995, 1996, 1995 and 1998. You need to use SINGULAR function to call every year in the final result. 

  - If you need to use an attribute of a previous collection, you must have calculated the attribute using CALCULATE.

  - CALCULATE ONLY supports singular expressions. If you need to use plural sub-collections, you MUST use aggregation functions. Plural sub-collections refer to collections that have a one-to-many or many-to-many relationship.
  
  - RANKING is used as a function instead of method.

  - When using functions like TOP_K, ORDER_BY, you must ALWAYS provide an expression, not a collection. Ensure that the correct type of argument is passed. For example, `supp_group.TOP_K(3, total_sales.DESC(na_pos='last')).CALCULATE(supplier_name=supplier_name, total_sales=total_sales)` is invalid because TOP_K expects an expression, not a collection. The “by” parameter must never have collections or subcollections 

  - PARTITION function ALWAYS need 3 parameters `Collection, name and by`. The “by” parameter must never have collections, subcollections or calculations. Any required variable or value must have been previously calculated, because the parameter only accept expressions. PARTITION does not support receiving a collection; you must ALWAYS provide an expression, not a collection. For example, you cannot do: `PARTTION(nations, name="nation", by=(name)).CALCULATE(nation_name=name,top_suppliers=nation.suppliers.TOP_K(3, by=SUM(lines.extended_price).DESC())` because TOP_K returns a collection.

  - PARTITION must always be used as a function. It should only be used as a method when performing calculations with the high-level graph. Never partition by the foreign key or the collection key.
  
  - CALCULATE function ALWAYS needs an expression, not a collection. For example, you cannot do: `nations.CALCULATE(nation_name=name, top_suppliers=suppliers.TOP_K(3, by=SUM(lines.extended_price).DESC())` because TOP_K returns a collection. 

  - In PyDough, complex calculations can often be expressed concisely by combining filters, transformations, and aggregations at the appropriate hierarchical level. Instead of breaking problems into multiple intermediate steps, leverage CALCULATE to directly aggregate values, use WHERE to filter data at the correct scope, and apply functions like SUM or TOP_K at the highest relevant level of analysis. Avoid unnecessary partitioning or intermediate variables unless absolutely required, and focus on composing operations hierarchically to streamline solutions while maintaining clarity and efficiency.

  - PyDough does not support use different childs in operations, for example you cannot do: `total_order_value = SUM(orders.lines.extended_price * (1 - orders.lines.discount))` because you have two different calls. Instead use CALCULATE with a variable, for example: `total_order_value = SUM(orders.lines.CALCULATE(total_order_value = extended_price * (1 - discount)).total_order_value)`.

  - If you need to get the best rankings within a CALCULATE method, you can use the RANKING method instead of TOP_K, and then filter them by the ranking number.

## **1. COLLECTIONS & SUB-COLLECTIONS**  

### **Syntax** 
Access collections/sub-collections using dot notation.  

### **Examples**:  
  - `People` → Access all records in the 'People' collection.  
  - `People.current_address` → Access current addresses linked to people.  
  - `Packages.customer` → Access customers linked to packages.  

## **2. CALCULATE EXPRESSIONS**  

### **Purpose**
Derive new fields, rename existing ones or select specific fields.  

### **Syntax**
Collection.CALCULATE(field=expression, ...)  

### **Examples**:  

  - **Select fields**:  
    ``` 
    People.CALCULATE(first_name=first_name, last_name=last_name)
    ```

  - **Derived fields**:
    ```   
    Packages.CALCULATE(  
        customer_name=JOIN_STRINGS(' ', customer.first_name, customer.last_name),  
        cost_per_unit=package_cost / quantity  
    )
    ```

### **Rules**  
  - Use aggregation functions (e.g., SUM, COUNT) for plural sub-collections.

  - Positional arguments must precede keyword arguments.

  - New fields defined in a CALCULATE do not take effect until after the CALCULATE completes. If you want to access the new field defined, you must use CALCULATE again to reference it.

  - Existing new fields not included in a CALCULATE can still be referenced but are not part of the final result unless included in the last CALCULATE clause.

  - A CALCULATE on the graph itself creates a collection with one row and columns corresponding to the properties inside the CALCULATE. 

## **3. FILTERING (WHERE)**  

### **Syntax** 
.WHERE(condition)  

### **Examples** 

  - **Filter people with negative account balance**:  
    ``` 
    People.WHERE(acctbal < 0)
    ```  

  - **Filter packages ordered in 2023**  
    ``` 
    Packages.WHERE(YEAR(order_date) == 2023)
    ``` 

  - **Filter addresses with occupants** 
    ``` 
    Addresses.WHERE(HAS(current_occupants)==1)
    ```  

### **Rules**  
  - Use & (AND), | (OR), ~ (NOT) instead of and, or, not.  
  - Avoid chained comparisons (e.g., replace a < b < c with (a < b) & (b < c)).

## **4. SORTING (ORDER_BY)**  

### **Syntax** 
  .ORDER_BY(field.ASC()/DESC(), ...)  

### **Parameters**  

  .ASC(na_pos='last') → Sort ascending, nulls last.  

  .DESC(na_pos='first') → Sort descending, nulls first.

### **Examples** 

  - **Alphabetical sort**:
    ``` 
    People.ORDER_BY(last_name.ASC(), first_name.ASC())
    ```

  - **Most expensive packages first**:  
    ``` 
    Packages.ORDER_BY(package_cost.DESC())
    ```  

## **5. SORTING TOP_K(k, by=field.DESC())**  

### **Purpose**
Select top k records.

### **Syntax**  
  .TOP_K(k, by=field.DESC())

### **Example** 
  Top 10 customers by orders count:
  ``` 
  customers.TOP_K(10, by=COUNT(orders).DESC())
  ```

  Top 10 customers by orders count (but also selecting only the name):
  ```   
  customers.CALCULATE(cust_name=name).TOP_K(10, by=COUNT(orders).DESC())
  ```

### **Rules**
- The two parameters are obligatory.

## **6. AGGREGATION FUNCTIONS**  

### **Functions**
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
  Example: HAS(People.packages)==1

- **HASNOT(collection)**: True if collection is empty.
  Example: HASNOT(orders)==1

### **Rules** 
Aggregations Function does not support calling aggregations inside of aggregations

## **7. PARTITION**

### **Purpose**
Group records by keys.  

### **Syntax**
PARTITION(Collection, name='group_name', by=(key1, key2))  

### **Rules**: 
- The `name` argument is a string indicating the name that is to be used when accessing the partitioned data.
- Al the parameters in "by=(key1, key2)" must be use in CALCULATE without using the "name" of the GROUP_BY. As opposed to any other term, which needs the name because that is the context.
- Partition keys must be scalar fields from the collection. 
- You must use Aggregation functions to call plural values inside PARTITION.
- Within a partition, you must use the `name` argument to be able to access any property or subcollections. 

### **Good Examples**  

  - **Group addresses by state and count occupants**: 
    ```  
    PARTITION(Addresses, name='addrs', by=state).CALCULATE(  
        state=state,  
        total_occupants=COUNT(addrs.current_occupants)  
    )
    ```  
    **IMPORTANT**: Look here, where we do not need to use  "addrs.state", we only use "state", because this is in the "by" sentence. 

  - **Group packages by year/month**:  
    ```
    PARTITION(Packages, name='packs', by=(YEAR(order_date), MONTH(order_date)))
    ```  
  - **For every year/month, find all packages that were below the average cost of all packages ordered in that year/month.**:  Notice how `packs` can access `avg_package_cost`, which was defined by its ancestor (at the `PARTITION` level).
    ``` 
    package_info = Packages.CALCULATE(order_year=YEAR(order_date), order_month=MONTH(order_date))
    PARTITION(package_info, name="packs", by=(order_year, order_month)).CALCULATE(
        avg_package_cost=AVG(packs.package_cost)
    ).packs.WHERE(
        package_cost < avg_package_cost
    )
    ```
    **IMPORTANT**: Look here, we can access the collection after the partition using the partition name. This is useful when you need to access a previously defined field or when you need the data to be partitioned.

  - **For every customer, find the percentage of all orders made by current occupants of that city/state made by that specific customer. Includes the first/last name of the person, the city/state they live in, and the percentage.**:  Notice how `addrs` can access `total_packages`, which was defined by its ancestor (at the `PARTITION` level) an notice we can defined more variables with CALCULATE.
    ``` 
      PARTITION(Addresses, name="addrs", by=(city, state)).CALCULATE(
      total_packages=COUNT(addrs.current_occupants.packages)
  ).addrs.CALCULATE(city, state).current_occupants.CALCULATE(
      first_name,
      last_name,
      city=city,
      state=state,
      pct_of_packages=100.0 * COUNT(packages) / total_packages,
  )
    ```

  - **Good Example #1**: Find every unique state.
  ```
  PARTITION(Addresses, name="addrs", by=state).CALCULATE(state)
  ```

  - **Good Example #2**: For every state, count how many addresses are in that state.
  ```
  PARTITION(Addresses, name="addrs", by=state).CALCULATE(
      state,
      n_addr=COUNT(addrs)
  )
  ```

  - **Good Example #3**: For every city/state, count how many people live in that city/state.
  ```
  PARTITION(Addresses, name="addrs", by=(city, state)).CALCULATE(
      state,
      city,
      n_people=COUNT(addrs.current_occupants)
  )
  ```

  - **Good Example #4**: Find the top 5 years with the most people born in that year who have yahoo email accounts, listing the year and the number of people.
  ```
  yahoo_people = People.CALCULATE(
      birth_year=YEAR(birth_date)
  ).WHERE(ENDSWITH(email, "@yahoo.com"))
  PARTITION(yahoo_people, name="yah_ppl", by=birth_year).CALCULATE(
      birth_year,
      n_people=COUNT(yah_ppl)
  ).TOP_K(5, by=n_people.DESC())
  ```

  - **Good Example #5**: Identify the states whose current occupants account for at least 1% of all packages purchased. List the state and the percentage. Notice how `total_packages` is down-streamed from the graph-level `CALCULATE`.
  ```
  GRAPH.CALCULATE(
      total_packages=COUNT(Packages)
  ).PARTITION(Addresses, name="addrs", by=state).CALCULATE(
      state,
      pct_of_packages=100.0 * COUNT(addrs.current_occupants.package) / total_packages
  ).WHERE(pct_of_packages >= 1.0)
  ```

  - **Good Example #6**: Identify which months of the year have numbers of packages shipped in that month that are above the average for all months.
  ```
  pack_info = Packages.CALCULATE(order_month=MONTH(order_date))
  month_info = PARTITION(pack_info, name="packs", by=order_month).CALCULATE(
      n_packages=COUNT(packs)
  )
  GRAPH.CALCULATE(
      avg_packages_per_month=AVG(month_info.n_packages)
  ).PARTITION(pack_info, name="packs", by=order_month).CALCULATE(
      month,
  ).WHERE(COUNT(packs) > avg_packages_per_month)
  ```

  - **Good Example #7**: Find the 10 most frequent combinations of the state that the person lives in and the first letter of that person's name. Notice how `state` can be used as a partition key of `people_info` since it was made available via down-streaming.
  ```
  people_info = Addresses.CALCULATE(state).current_occupants.CALCULATE(
      first_letter=first_name[:1],
  )
  PARTITION(people_info, name="ppl", by=(state, first_letter)).CALCULATE(
      state,
      first_letter,
      n_people=COUNT(ppl),
  ).TOP_K(10, by=n_people.DESC())
  ```

  - **Good Example #8**: Same as good example #8, but written differently so it will include people without a current address (their state is listed as `"N/A"`).
  ```
  people_info = People.CALCULATE(
      state=DEFALT_TO(current_address.state, "N/A"),
      first_letter=first_name[:1],
  )
  PARTITION(people_info, name="ppl", by=(state, first_letter)).CALCULATE(
      state,
      first_letter,
      n_people=COUNT(ppl),
  ).TOP_K(10, by=n_people.DESC())
  ```

  - **Good Example #9**: Partition the current occupants of each address by their birth year and filter to include individuals born in years with at least 10,000 births. For each such person, list their first/last name and the state they live in. This is valid because `state` was down-streamed to `people_info` before it was partitioned, so when `ppl` is accessed, it still has access to `state`.
  ```
  people_info = Addresses.CALCULATE(state).current_occupants.CALCULATE(birth_year=YEAR(birth_date))
  GRAPH.PARTITION(people_info, name="ppl", by=birth_year).WHERE(
      COUNT(p) >= 10000
  ).ppl.CALCULATE(
      first_name,
      last_name,
      state
  )
  ```

  - **Good Example #10**: Find all packages that meet the following criteria: they were ordered in the last year that any package in the database was ordered, their cost was below the average of all packages ever ordered, and the state it was shipped to received at least 10,000 packages that year.
  ```
  package_info = Packages.CALCULATE(
      order_year=YEAR(order_date),
      shipping_state=shipping_address.state
  )
  GRAPH.CALCULATE(
      avg_cost=AVG(package_info.package_cost),
      final_year=MAX(package_info.order_year),
  ).PARTITION(
      package_info.WHERE(order_year == final_year),
      name="packs",
      by=shipping_state
  ).WHERE(
      COUNT(packs) > 10000
  ).packs.WHERE(
      package_cost < avg_cost
  ).CALCULATE(
      shipping_state,
      package_id,
      order_date,
  )
  ```

### **Bad Examples**
  - **Partition people by their birth year to find the number of people born in each year**: Invalid because the email property is referenced, which is not one of the properties accessible by the partition.
    ```
    PARTITION(People(birth_year=YEAR(birth_date)), name=\"ppl\", by=birth_year)(
        birth_year,
        email,
        n_people=COUNT(ppl)
    )
    ```

  - **Count how many packages were ordered in each year**: Invalid because YEAR(order_date) is not allowed to be used as a partition term (it must be placed in a CALCULATE so it is accessible as a named reference).
    ```
    PARTITION(Packages, name=\"packs\", by=YEAR(order_date)).CALCULATE(
        n_packages=COUNT(packages)
    )
    ```

  - **Count how many people live in each state**: Invalid because current_address.state is not allowed to be used as a partition term (it must be placed in a CALCULATE so it is accessible as a named reference).
    ``` 
    PARTITION(People, name=\"ppl\", by=current_address.state).CALCULATE(
        n_packages=COUNT(packages)
    )
    ```
  - **Rank parts within each segment and filter top 20**: Invalid because segment_group.part_name is a plural expression you must use an aggregation function to use plural expression or subcollections.
    ``` 
  top_per_segment = PARTITION(
      segment_part_sales,
      name='segment_group',
      by=segment
  ).CALCULATE(
      segment=segment,
      part_name=segment_group.part_name,
      total_sold=segment_group.total_sold,
      rank=RANKING(by=segment_group.total_sold.DESC(), levels=1)
  ).WHERE(rank <= 20).ORDER_BY(segment.ASC(), total_sold.DESC())
    ```

## **8. WINDOW FUNCTIONS**  

### **RANKING:**  
#### **Syntax**
RANKING(by=field.DESC(), levels=1, allow_ties=False)  

#### **Parameters**
    
- by: Ordering criteria (e.g., acctbal.DESC()).
        
- levels: Hierarchy level (e.g., levels=1 for per-nation ranking). Must be a positive integer.
        
- allow\_ties (default False): Allow tied ranks.
        
- dense (default False): Use dense ranking.
        
#### **Examples**
``` 
# (no levels) rank every customer relative to all other customers
Regions.nations.customers.CALCULATE(r=RANKING(...))

# (levels=1) rank every customer relative to other customers in the same nation
Regions.nations.customers.CALCULATE(r=RANKING(..., levels=1))

# (levels=2) rank every customer relative to other customers in the same region
Regions.nations.customers.CALCULATE(r=RANKING(..., levels=2))

# (levels=3) rank every customer relative to all other customers
Regions.nations.customers.CALCULATE(r=RANKING(..., levels=3))

# Rank customers per-nation by their account balance
# (highest = rank #1, no ties)
Nations.customers.CALCULATE(r = RANKING(by=acctbal.DESC(), levels=1))

# For every customer, finds their most recent order
# (ties allowed)
Customers.orders.WHERE(RANKING(by=order_date.DESC(), levels=1, allow_ties=True) == 1)
```

### **PERCENTILE:**  

#### **Syntax**
PERCENTILE(by=field.ASC(), n_buckets=100)  

#### **Parameters**
    
- by: Ordering criteria.
        
- levels: Hierarchy level.
        
- n\_buckets (default 100): Number of percentile buckets.
        
#### **Example**
``` 
Customers.WHERE(PERCENTILE(by=acctbal.ASC(), n\_buckets=1000) == 1000).
```
  
Filter top 5% by account balance:  
``` 
Customers.WHERE(PERCENTILE(by=acctbal.ASC()) > 95)
```

### **RELSUM:**

The `RELSUM` function returns the sum of multiple rows of a singular expression within the same collection, e.g. the global sum across all rows, or the sum of rows per an ancestor of a sub-collection. The arguments:

#### **Parameters:**
- `expression`: the singular expression to take the sum of across multiple rows.
- `levels` (optional): optional argument (default `None`) for the same `levels` argument as all other window functions.

#### **Examples**
```
# Finds the ratio between each customer's account balance and the global
# sum of all customers' account balances.
Customers.CALCULATE(ratio=acctbal / RELSUM(acctbal))

# Finds the ratio between each customer's account balance and the sum of all
# all customers' account balances within that nation.
Nations.customers.CALCULATE(ratio=acctbal / RELSUM(acctbal, levels=1))
```

### **RELAVG:**

The `RELAVG` function returns the average of multiple rows of a singular expression within the same collection, e.g. the global average across all rows, or the average of rows per an ancestor of a sub-collection. The arguments:

#### **Parameters:**
- `expression`: the singular expression to take the average of across multiple rows.
- `levels` (optional): optional argument (default `None`) for the same `levels` argument as all other window functions.

#### **Examples**
```
# Finds all customers whose account balance is above the global average of all
# customers' account balances.
Customers.WHERE(acctbal > RELAVG(acctbal))

# Finds all customers whose account balance is above the average of all
# ustomers' account balances within that nation.
Nations.customers.WHERE(acctbal > RELAVG(acctbal, levels=1))
```

### **RELCOUNT:**

The `RELCOUNT` function returns the number of non-null records in multiple rows of a singular expression within the same collection, e.g. the count of all non-null rows, or the number of non-null rows per an ancestor of a sub-collection. The arguments:

#### **Parameters:**
- `expression`: the singular expression to count the number of non-null entries across multiple rows.
- `levels` (optional): optional argument (default `None`) for the same `levels` argument as all other window functions.

#### **Examples**
```
# Divides each customer's account balance by the total number of positive
# account balances globally.
Customers.CALCULATE(ratio = acctbal / RELCOUNT(KEEP_IF(acctbal, acctbal > 0.0)))

# Divides each customer's account balance by the total number of positive
# account balances in the same nation.
Nations.customers.CALCULATE(ratio = acctbal / RELCOUNT(KEEP_IF(acctbal, acctbal > 0.0), levels=1))
```

### **RELSIZE:**

The `RELSIZE` function returns the number of total records, either globally or the number of sub-collection rows per some ancestor collection. The arguments:

#### **Parameters:**
- `levels` (optional): optional argument (default `None`) for the same `levels` argument as all other window functions.

#### **Examples**
```
# Divides each customer's account balance by the number of total customers.
Customers.CALCULATE(ratio = acctbal / RELSIZE())

# Divides each customer's account balance by the number of total customers in
# that nation.
Nations.customers.CALCULATE(ratio = acctbal / RELSIZE(levels=1))
```

## **9. CONTEXTLESS EXPRESSIONS**   

### **Purpose**
Reusable code snippets.  

### **Example**
Define and reuse filters:  
  ``` 
  is_high_value = package_cost > 1000  
  high_value_packages = Packages.WHERE(is_high_value)
  ```

## **10. SINGULAR**
### **Purpose**
SINGULAR in PyDough ensures data is explicitly treated as singular in sub-collection contexts, preventing undefined behavior if used correctly.

### **Examples**
```
region_order_values_1996 = regions.CALCULATE(
    region_name=name,
    total_order_value=SUM(nations.customers.orders.WHERE(YEAR(order_date) == 1996).total_price)
).TOP_K(1, by=total_order_value.DESC())

region_order_values_1997 = regions.CALCULATE(
    region_name=name,
    total_order_value=SUM(nations.customers.orders.WHERE(YEAR(order_date) == 1997).total_price)
).TOP_K(1, by=total_order_value.DESC())

result = TPCH.CALCULATE(
    year_1996=region_order_values_1996.SINGULAR().total_order_value,
    year_1997=region_order_values_1997.SINGULAR().total_order_value
)
```

**Good Example #1**: Access the package cost of the most recent package ordered by each person. This is valid because even though `.packages` is plural with regards to `People`, the filter done will ensure that there is only one record for each record of `People`, so `.SINGULAR()` is valid. 

```
most_recent_package = packages.WHERE(
    RANKING(by=order_date.DESC(), levels=1) == 1
).SINGULAR()
People.CALCULATE(
    ssn,
    first_name,
    middle_name,
    last_name,
    most_recent_package_cost=most_recent_package.package_cost
)
```

**Good Example #2**: Access the email of the current occupant of each address that has the name `"John Smith"` (no middle name). This is valid if it is safe to assume that each address only has one current occupant named `"John Smith"` without a middle name.

```
js = current_occupants.WHERE(
    (first_name == "John") &  
    (last_name == "Smith") & 
    ABSENT(middle_name)
).SINGULAR()
Addresses.CALCULATE(
    address_id,
    john_smith_email=DEFAULT_TO(js.email, "NO JOHN SMITH LIVING HERE")
)
```

**Bad Example #1**: This is invalid primarily because of two reasons:
1. Each `Addresses` might have multiple `current_occupants` named `John`, therefore the use of `.SINGULAR()`, though it would not raise an exception, is invalid.
2. Even if, `current_occupants` were non-plural after using `SINGULAR`, `packages` is a plural sub-collection of `current_occupants`, therefore, the data being accessed would be plural with regards to `Addresses`.
```
Addresses.CALCULATE(
    package_id=current_occupants.WHERE(
        first_name == "John"
    ).SINGULAR().packages.package_id
)
```
## **BINARY OPERATORS**

### **Arithmetic**

*   Operators: +, -, \*, /, \*\* (addition, subtraction, multiplication, division, exponentiation).
    
*   Example:Lineitems(value = (extended\_price \* (1 - (discount \*\* 2)) + 1.0) / part.retail\_price)
    
*   Warning: Division by 0 behavior depends on the database.
    

### **Comparisons**

*   Operators: <=, <, ==, !=, >, >=.
    
*   Example:Customers(in\_debt = acctbal < 0, is\_european = nation.region.name == "EUROPE")
    
*   Warning: Avoid chained inequalities (e.g., a <= b <= c). Use (a <= b) & (b <= c) or MONOTONIC.
    

### **Logical**

*   Operators: & (AND), | (OR), ~ (NOT).
    
*   Example:Customers(is\_eurasian = (nation.region.name == "ASIA") | (nation.region.name == "EUROPE"))
    
*   Warning: Use &, |, ~ instead of Python’s and, or, not.
    

## **UNARY OPERATORS****Negation**

*   Operator: - (flips sign).
    
*   Example:Lineitems(lost\_value = extended\_price \* (-discount))
    

## **OTHER OPERATORS**

### **Slicing**

#### Syntax
string\[start:stop:step\].
    
#### Example
Customers(country\_code = phone\[:3\])
    
#### Rules
- Step must be 1 or omitted; start/stop non-negative or omitted.
    

## **STRING FUNCTIONS**

*   LOWER(s): Converts string to lowercase.Example: LOWER(name) → "apple".
    
*   UPPER(s): Converts string to uppercase.Example: UPPER(name) → "APPLE".
    
*   LENGTH(s): Returns character count.Example: LENGTH(comment) → 42.
    
*   STARTSWITH(s, prefix): Checks prefix match.Example: STARTSWITH(name, "yellow") → True/False.
    
*   ENDSWITH(s, suffix): Checks suffix match.Example: ENDSWITH(name, "chocolate") → True/False.
    
*   CONTAINS(s, substr): Checks substring presence.Example: CONTAINS(name, "green") → True/False.
    
*   LIKE(s, pattern): SQL-style pattern matching (%, \_).Example: LIKE(comment, "%special%") → True/False.
    
*   JOIN\_STRINGS(delim, s1, s2, ...): Joins strings with a delimiter.Example: JOIN\_STRINGS("-", "A", "B") → "A-B".
    

## **DATETIME FUNCTIONS**

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
  ``` 
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
  ```

* DATEDIFF: Calling DATEDIFF between 2 timestamps returns the difference in one of the following units of time:     years, months, days, hours, minutes, or seconds.

  - `DATEDIFF("years", x, y)`: Returns the number of full years since `x` that `y` occurred. For example, if `x` is December 31, 2009, and `y` is January 1, 2010, it counts as 1 year apart, even though they are only 1 day apart.
  - `DATEDIFF("months", x, y)`: Returns the number of full months since `x` that `y` occurred. For example, if `x` is January 31, 2014, and `y` is February 1, 2014, it counts as 1 month apart, even though they are only 1 day apart.
  - `DATEDIFF("days", x, y)`: Returns the number of full days since `x` that `y` occurred. For example, if `x` is 11:59 PM on one day, and `y` is 12:01 AM the next day, it counts as 1 day apart, even though they are only 2 minutes apart.
  - `DATEDIFF("hours", x, y)`: Returns the number of full hours since `x` that `y` occurred. For example, if `x` is 6:59 PM and `y` is 7:01 PM on the same day, it counts as 1 hour apart, even though the difference is only 2 minutes.
  - `DATEDIFF("minutes", x, y)`: Returns the number of full minutes since `x` that `y` occurred. For example, if `x` is 7:00 PM and `y` is 7:01 PM, it counts as 1 minute apart, even though the difference is exactly 60 seconds.
  - `DATEDIFF("seconds", x, y)`: Returns the number of full seconds since `x` that `y` occurred. For example, if `x` is at 7:00:01 PM and `y` is at 7:00:02 PM, it counts as 1 second apart.

  - Example:
  ``` 
  # Calculates, for each order, the number of days since January 1st 1992
  # that the order was placed:
  Orders.CALCULATE( 
    days_since=DATEDIFF("days", datetime.date(1992, 1, 1), order_date)
  )
  ```

## **CONDITIONAL FUNCTIONS**

*   IFF(cond, a, b): Returns a if cond is True, else b.Example: IFF(acctbal > 0, acctbal, 0).
    
*   ISIN(val, (x, y)): Checks membership in a list.Example: ISIN(size, (10, 11)) → True/False.
    
*   DEFAULT\_TO(a, b): Returns first non-null value.Example: DEFAULT\_TO(tax, 0).
    
*   PRESENT(x): Checks if non-null.Example: PRESENT(tax) → True/False.
    
*   ABSENT(x): Checks if null.Example: ABSENT(tax) → True/False.
    
*   KEEP\_IF(a, cond): Returns a if cond is True, else null.Example: KEEP\_IF(acctbal, acctbal > 0).
    
*   MONOTONIC(a, b, c): Checks ascending order.Example: MONOTONIC(5, part.size, 10) → True/False.
    

## **NUMERICAL FUNCTIONS**

*   ABS(x): Absolute value.Example: ABS(-5) → 5.
    
*   ROUND(x, decimals): Rounds to decimals places.Example: ROUND(3.1415, 2) → 3.14.
    
*   POWER(x, exponent): Raises x to a power.Example: POWER(3, 2) → 9.
    
*   SQRT(x): Square root of x.Example: SQRT(16) → 4.
    

## **GENERAL NOTES**

*   Use &, |, ~ for logical operations (not and, or, not).
    
*   For chained inequalities, use MONOTONIC or explicit comparisons.
    
*   Aggregation functions convert plural values (e.g., collections) to singular values.
    
## **12. EXAMPLE QUERIES**  

* **Top 5 States by Average Occupants:**  

  addr_info = Addresses.CALCULATE(n_occupants=COUNT(current_occupants))  
  average_occupants=PARTITION(addr_info, name="addrs", by=state).CALCULATE(  
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
  
  Orders.CALCULATE( 
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
  
  Orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))

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

* **Top 5 Most Profitable Nations**  
  *Goal: Identify regions with highest revenue.*  
  *Code:*  
  selected_regions = nations.CALCULATE(  
      region_name=name,  
      Total_revenue=SUM(customers.orders.total_price)  
  ).TOP_K(5, Total_revenue.DESC())  

* **Inactive Customers**  
  *Goal: Find customers who never placed orders.*  
  *Code:*  
  customers_without_orders = customers.WHERE(HASNOT(orders)==1).CALCULATE(  
      customer_key=key,  
      customer_name=name  
  )  

* **Customer Activity by Nation**  
  *Goal: Track active/inactive customers per nation.*  
  *Code:*  
  cust_info = customers.CALCULATE(is_active=HAS(orders)==1)  
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

## **GENERAL NOTES**

*   Use &, |, ~ for logical operations (not and, or, not).
    
*   For chained inequalities, use MONOTONIC or explicit comparisons.
    
*   Aggregation functions convert plural values (e.g., collections) to singular values.