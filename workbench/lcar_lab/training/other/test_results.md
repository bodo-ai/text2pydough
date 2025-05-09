# Pydough Code Documentation Retrieval Results


## Example 1

### Question
```
Provide a summary pricing report for all line items shipped as of September 2nd of 1998. The summary should list totals for extended price, discounted extended price, discounted extended price plus tax, average quantity, average extended price, average discount, and number of lines, all broken down by the return flag & line status. This is also known as TPC-H query #1.
```

### Pydough Code
```python
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
result = partitioned_lines(
    L_RETURNFLAG=return_flag,
    L_LINESTATUS=status,
    SUM_QTY=SUM(l.quantity),
    SUM_BASE_PRICE=SUM(l.extended_price),
    SUM_DISC_PRICE=SUM(disc_price),
    SUM_CHARGE=SUM(charge),
    AVG_QTY=AVG(l.quantity),
    AVG_PRICE=AVG(l.extended_price),
    AVG_DISC=AVG(l.discount),
    COUNT_ORDER=COUNT(l),
).ORDER_BY(return_flag.ASC(), status.ASC())
```

### Extracted Key Terms
selected_lines = lines, SORTING, AVG_QTY=AVG(l, AVG_DISC=AVG(l, SUM_BASE_PRICE=SUM(l, SUM_QTY=SUM(l, ORDER_BY, COUNT, WHERE, charge = disc_price * (1 + l, AVG, ), PARTITION, disc_price = l, SUM, ASC, AVG_PRICE=AVG(l

### Documentation Retrieval Results

#### Generated Documentation
# Explanation of Pydough Code for TPC-H Query #1

Based on the provided documentation, I'll explain the Pydough code that generates a summary pricing report for line items shipped as of September 2nd, 1998.

## 1. Pydough-specific Functions and Patterns

The code uses several key Pydough functions and patterns:

### WHERE Function
```python
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
```
This filters the `lines` collection to only include records where the `ship_date` is on or before September 2nd, 1998 [1abb098].

### PARTITION Function
```python
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
```
This groups the filtered lines by `return_flag` and `status`, creating partitions that can be aggregated [1abb098].

### Aggregation Functions
The code uses several aggregation functions:
- `SUM()` - Calculates the sum of values [1abb098]
- `AVG()` - Calculates the average of values [1abb098]
- `COUNT()` - Counts the number of records [1abb098]

### ORDER_BY Function
```python
.ORDER_BY(return_flag.ASC(), status.ASC())
```
This sorts the results by `return_flag` and `status` in ascending order [1abb098].

## 2. Data Flow and Transformations

The data flow follows these steps:

1. **Define calculated fields**: First, two expressions are defined for later use:
   ```python
   disc_price = l.extended_price * (1 - l.discount)
   charge = disc_price * (1 + l.tax)
   ```
   These are contextless expressions that will be used in aggregations [1abb098].

2. **Filter data**: The code filters line items to only those shipped on or before September 2nd, 1998:
   ```python
   selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
   ```

3. **Partition data**: The filtered data is then grouped by return flag and line status:
   ```python
   partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
   ```

4. **Calculate aggregations**: For each partition, various aggregations are calculated:
   ```python
   result = partitioned_lines(
       L_RETURNFLAG=return_flag,
       L_LINESTATUS=status,
       SUM_QTY=SUM(l.quantity),
       SUM_BASE_PRICE=SUM(l.extended_price),
       SUM_DISC_PRICE=SUM(disc_price),
       SUM_CHARGE=SUM(charge),
       AVG_QTY=AVG(l.quantity),
       AVG_PRICE=AVG(l.extended_price),
       AVG_DISC=AVG(l.discount),
       COUNT_ORDER=COUNT(l),
   )
   ```

5. **Sort results**: Finally, the results are sorted by return flag and line status:
   ```python
   .ORDER_BY(return_flag.ASC(), status.ASC())
   ```

## 3. Pydough Best Practices Demonstrated

The code demonstrates several Pydough best practices:

1. **Contextless expressions**: Defining `disc_price` and `charge` as contextless expressions allows them to be reused in different contexts [23d4d72].

2. **Naming partitions**: Using `name="l"` in the PARTITION function creates a clear reference for the partitioned data [1abb098].

3. **Clear column naming**: The output columns are given descriptive names that match the requirements of the query [1abb098].

4. **Efficient data flow**: The code follows a logical flow of filtering, partitioning, aggregating, and sorting [1abb098].

## 4. How This Code Follows Pydough Conventions

The code follows Pydough conventions in several ways:

1. **Method chaining**: Operations are chained together in a readable sequence [1abb098].

2. **Contextual references**: The code uses the partition name `l` to reference fields within the partition context [1abb098].

3. **Expressive syntax**: The code uses expressive syntax like `return_flag.ASC()` to indicate sorting direction [1abb098].

4. **Declarative style**: The code describes what to compute rather than how to compute it [1abb098].

## 5. How the Code Addresses the Original Question

The code directly addresses the requirements in the original question:

1. **Filtering by date**: It filters line items shipped as of September 2nd, 1998 [1abb098].

2. **Grouping by return flag and line status**: It partitions data by these two fields [1abb098].

3. **Calculating required metrics**:
   - Sum of quantity (`SUM_QTY`)
   - Sum of extended price (`SUM_BASE_PRICE`)
   - Sum of discounted extended price (`SUM_DISC_PRICE`)
   - Sum of discounted extended price plus tax (`SUM_CHARGE`)
   - Average quantity (`AVG_QTY`)
   - Average extended price (`AVG_PRICE`)
   - Average discount (`AVG_DISC`)
   - Count of lines (`COUNT_ORDER`) [1abb098]

4. **Sorting results**: It sorts by return flag and line status as required [1abb098].

## Comparison with SQL

The Pydough code is a more concise and readable alternative to the equivalent SQL query shown in the documentation [1abb098]:

```sql
select
    l_returnflag,
    l_linestatus,
    sum(l_quantity) as sum_qty,
    sum(l_extendedprice) as sum_base_price,
    sum(l_extendedprice * (1 - l_discount)) as sum_disc_price,
    sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,
    avg(l_quantity) as avg_qty,
    avg(l_extendedprice) as avg_price,
    avg(l_discount) as avg_disc,
    count(*) as count_order
from
    lineitem
where
    l_shipdate <= date '1998-12-01' - interval '90' day
group by
    l_returnflag,
    l_linestatus
order by
    l_returnflag,
    l_linestatus
```

The Pydough version makes the calculations more explicit by defining intermediate expressions (`disc_price` and `charge`), which improves readability and maintainability.

#### Full RAG Results
```json
{'generated_answer': '# Explanation of Pydough Code for TPC-H Query #1\n\nBased on the provided documentation, I\'ll explain the Pydough code that generates a summary pricing report for line items shipped as of September 2nd, 1998.\n\n## 1. Pydough-specific Functions and Patterns\n\nThe code uses several key Pydough functions and patterns:\n\n### WHERE Function\n```python\nselected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\n```\nThis filters the `lines` collection to only include records where the `ship_date` is on or before September 2nd, 1998 [1abb098].\n\n### PARTITION Function\n```python\npartitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))\n```\nThis groups the filtered lines by `return_flag` and `status`, creating partitions that can be aggregated [1abb098].\n\n### Aggregation Functions\nThe code uses several aggregation functions:\n- `SUM()` - Calculates the sum of values [1abb098]\n- `AVG()` - Calculates the average of values [1abb098]\n- `COUNT()` - Counts the number of records [1abb098]\n\n### ORDER_BY Function\n```python\n.ORDER_BY(return_flag.ASC(), status.ASC())\n```\nThis sorts the results by `return_flag` and `status` in ascending order [1abb098].\n\n## 2. Data Flow and Transformations\n\nThe data flow follows these steps:\n\n1. **Define calculated fields**: First, two expressions are defined for later use:\n   ```python\n   disc_price = l.extended_price * (1 - l.discount)\n   charge = disc_price * (1 + l.tax)\n   ```\n   These are contextless expressions that will be used in aggregations [1abb098].\n\n2. **Filter data**: The code filters line items to only those shipped on or before September 2nd, 1998:\n   ```python\n   selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\n   ```\n\n3. **Partition data**: The filtered data is then grouped by return flag and line status:\n   ```python\n   partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))\n   ```\n\n4. **Calculate aggregations**: For each partition, various aggregations are calculated:\n   ```python\n   result = partitioned_lines(\n       L_RETURNFLAG=return_flag,\n       L_LINESTATUS=status,\n       SUM_QTY=SUM(l.quantity),\n       SUM_BASE_PRICE=SUM(l.extended_price),\n       SUM_DISC_PRICE=SUM(disc_price),\n       SUM_CHARGE=SUM(charge),\n       AVG_QTY=AVG(l.quantity),\n       AVG_PRICE=AVG(l.extended_price),\n       AVG_DISC=AVG(l.discount),\n       COUNT_ORDER=COUNT(l),\n   )\n   ```\n\n5. **Sort results**: Finally, the results are sorted by return flag and line status:\n   ```python\n   .ORDER_BY(return_flag.ASC(), status.ASC())\n   ```\n\n## 3. Pydough Best Practices Demonstrated\n\nThe code demonstrates several Pydough best practices:\n\n1. **Contextless expressions**: Defining `disc_price` and `charge` as contextless expressions allows them to be reused in different contexts [23d4d72].\n\n2. **Naming partitions**: Using `name="l"` in the PARTITION function creates a clear reference for the partitioned data [1abb098].\n\n3. **Clear column naming**: The output columns are given descriptive names that match the requirements of the query [1abb098].\n\n4. **Efficient data flow**: The code follows a logical flow of filtering, partitioning, aggregating, and sorting [1abb098].\n\n## 4. How This Code Follows Pydough Conventions\n\nThe code follows Pydough conventions in several ways:\n\n1. **Method chaining**: Operations are chained together in a readable sequence [1abb098].\n\n2. **Contextual references**: The code uses the partition name `l` to reference fields within the partition context [1abb098].\n\n3. **Expressive syntax**: The code uses expressive syntax like `return_flag.ASC()` to indicate sorting direction [1abb098].\n\n4. **Declarative style**: The code describes what to compute rather than how to compute it [1abb098].\n\n## 5. How the Code Addresses the Original Question\n\nThe code directly addresses the requirements in the original question:\n\n1. **Filtering by date**: It filters line items shipped as of September 2nd, 1998 [1abb098].\n\n2. **Grouping by return flag and line status**: It partitions data by these two fields [1abb098].\n\n3. **Calculating required metrics**:\n   - Sum of quantity (`SUM_QTY`)\n   - Sum of extended price (`SUM_BASE_PRICE`)\n   - Sum of discounted extended price (`SUM_DISC_PRICE`)\n   - Sum of discounted extended price plus tax (`SUM_CHARGE`)\n   - Average quantity (`AVG_QTY`)\n   - Average extended price (`AVG_PRICE`)\n   - Average discount (`AVG_DISC`)\n   - Count of lines (`COUNT_ORDER`) [1abb098]\n\n4. **Sorting results**: It sorts by return flag and line status as required [1abb098].\n\n## Comparison with SQL\n\nThe Pydough code is a more concise and readable alternative to the equivalent SQL query shown in the documentation [1abb098]:\n\n```sql\nselect\n    l_returnflag,\n    l_linestatus,\n    sum(l_quantity) as sum_qty,\n    sum(l_extendedprice) as sum_base_price,\n    sum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\n    sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\n    avg(l_quantity) as avg_qty,\n    avg(l_extendedprice) as avg_price,\n    avg(l_discount) as avg_disc,\n    count(*) as count_order\nfrom\n    lineitem\nwhere\n    l_shipdate <= date \'1998-12-01\' - interval \'90\' day\ngroup by\n    l_returnflag,\n    l_linestatus\norder by\n    l_returnflag,\n    l_linestatus\n```\n\nThe Pydough version makes the calculations more explicit by defining intermediate expressions (`disc_price` and `charge`), which improves readability and maintainability.', 'search_results': AggregateSearchResult(chunk_search_results=[ChunkSearchResult(score=0.049, text="source": [

"## Query 6\n",

"\n",

"This question formulated a sample \"what-if\" question, asking **how was revenue impacted over a previous year due to the presence of certain discounts** and potentially speculating on future revenue due to a change in that discount. It considers all the lineitems shipped in a given year with discounts in a certain value (in this case, 0.05 to 0.07). The query lists the amount by which the total revenue would have increased if these discounts had been eliminated for lineitems with l_quantity less than quantity. Note that the potential revenue increase is equal to the sum of the extended price times one minus the discount for all lineitems with discounts and quantities in the qualifying range. The chosen quantity range is quantity values below 24.\n",

"\n",

"\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"SELECT\n",

" SUM(L_EXTENDEDPRICE * L_DISCOUNT) AS REVENUE\n",

"FROM\n",

" LINEITEM\n",

"WHERE\n",

" L_SHIPDATE >= DATE '1994-01-01'\n",

" AND L_SHIPDATE < DATE '1995-01-01'\n",

" AND L_DISCOUNT BETWEEN 0.05 AND 0.07\n",

" AND L_QUANTITY < 24;\n",

"```"

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "6e1edea5-63f0-4542-9bcc-16a3398abe22",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"selected_lines = lines.WHERE(\n",

" (ship_date >= datetime.date(1994, 1, 1))\n",

" & (ship_date < datetime.date(1995, 1, 1))\n",

" & (0.05 <= discount)\n",

" & (discount <= 0.07)\n",

" & (quantity < 24)\n",

").CALCULATE(amt=extended_price * discount)\n",

"output = TPCH.CALCULATE(REVENUE=SUM(selected_lines.amt))\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "3f4c5e4e-b038-4c83-b064-f730612378da",

"metadata": {},

"source": [

"## Query 7\n",

"\n",

"This question asks about **the value of goods shipped between certain nations within a particular year** as a representation for future contract negotiations. More specifically, it finds, for two given nations, the gross discounted revenues derived from lineitems in which parts were shipped from a supplier in either nation to a customer in the other nation during 1995 and 1996. The query lists the supplier nation, the customer nation, the year, and the revenue from shipments that took place in that year. The query orders the answer by Supplier nation, Customer nation, and year (all ascending). The two nations chosen are France and Germany.\n",

"\n",

"\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"SELECT\n",

" SUPP_NATION,\n",

" CUST_NATION,\n",

" L_YEAR,\n",

" SUM(VOLUME) AS REVENUE\n",

"FROM (\n",

" SELECT\n",

" N1.N_NAME AS SUPP_NATION,\n",

" N2.N_NAME AS CUST_NATION,\n",

" EXTRACT(YEAR FROM L_SHIPDATE) AS L_YEAR,\n",

" L_EXTENDEDPRICE * (1 - L_DISCOUNT) AS VOLUME\n",

" FROM\n",

" SUPPLIER,\n",

" LINEITEM,\n",

" ORDERS,\n",

" CUSTOMER,\n",

" NATION N1,\n",

" NATION N2\n",

" WHERE\n",

" S_SUPPKEY = L_SUPPKEY\n",

" AND O_ORDERKEY = L_ORDERKEY\n",

" AND C_CUSTKEY = O_CUSTKEY\n",

" AND S_NATIONKEY = N1.N_NATIONKEY\n",

" AND C_NATIONKEY = N2.N_NATIONKEY\n",

" AND (\n",

" (N1.N_NAME = 'FRANCE' AND N2.N_NAME = 'GERMANY')\n",

" OR (N1.N_NAME = 'GERMANY' AND N2.N_NAME = 'FRANCE')\n",

" )\n",

" AND L_SHIPDATE BETWEEN DATE '1995-01-01' AND DATE '1996-12-31'\n",

") SHIPPING\n",

"GROUP BY\n",

" SUPP_NATION,\n",

" CUST_NATION,\n",

" L_YEAR\n",

"ORDER BY\n",

" SUPP_NATION,\n",

" CUST_NATION,\n",

" L_YEAR;\n",

"```"

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "45ebb047-324c-4040-8c81-b0d274ef6a3b",

"metadata": {},

"outputs": [],), ChunkSearchResult(score=0.046, text="source": [

"## Query 1\n",

"\n",

"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"select\n",

"\tl_returnflag,\n",

"\tl_linestatus,\n",

"\tsum(l_quantity) as sum_qty,\n",

"\tsum(l_extendedprice) as sum_base_price,\n",

"\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\n",

"\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\n",

"\tavg(l_quantity) as avg_qty,\n",

"\tavg(l_extendedprice) as avg_price,\n",

"\tavg(l_discount) as avg_disc,\n",

"\tcount(*) as count_order\n",

"from\n",

"\tlineitem\n",

"where\n",

"\tl_shipdate <= date '1998-12-01' - interval '90' day\n",

"group by\n",

"\tl_returnflag,\n",

"\tl_linestatus\n",

"order by\n",

"\tl_returnflag,\n",

"\tl_linestatus\n",

"```"

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"disc_price = l.extended_price * (1 - l.discount)\n",

"charge = disc_price * (1 + l.tax)\n",

"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\n",

"partitioned_lines = PARTITION(selected_lines, name=\"l\", by=(return_flag, status))\n",

"output = partitioned_lines.CALCULATE(\n",

" L_RETURNFLAG=return_flag,\n",

" L_LINESTATUS=status,\n",

" SUM_QTY=SUM(l.quantity),\n",

" SUM_BASE_PRICE=SUM(l.extended_price),\n",

" SUM_DISC_PRICE=SUM(disc_price),\n",

" SUM_CHARGE=SUM(charge),\n",

" AVG_QTY=AVG(l.quantity),\n",

" AVG_PRICE=AVG(l.extended_price),\n",

" AVG_DISC=AVG(l.discount),\n",

" COUNT_ORDER=COUNT(l),\n",

").ORDER_BY(return_flag.ASC(), status.ASC())\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",

"metadata": {},

"source": [

"## Query 2\n",

"\n",

"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\n",

"\n",

"\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"SELECT\n",

" S_ACCTBAL,\n",

" S_NAME,\n",

" N_NAME,\n",

" P_PARTKEY,\n",

" P_MFGR,\n",

" S_ADDRESS,\n",

" S_PHONE,\n",

" S_COMMENT\n",

"FROM\n",

" PART,\n",

" SUPPLIER,\n",

" PARTSUPP,\n",

" NATION,\n",

" REGION\n",

"WHERE\n",

" P_PARTKEY = PS_PARTKEY\n",

" AND S_SUPPKEY = PS_SUPPKEY\n",

" AND P_SIZE = 15\n",

" AND P_TYPE LIKE '%BRASS'\n",

" AND S_NATIONKEY = N_NATIONKEY\n",

" AND N_REGIONKEY = R_REGIONKEY\n",

" AND R_NAME = 'EUROPE'\n",

" AND PS_SUPPLYCOST = (\n",

" SELECT MIN(PS_SUPPLYCOST)\n",

" FROM PARTSUPP, SUPPLIER, NATION, REGION\n",

" WHERE P_PARTKEY = PS_PARTKEY\n",

" AND S_SUPPKEY = PS_SUPPKEY\n",

" AND S_NATIONKEY = N_NATIONKEY\n",

" AND N_REGIONKEY = R_REGIONKEY\n",

" AND R_NAME = 'EUROPE'\n",

" )\n",

"ORDER BY\n",

" S_ACCTBAL DESC,\n",

" N_NAME,\n",

" S_NAME,\n",

" P_PARTKEY\n",

"LIMIT 100;\n",

"```\n",

"\n",

"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "), ChunkSearchResult(score=0.046, text="source": [

"## Query 19\n",

"\n",

"This question seeks to **report the gross discounted revenue resulting from select parts with a set of handling details**. More specifically, it finds the gross discounted revenue for all orders for three different types of parts that were shipped by air and delivered in person. Parts are selected based on the combination of specific brands, a list of containers, and a range of sizes. The allowed combinations are:\n",

"\n",

"- The brand is `'BRAND#12'`, the quantity is between 1 and 11, the size is between 1 and 5, and the container type is one of `['SM CASE', 'SM BOX', 'SM PACK', 'SM PKG']`.\n",

"- The brand is `'BRAND#23'`, the quantity is between 10 and 20, the size is between 1 and 10, and the container type is one of `['MED BAG', 'MED BOX', 'MED PKG', 'MED PACK']`.\n",

"- The brand is `'BRAND#34'`, the quantity is between 20 and 30, the size is between 1 and 15, and the container type is one of `['LG CASE', 'LG BOX', 'LG PACK', 'LG PKG']`.\n",

"\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"select\n",

" sum(l_extendedprice * (1 - l_discount) ) as revenue\n",

"from\n",

" lineitem,\n",

" part\n",

"where\n",

" (\n",

" p_partkey = l_partkey\n",

" and p_brand = 'Brand#12'\n",

" and p_container in ( 'SM CASE', 'SM BOX', 'SM PACK', 'SM PKG')\n",

" and l_quantity >= 1 and l_quantity <= 1 + 10\n",

" and p_size between 1 and 5\n",

" and l_shipmode in ('AIR', 'AIR REG')\n",

" and l_shipinstruct = 'DELIVER IN PERSON'\n",

" )\n",

" or\n",

" (\n",

" p_partkey = l_partkey\n",

" and p_brand = 'Brand#23'\n",

" and p_container in ('MED BAG', 'MED BOX', 'MED PKG', 'MED PACK')\n",

" and l_quantity >= 10 and l_quantity <= 10 + 10\n",

" and p_size between 1 and 10\n",

" and l_shipmode in ('AIR', 'AIR REG')\n",

" and l_shipinstruct = 'DELIVER IN PERSON'\n",

" )\n",

" or\n",

" (\n",

" p_partkey = l_partkey\n",

" and p_brand = 'Brand#34'\n",

" and p_container in ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG')\n",

" and l_quantity >= 20 and l_quantity <= 20 + 10\n",

" and p_size between 1 and 15\n",

" and l_shipmode in ('AIR', 'AIR REG')\n",

" and l_shipinstruct = 'DELIVER IN PERSON'\n",

" )\n",

"```"

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "aeaaa90e-000e-4a12-91e9-4100d308d312",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"selected_lines = lines.WHERE(\n",

" (ISIN(ship_mode, (\"AIR\", \"AIR REG\")))\n",

" & (ship_instruct == \"DELIVER IN PERSON\")\n",

" & (part.size >= 1)\n",

" & (\n",

" (\n",

" (part.size <= 5)\n",

" & (quantity >= 1)\n",

" & (quantity <= 11)\n",

" & ISIN(\n",

" part.container,\n",

" (\"SM CASE\", \"SM BOX\", \"SM PACK\", \"SM PKG\"),\n",

" )\n",

" & (part.brand == \"Brand#12\")\n",

" )\n",

" | (\n",

" (part.size <= 10)\n",

" & (quantity >= 10)\n",

" & (quantity <= 20)\n",

" & ISIN(\n",

" part.container,\n",

" (\"MED BAG\", \"MED BOX\", \"MED PACK\", \"MED PKG\"),\n",

" )\n",

" & (part.brand == \"Brand#23\")\n",

" )\n",

" | (\n",

" (part.size <= 15)\n",

" & (quantity >= 20)\n",

" & (quantity <= 30)\n",

" & ISIN(\n",

" part.container,\n",

" (\"LG CASE\", \"LG BOX\", \"LG PACK\", \"LG PKG\"),\n",

" )\n",

" & (part.brand == \"Brand#34\")\n",

" )\n",

" )\n",

")\n",

"output = TPCH.CALCULATE(\n",

" REVENUE=SUM(selected_lines.extended_price * (1 - selected_lines.discount))\n",

")\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "860e2d30-5fb9-48ad-ba6d-b2cc7145f97f",

"metadata": {},), ChunkSearchResult(score=0.045, text=## File: tests/test_plan_refsols/tpch_q1.txt

````

ROOT(columns=[('L_RETURNFLAG', L_RETURNFLAG), ('L_LINESTATUS', L_LINESTATUS), ('SUM_QTY', SUM_QTY), ('SUM_BASE_PRICE', SUM_BASE_PRICE), ('SUM_DISC_PRICE', SUM_DISC_PRICE), ('SUM_CHARGE', SUM_CHARGE), ('AVG_QTY', AVG_QTY), ('AVG_PRICE', AVG_PRICE), ('AVG_DISC', AVG_DISC), ('COUNT_ORDER', COUNT_ORDER)], orderings=[(ordering_8):asc_first, (ordering_9):asc_first])

PROJECT(columns={'AVG_DISC': AVG_DISC, 'AVG_PRICE': AVG_PRICE, 'AVG_QTY': AVG_QTY, 'COUNT_ORDER': COUNT_ORDER, 'L_LINESTATUS': L_LINESTATUS, 'L_RETURNFLAG': L_RETURNFLAG, 'SUM_BASE_PRICE': SUM_BASE_PRICE, 'SUM_CHARGE': SUM_CHARGE, 'SUM_DISC_PRICE': SUM_DISC_PRICE, 'SUM_QTY': SUM_QTY, 'ordering_8': L_RETURNFLAG, 'ordering_9': L_LINESTATUS})

PROJECT(columns={'AVG_DISC': agg_0, 'AVG_PRICE': agg_1, 'AVG_QTY': agg_2, 'COUNT_ORDER': DEFAULT_TO(agg_3, 0:int64), 'L_LINESTATUS': status, 'L_RETURNFLAG': return_flag, 'SUM_BASE_PRICE': DEFAULT_TO(agg_4, 0:int64), 'SUM_CHARGE': DEFAULT_TO(agg_5, 0:int64), 'SUM_DISC_PRICE': DEFAULT_TO(agg_6, 0:int64), 'SUM_QTY': DEFAULT_TO(agg_7, 0:int64)})

AGGREGATE(keys={'return_flag': return_flag, 'status': status}, aggregations={'agg_0': AVG(discount), 'agg_1': AVG(extended_price), 'agg_2': AVG(quantity), 'agg_3': COUNT(), 'agg_4': SUM(extended_price), 'agg_5': SUM(expr_10), 'agg_6': SUM(expr_11), 'agg_7': SUM(quantity)})

PROJECT(columns={'discount': discount, 'expr_10': extended_price * 1:int64 - discount * 1:int64 + tax, 'expr_11': extended_price * 1:int64 - discount, 'extended_price': extended_price, 'quantity': quantity, 'return_flag': return_flag, 'status': status})

FILTER(condition=ship_date <= datetime.date(1998, 12, 1):date, columns={'discount': discount, 'extended_price': extended_price, 'quantity': quantity, 'return_flag': return_flag, 'status': status, 'tax': tax})

SCAN(table=tpch.LINEITEM, columns={'discount': l_discount, 'extended_price': l_extendedprice, 'quantity': l_quantity, 'return_flag': l_returnflag, 'ship_date': l_shipdate, 'status': l_linestatus, 'tax': l_tax})

````

## File: tests/test_plan_refsols/tpch_q10.txt

````

ROOT(columns=[('C_CUSTKEY', C_CUSTKEY), ('C_NAME', C_NAME), ('REVENUE', REVENUE), ('C_ACCTBAL', C_ACCTBAL), ('N_NAME', N_NAME), ('C_ADDRESS', C_ADDRESS), ('C_PHONE', C_PHONE), ('C_COMMENT', C_COMMENT)], orderings=[(ordering_1):desc_last, (ordering_2):asc_first])

LIMIT(limit=Literal(value=20, type=Int64Type()), columns={'C_ACCTBAL': C_ACCTBAL, 'C_ADDRESS': C_ADDRESS, 'C_COMMENT': C_COMMENT, 'C_CUSTKEY': C_CUSTKEY, 'C_NAME': C_NAME, 'C_PHONE': C_PHONE, 'N_NAME': N_NAME, 'REVENUE': REVENUE, 'ordering_1': ordering_1, 'ordering_2': ordering_2}, orderings=[(ordering_1):desc_last, (ordering_2):asc_first])

PROJECT(columns={'C_ACCTBAL': C_ACCTBAL, 'C_ADDRESS': C_ADDRESS, 'C_COMMENT': C_COMMENT, 'C_CUSTKEY': C_CUSTKEY, 'C_NAME': C_NAME, 'C_PHONE': C_PHONE, 'N_NAME': N_NAME, 'REVENUE': REVENUE, 'ordering_1': REVENUE, 'ordering_2': C_CUSTKEY})

PROJECT(columns={'C_ACCTBAL': acctbal, 'C_ADDRESS': address, 'C_COMMENT': comment, 'C_CUSTKEY': key, 'C_NAME': name, 'C_PHONE': phone, 'N_NAME': name_4, 'REVENUE': DEFAULT_TO(agg_0, 0:int64)})

JOIN(conditions=[t0.nation_key == t1.key], types=['left'], columns={'acctbal': t0.acctbal, 'address': t0.address, 'agg_0': t0.agg_0, 'comment': t0.comment, 'key': t0.key, 'name': t0.name, 'name_4': t1.name, 'phone': t0.phone})

JOIN(conditions=[t0.key == t1.customer_key], types=['left'], columns={'acctbal': t0.acctbal, 'address': t0.address, 'agg_0': t1.agg_0, 'comment': t0.comment, 'key': t0.key, 'name': t0.name, 'nation_key': t0.nation_key, 'phone': t0.phone})

SCAN(table=tpch.CUSTOMER, columns={'acctbal': c_acctbal, 'address': c_address, 'comment': c_comment, 'key': c_custkey, 'name': c_name, 'nation_key': c_nationkey, 'phone': c_phone})

AGGREGATE(keys={'customer_key': customer_key}, aggregations={'agg_0': SUM(amt)})

PROJECT(columns={'amt': extended_price * 1:int64 - discount, 'customer_key': customer_key})), ChunkSearchResult(score=0.045, text=CAST(STRFTIME('%Y', sbtxdatetime) AS INTEGER) < 2025

AND CAST(STRFTIME('%d', sbtxdatetime) AS INTEGER) > 1

````

## File: tests/test_sql_refsols/sql_transaction_week_sampler_wednesday_zero_ansi.sql

````sql

SELECT

sbtxdatetime AS date_time,

DATE_TRUNC('WEEK', CAST(sbtxdatetime AS TIMESTAMP)) AS sow,

CASE

WHEN DAY_OF_WEEK(sbtxdatetime) = 0

THEN 'Sunday'

WHEN DAY_OF_WEEK(sbtxdatetime) = 1

THEN 'Monday'

WHEN DAY_OF_WEEK(sbtxdatetime) = 2

THEN 'Tuesday'

WHEN DAY_OF_WEEK(sbtxdatetime) = 3

THEN 'Wednesday'

WHEN DAY_OF_WEEK(sbtxdatetime) = 4

THEN 'Thursday'

WHEN DAY_OF_WEEK(sbtxdatetime) = 5

THEN 'Friday'

WHEN DAY_OF_WEEK(sbtxdatetime) = 6

THEN 'Saturday'

END AS dayname,

(

DAY_OF_WEEK(sbtxdatetime) + 4

) % 7 AS dayofweek

FROM main.sbtransaction

WHERE

EXTRACT(DAY FROM sbtxdatetime) > 1 AND EXTRACT(YEAR FROM sbtxdatetime) < 2025

````

## File: tests/test_sql_refsols/sql_transaction_week_sampler_wednesday_zero_sqlite.sql

````sql

SELECT

sbtxdatetime AS date_time,

DATE(

sbtxdatetime,

'-' || CAST((

CAST(STRFTIME('%w', DATETIME(sbtxdatetime)) AS INTEGER) + 4

) % 7 AS TEXT) || ' days',

'start of day'

) AS sow,

CASE

WHEN CAST(STRFTIME('%w', sbtxdatetime) AS INTEGER) = 0

THEN 'Sunday'

WHEN CAST(STRFTIME('%w', sbtxdatetime) AS INTEGER) = 1

THEN 'Monday'

WHEN CAST(STRFTIME('%w', sbtxdatetime) AS INTEGER) = 2

THEN 'Tuesday'

WHEN CAST(STRFTIME('%w', sbtxdatetime) AS INTEGER) = 3

THEN 'Wednesday'

WHEN CAST(STRFTIME('%w', sbtxdatetime) AS INTEGER) = 4

THEN 'Thursday'

WHEN CAST(STRFTIME('%w', sbtxdatetime) AS INTEGER) = 5

THEN 'Friday'

WHEN CAST(STRFTIME('%w', sbtxdatetime) AS INTEGER) = 6

THEN 'Saturday'

END AS dayname,

(

CAST(STRFTIME('%w', sbtxdatetime) AS INTEGER) + 4

) % 7 AS dayofweek

FROM main.sbtransaction

WHERE

CAST(STRFTIME('%Y', sbtxdatetime) AS INTEGER) < 2025

AND CAST(STRFTIME('%d', sbtxdatetime) AS INTEGER) > 1

````

## File: tests/test_sql_refsols/tpch_q1_ansi.sql

````sql

WITH _t1 AS (

SELECT

AVG(l_discount) AS agg_0,

AVG(l_extendedprice) AS agg_1,

AVG(l_quantity) AS agg_2,

COUNT() AS agg_3,

SUM(l_extendedprice * (

1 - l_discount

) * (

1 + l_tax

)) AS agg_5,

SUM(l_extendedprice * (

1 - l_discount

)) AS agg_6,

SUM(l_extendedprice) AS agg_4,

SUM(l_quantity) AS agg_7,

l_returnflag AS return_flag,

l_linestatus AS status

FROM tpch.lineitem

WHERE

l_shipdate <= CAST('1998-12-01' AS DATE)

GROUP BY

l_returnflag,

l_linestatus

)

SELECT

return_flag AS L_RETURNFLAG,

status AS L_LINESTATUS,

COALESCE(agg_7, 0) AS SUM_QTY,

COALESCE(agg_4, 0) AS SUM_BASE_PRICE,

COALESCE(agg_6, 0) AS SUM_DISC_PRICE,

COALESCE(agg_5, 0) AS SUM_CHARGE,

agg_2 AS AVG_QTY,

agg_1 AS AVG_PRICE,

agg_0 AS AVG_DISC,

COALESCE(agg_3, 0) AS COUNT_ORDER

FROM _t1

ORDER BY

return_flag,

status

````

## File: tests/test_sql_refsols/tpch_q1_sqlite.sql

````sql

WITH _t1 AS (

SELECT

AVG(l_discount) AS agg_0,

AVG(l_extendedprice) AS agg_1,

AVG(l_quantity) AS agg_2,

COUNT() AS agg_3,

SUM(l_extendedprice * (

1 - l_discount

) * (

1 + l_tax

)) AS agg_5,

SUM(l_extendedprice * (

1 - l_discount

)) AS agg_6,

SUM(l_extendedprice) AS agg_4,

SUM(l_quantity) AS agg_7,

l_returnflag AS return_flag,

l_linestatus AS status

FROM tpch.lineitem

WHERE

l_shipdate <= '1998-12-01'

GROUP BY

l_returnflag,

l_linestatus

)

SELECT

return_flag AS L_RETURNFLAG,

status AS L_LINESTATUS,

COALESCE(agg_7, 0) AS SUM_QTY,

COALESCE(agg_4, 0) AS SUM_BASE_PRICE,

COALESCE(agg_6, 0) AS SUM_DISC_PRICE,

COALESCE(agg_5, 0) AS SUM_CHARGE,

agg_2 AS AVG_QTY,

agg_1 AS AVG_PRICE,

agg_0 AS AVG_DISC,

COALESCE(agg_3, 0) AS COUNT_ORDER

FROM _t1

ORDER BY

return_flag,

status

````

## File: tests/test_sql_refsols/tpch_q10_ansi.sql

````sql

WITH _t3_2 AS (

SELECT

SUM(lineitem.l_extendedprice * (

1 - lineitem.l_discount

)) AS agg_0,

orders.o_custkey AS customer_key

FROM tpch.orders AS orders

JOIN tpch.lineitem AS lineitem

ON lineitem.l_orderkey = orders.o_orderkey AND lineitem.l_returnflag = 'R'

WHERE

orders.o_orderdate < CAST('1994-01-01' AS DATE)), ChunkSearchResult(score=0.044, text="source": [

"%%pydough\n",

"\n",

"customer_info = customers.CALCULATE(\n",

" key,\n",

" num_non_special_orders=COUNT(\n",

" orders.WHERE(~(LIKE(comment, \"%special%requests%\")))\n",

" ),\n",

")\n",

"output = PARTITION(customer_info, name=\"custs\", by=num_non_special_orders).CALCULATE(\n",

" C_COUNT=num_non_special_orders, CUSTDIST=COUNT(custs)\n",

").ORDER_BY(CUSTDIST.DESC(), C_COUNT.DESC())\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "1f793b72-d8ce-4f82-84b5-7e568ee0600a",

"metadata": {},

"source": [

"## Query 14\n",

"\n",

"This question seeks seeks to determine **the impact of a promotion on revenue within a particular month**. More specifically, it determines what percentage of the revenue in a given year and month was derived from promotional parts. The query considers only parts actually shipped in that month and gives the percentage. Revenue is defined as extended price times one minus the discount. The chosen year and month are September of 1995.\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"SELECT\n",

" 100.00 * SUM(CASE\n",

" WHEN P_TYPE LIKE 'PROMO%'\n",

" THEN L_EXTENDEDPRICE * (1 - L_DISCOUNT)\n",

" ELSE 0\n",

" END) / SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS PROMO_REVENUE\n",

"FROM\n",

" LINEITEM,\n",

" PART\n",

"WHERE\n",

" L_PARTKEY = P_PARTKEY\n",

" AND L_SHIPDATE >= DATE '1995-09-01'\n",

" AND L_SHIPDATE < DATE '1995-10-01';\n",

"```"

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "8a843681-0893-4636-a312-75095c730de3",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"value = extended_price * (1 - discount)\n",

"selected_lines = lines.WHERE(\n",

" (ship_date >= datetime.date(1995, 9, 1))\n",

" & (ship_date < datetime.date(1995, 10, 1))\n",

").CALCULATE(\n",

" value=value,\n",

" promo_value=IFF(STARTSWITH(part.part_type, \"PROMO\"), value, 0),\n",

")\n",

"output = TPCH.CALCULATE(PROMO_REVENUE=100.0 * SUM(selected_lines.promo_value) / SUM(selected_lines.value))\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "1734b0e1-a4bb-456b-a41e-fa6440c87e85",

"metadata": {},

"source": [

"## Query 15\n",

"\n",

"This question seeks to determine **the top supplier within a particular quarter**. It does so by finding the supplier who contributed the most to the overall revenue for parts shipped during a given quarter of a given year. In case of a tie, the query lists all suppliers whose contribution was equal to the maximum, presented in supplier number order. The chosen quarter is the first 3 months of 1996.\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"with REVENUE (SUPPLIER_NO, TOTAL_REVENUE) AS\n",

" SELECT\n",

" L_SUPPKEY,\n",

" SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT))\n",

" FROM\n",

" LINEITEM\n",

" WHERE\n",

" L_SHIPDATE >= DATE '1996-01-01'\n",

" AND L_SHIPDATE < DATE '1996-04-01'\n",

" GROUP BY\n",

" L_SUPPKEY;\n",

"\n",

"SELECT\n",

" S_SUPPKEY,\n",

" S_NAME,\n",

" S_ADDRESS,\n",

" S_PHONE,\n",

" TOTAL_REVENUE\n",

"FROM\n",

" SUPPLIER,\n",

" REVENUE\n",

"WHERE\n",

" S_SUPPKEY = SUPPLIER_NO AND\n",

" TOTAL_REVENUE = (\n",

" SELECT\n",

" MAX(TOTAL_REVENUE)\n",

" FROM\n",

" REVENUE0\n",

" )\n",

"ORDER BY\n",

" SUPPLIER_NO;\n",

"```\n",

"\n",

"With PyDough, the total revenue per-supplier can be expressed via contextless expressions which are first placed into context for the global aggregation to find the maximum revenue overall, then used again to be associated per-supplier."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "a3f9b025-3ae7-4c7d-888c-a430cbe536b2",

"metadata": {},

"outputs": [],), ChunkSearchResult(score=0.040, text="source": [

"### SQL\n",

"\n",

"```SQL\n",

"Select\n",

" (L_EXTENDED_PRICE * (1 - L_DISCOUNT)) / order_total as revenue_ratio,\n",

" orderkey,\n",

" l_linenumber as line_number\n",

"from lines\n",

"inner join (\n",

" select\n",

" o_orderkey as order_key,\n",

" SUM(L_EXTENDED_PRICE * (1 - L_DISCOUNT)) as order_total\n",

" from orders\n",

" inner join lines\n",

" on l_orderkey = o_orderkey\n",

" group by o_orderkey\n",

")\n",

"on l_orderkey = order_key\n",

"order by revenue_ratio ASC, order_key DESC, line_number DESC\n",

"LIMIT 5\n",

"```"

]

},

{

"cell_type": "markdown",

"id": "4e81ec40-f82c-42e6-9656-7f36e619a52a",

"metadata": {},

"source": [

"### PyDough\n",

"\n",

"```python\n",

"revenue_def = extended_price*(1-discount)\n",

"orders.CALCULATE(total_line_price=SUM(lines.CALCULATE(line_price=revenue_def).line_price)).lines.CALCULATE(\n",

" revenue_ratio=revenue_def / total_line_price, \n",

" order_key=order_key, \n",

" line_number=line_number\n",

").TOP_K(5, by=(revenue_ratio.ASC(), order_key.DESC(), line_number.DESC()))\n",

"```"

]

},

{

"cell_type": "markdown",

"id": "efca5340-6acc-48dd-9287-f3baaabe5239",

"metadata": {},

"source": [

"The example SQL requires a nested subquery to answer, which can easily become complicated and unmanagable as questions scale in size. It also requires explicitly representing the join information where a decision like **LEFT** vs **INNER** join impacts correctness and is a function of the data.\n",

"\n",

"In constrast, PyDough has a simpler representation, avoiding some of the redundancy in the SQL code and the join information is encoded entirely in the metadata."

]

},

{

"cell_type": "markdown",

"id": "3228b465-a356-4d5e-9b61-a13b437a8c7f",

"metadata": {},

"source": [

"## PyDough Solution\n",

"\n",

"While we can just execute the PyDough example above, we are going to take a different approach to show how one might generate this query in a \"WHAT-IF\" manner. This approach will be a longer solution, but will be helpful to enable faster iteration once we modify the question.\n",

"\n",

"We are opting to demonstrate this because:\n",

"1. We believe this is a good representation for how PyDough can be leveraged to gradually handle increasing question complexity.\n",

"2. We believe this reflects an investigative approach to query generation, where someone may understand at a high-level what needs to be done, but not necessary that \"path\" to get there.\n",

"\n",

"To do this we will first need to define revenue. Here we will say that the revenue is the price information after removing any discounts."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "90f77e14-4540-42af-a62e-2ba4e9ae40b9",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"revenue_def = extended_price*(1-discount)"

]

},

{

"cell_type": "markdown",

"id": "c250943d-f018-4b53-b3b0-423c35db5004",

"metadata": {},

"source": [

"This might seem shocking. We have defined `revenue_def` out of nowhere using an `extended_price` and `discount`. What has actually happened here is that we have generated what is called a `Contextless Expression`. This fundamental building block is the key to PyDough's composability.\n",

"\n",

"On its own this expression doesn't mean anything. In fact if we inspect this object in regular PyDough we will see that PyDough itself has a lot of questions."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "3dc2af81-baa9-45df-9624-a6afca0101b7",

"metadata": {},

"outputs": [],

"source": [

"revenue_def"

]

},

{

"cell_type": "markdown",

"id": "576f9203-35c0-458a-8860-88615bcade4f",

"metadata": {},), ChunkSearchResult(score=0.040, text=# names in a rolling window.

⋮----

def avg_order_diff_per_customer()

⋮----

# Finds the 5 customers with the highest average difference in days between

# orders made.

prev_order_date_by_cust = PREV(order_date, by=order_date.ASC(), levels=1)

order_info = orders.CALCULATE(

selected_customers = Customers.WHERE(HAS(order_info))

⋮----

def yoy_change_in_num_orders()

⋮----

# For every year, counts the number of orders made in that year and the

# percentage change from the previous year.

years = PARTITION(

current_year_orders = COUNT(orders_in_year)

prev_year_orders = PREV(COUNT(orders_in_year), by=year.ASC())

⋮----

def first_order_in_year()

⋮----

# Find all orders that do not have a previous order in the same year

# (breaking ties by order key).

previous_order_date = PREV(order_date, by=(order_date.ASC(), key.ASC()))

⋮----

def customer_largest_order_deltas()

⋮----

# For each customer, find the highest positive/negative difference in

# revenue between one of their orders and and the most recent order before

# it, ignoring their first ever order. Return the 5 customers with the

# largest such difference. Only consider customers with orders.

line_revenue = extended_price * (1 - discount)

order_revenue = SUM(lines.CALCULATE(r=line_revenue).r)

previous_order_revenue = PREV(order_revenue, by=order_date.ASC(), levels=1)

orders_info = orders.WHERE(PRESENT(previous_order_revenue)).CALCULATE(

⋮----

def suppliers_bal_diffs()

⋮----

# Finds the 5 suppliers with the largest difference in account balance from

# the supplier with the next smallest account balance in the same region.

⋮----

def month_year_sliding_windows()

⋮----

# Finds all months where the total amount spent by customers on orders in

# that month was more than the preceding/following month, and the amount

# spent in that year was more than the following year.

ym_groups = PARTITION(

y_groups = (

⋮----

def avg_gap_prev_urgent_same_clerk()

⋮----

# Finds the average gap in days between each urgent order and the previous

# urgent order handled by the same clerk

urgent_orders = Orders.WHERE(order_priority == "1-URGENT")

clerks = PARTITION(urgent_orders, name="orders", by=clerk)

order_info = clerks.orders.CALCULATE(

⋮----

def nation_window_aggs()

⋮----

# Calculating multiple global windowed aggregations for each nation, only

# considering nations whose names do not start with a vowel.

⋮----

def region_nation_window_aggs()

⋮----

# per-region, considering nations whose names do not start with a vowel.

⋮----

def supplier_pct_national_qty()

⋮----

# Find the 5 African suppliers with the highest percentage of total

# quantity of product shipped from them out of all suppliers in that nation

# meeting certain criteria. Include for each such supplier their name,

# nation name, the quantity, and the percentage. The criteria are that the

# shipments were done in 1998, they were shipped by ship, the part shipped

# had had "tomato" in the name and was a large container. Also, when

# finding the sum for each naiton and the best suppliers, ignore all

# suppliers with a negative account balance and whose comments do not

# contain the word "careful".

selected_lines = lines.WHERE(

supp_qty = SUM(selected_lines.quantity)

⋮----

def highest_priority_per_year()

⋮----

# For each year, identify the priority with the highest percentage of

# made in that year with that priority, listing the year, priority, and

# percentage. Sort the results by year.

order_info = Orders.CALCULATE(order_year=YEAR(order_date))

year_priorities = PARTITION(

years = PARTITION(year_priorities, name="priorities", by=order_year)

⋮----

def nation_best_order()

⋮----

# For each Asian nation, identify the most expensive order made by a

# customer in that nation in 1998, listing the nation name, customer

# name, order key, the order's price, and percentage of the price of

# all orders made in 1998. Order the nations alphabetically.

selected_nations = Nations.WHERE(region.name == "ASIA")

best_order = (

⋮----), ChunkSearchResult(score=0.031, text=) < COALESCE(_t9.agg_1, 0)

ORDER BY

ordering_2 DESC

LIMIT 10

)

SELECT

ps_partkey AS PS_PARTKEY,

value AS VALUE

FROM _t0_2

ORDER BY

ordering_2 DESC

````

## File: tests/test_sql_refsols/tpch_q12_ansi.sql

````sql

WITH _t1_2 AS (

SELECT

SUM(

(

orders.o_orderpriority <> '1-URGENT' AND orders.o_orderpriority <> '2-HIGH'

)

) AS agg_1,

SUM((

orders.o_orderpriority = '1-URGENT' OR orders.o_orderpriority = '2-HIGH'

)) AS agg_0,

lineitem.l_shipmode AS ship_mode

FROM tpch.lineitem AS lineitem

LEFT JOIN tpch.orders AS orders

ON lineitem.l_orderkey = orders.o_orderkey

WHERE

lineitem.l_commitdate < lineitem.l_receiptdate

AND lineitem.l_commitdate > lineitem.l_shipdate

AND lineitem.l_receiptdate < CAST('1995-01-01' AS DATE)

AND lineitem.l_receiptdate >= CAST('1994-01-01' AS DATE)

AND (

lineitem.l_shipmode = 'MAIL' OR lineitem.l_shipmode = 'SHIP'

)

GROUP BY

lineitem.l_shipmode

)

SELECT

ship_mode AS L_SHIPMODE,

COALESCE(agg_0, 0) AS HIGH_LINE_COUNT,

COALESCE(agg_1, 0) AS LOW_LINE_COUNT

FROM _t1_2

ORDER BY

ship_mode

````

## File: tests/test_sql_refsols/tpch_q12_sqlite.sql

````sql

WITH _t1_2 AS (

SELECT

SUM(

(

orders.o_orderpriority <> '1-URGENT' AND orders.o_orderpriority <> '2-HIGH'

)

) AS agg_1,

SUM((

orders.o_orderpriority = '1-URGENT' OR orders.o_orderpriority = '2-HIGH'

)) AS agg_0,

lineitem.l_shipmode AS ship_mode

FROM tpch.lineitem AS lineitem

LEFT JOIN tpch.orders AS orders

ON lineitem.l_orderkey = orders.o_orderkey

WHERE

lineitem.l_commitdate < lineitem.l_receiptdate

AND lineitem.l_commitdate > lineitem.l_shipdate

AND lineitem.l_receiptdate < '1995-01-01'

AND lineitem.l_receiptdate >= '1994-01-01'

AND (

lineitem.l_shipmode = 'MAIL' OR lineitem.l_shipmode = 'SHIP'

)

GROUP BY

lineitem.l_shipmode

)

SELECT

ship_mode AS L_SHIPMODE,

COALESCE(agg_0, 0) AS HIGH_LINE_COUNT,

COALESCE(agg_1, 0) AS LOW_LINE_COUNT

FROM _t1_2

ORDER BY

ship_mode

````

## File: tests/test_sql_refsols/tpch_q13_ansi.sql

````sql

WITH _t1 AS (

SELECT

COUNT() AS agg_0,

o_custkey AS customer_key

FROM tpch.orders

WHERE

NOT o_comment LIKE '%special%requests%'

GROUP BY

o_custkey

), _t2 AS (

SELECT

COUNT() AS agg_0,

COALESCE(_t1.agg_0, 0) AS num_non_special_orders

FROM tpch.customer AS customer

LEFT JOIN _t1 AS _t1

ON _t1.customer_key = customer.c_custkey

GROUP BY

COALESCE(_t1.agg_0, 0)

), _t0_2 AS (

SELECT

COALESCE(agg_0, 0) AS custdist,

num_non_special_orders AS c_count,

COALESCE(agg_0, 0) AS ordering_1,

num_non_special_orders AS ordering_2

FROM _t2

ORDER BY

ordering_1 DESC,

ordering_2 DESC

LIMIT 10

)

SELECT

c_count AS C_COUNT,

custdist AS CUSTDIST

FROM _t0_2

ORDER BY

ordering_1 DESC,

ordering_2 DESC

````

## File: tests/test_sql_refsols/tpch_q13_sqlite.sql

````sql

WITH _t1 AS (

SELECT

COUNT() AS agg_0,

o_custkey AS customer_key

FROM tpch.orders

WHERE

NOT o_comment LIKE '%special%requests%'

GROUP BY

o_custkey

), _t2 AS (

SELECT

COUNT() AS agg_0,

COALESCE(_t1.agg_0, 0) AS num_non_special_orders

FROM tpch.customer AS customer

LEFT JOIN _t1 AS _t1

ON _t1.customer_key = customer.c_custkey

GROUP BY

COALESCE(_t1.agg_0, 0)

), _t0_2 AS (

SELECT

COALESCE(agg_0, 0) AS custdist,

num_non_special_orders AS c_count,

COALESCE(agg_0, 0) AS ordering_1,

num_non_special_orders AS ordering_2

FROM _t2

ORDER BY

ordering_1 DESC,

ordering_2 DESC

LIMIT 10

)

SELECT

c_count AS C_COUNT,

custdist AS CUSTDIST

FROM _t0_2

ORDER BY

ordering_1 DESC,

ordering_2 DESC

````

## File: tests/test_sql_refsols/tpch_q14_ansi.sql

````sql

WITH _t0_2 AS (

SELECT

SUM(

CASE

WHEN part.p_type LIKE 'PROMO%'

THEN lineitem.l_extendedprice * (

1 - lineitem.l_discount

)

ELSE 0

END

) AS agg_0,

SUM(lineitem.l_extendedprice * (

1 - lineitem.l_discount

)) AS agg_1

FROM tpch.lineitem AS lineitem

LEFT JOIN tpch.part AS part

ON lineitem.l_partkey = part.p_partkey

WHERE

lineitem.l_shipdate < CAST('1995-10-01' AS DATE)

AND lineitem.l_shipdate >= CAST('1995-09-01' AS DATE)

)

SELECT

(

100.0 * COALESCE(agg_0, 0)

) / COALESCE(agg_1, 0) AS PROMO_REVENUE), ChunkSearchResult(score=0.029, text=FROM _t0_2

````

## File: tests/test_sql_refsols/tpch_q14_sqlite.sql

````sql

WITH _t0_2 AS (

SELECT

SUM(

IIF(

part.p_type LIKE 'PROMO%',

lineitem.l_extendedprice * (

1 - lineitem.l_discount

),

0

)

) AS agg_0,

SUM(lineitem.l_extendedprice * (

1 - lineitem.l_discount

)) AS agg_1

FROM tpch.lineitem AS lineitem

LEFT JOIN tpch.part AS part

ON lineitem.l_partkey = part.p_partkey

WHERE

lineitem.l_shipdate < '1995-10-01' AND lineitem.l_shipdate >= '1995-09-01'

)

SELECT

CAST((

100.0 * COALESCE(agg_0, 0)

) AS REAL) / COALESCE(agg_1, 0) AS PROMO_REVENUE

FROM _t0_2

````

## File: tests/test_sql_refsols/tpch_q15_ansi.sql

````sql

WITH _t7 AS (

SELECT

l_discount AS discount,

l_extendedprice AS extended_price,

l_shipdate AS ship_date,

l_suppkey AS supplier_key

FROM tpch.lineitem

WHERE

l_shipdate < CAST('1996-04-01' AS DATE)

AND l_shipdate >= CAST('1996-01-01' AS DATE)

), _t1 AS (

SELECT

SUM(extended_price * (

1 - discount

)) AS agg_0,

supplier_key

FROM _t7

GROUP BY

supplier_key

), _t2 AS (

SELECT

MAX(COALESCE(_t1.agg_0, 0)) AS max_revenue

FROM tpch.supplier AS supplier

LEFT JOIN _t1 AS _t1

ON _t1.supplier_key = supplier.s_suppkey

), _t5_2 AS (

SELECT

SUM(extended_price * (

1 - discount

)) AS agg_1,

supplier_key

FROM _t7

GROUP BY

supplier_key

)

SELECT

supplier.s_suppkey AS S_SUPPKEY,

supplier.s_name AS S_NAME,

supplier.s_address AS S_ADDRESS,

supplier.s_phone AS S_PHONE,

COALESCE(_t5.agg_1, 0) AS TOTAL_REVENUE

FROM _t2 AS _t2

CROSS JOIN tpch.supplier AS supplier

LEFT JOIN _t5_2 AS _t5

ON _t5.supplier_key = supplier.s_suppkey

WHERE

_t2.max_revenue = COALESCE(_t5.agg_1, 0)

ORDER BY

supplier.s_suppkey

````

## File: tests/test_sql_refsols/tpch_q15_sqlite.sql

````sql

WITH _t7 AS (

SELECT

l_discount AS discount,

l_extendedprice AS extended_price,

l_shipdate AS ship_date,

l_suppkey AS supplier_key

FROM tpch.lineitem

WHERE

l_shipdate < '1996-04-01' AND l_shipdate >= '1996-01-01'

), _t1 AS (

SELECT

SUM(extended_price * (

1 - discount

)) AS agg_0,

supplier_key

FROM _t7

GROUP BY

supplier_key

), _t2 AS (

SELECT

MAX(COALESCE(_t1.agg_0, 0)) AS max_revenue

FROM tpch.supplier AS supplier

LEFT JOIN _t1 AS _t1

ON _t1.supplier_key = supplier.s_suppkey

), _t5_2 AS (

SELECT

SUM(extended_price * (

1 - discount

)) AS agg_1,

supplier_key

FROM _t7

GROUP BY

supplier_key

)

SELECT

supplier.s_suppkey AS S_SUPPKEY,

supplier.s_name AS S_NAME,

supplier.s_address AS S_ADDRESS,

supplier.s_phone AS S_PHONE,

COALESCE(_t5.agg_1, 0) AS TOTAL_REVENUE

FROM _t2 AS _t2

CROSS JOIN tpch.supplier AS supplier

LEFT JOIN _t5_2 AS _t5

ON _t5.supplier_key = supplier.s_suppkey

WHERE

_t2.max_revenue = COALESCE(_t5.agg_1, 0)

ORDER BY

supplier.s_suppkey

````

## File: tests/test_sql_refsols/tpch_q16_ansi.sql

````sql

WITH _t1_2 AS (

SELECT

COUNT(DISTINCT partsupp.ps_suppkey) AS supplier_count,

COUNT(DISTINCT partsupp.ps_suppkey) AS ordering_1,

part.p_brand,

part.p_brand AS ordering_2,

part.p_size,

part.p_size AS ordering_4,

part.p_type,

part.p_type AS ordering_3

FROM tpch.part AS part

JOIN tpch.partsupp AS partsupp

ON part.p_partkey = partsupp.ps_partkey

LEFT JOIN tpch.supplier AS supplier

ON partsupp.ps_suppkey = supplier.s_suppkey

WHERE

NOT part.p_type LIKE 'MEDIUM POLISHED%%'

AND NOT supplier.s_comment LIKE '%Customer%Complaints%'

AND part.p_brand <> 'BRAND#45'

AND part.p_size IN (49, 14, 23, 45, 19, 3, 36, 9)

GROUP BY

part.p_brand,

part.p_size,

part.p_type

), _t0_2 AS (

SELECT

p_brand,

p_size,

p_type,

supplier_count,

ordering_1,

ordering_2,

ordering_3,

ordering_4

FROM _t1_2

ORDER BY

ordering_1 DESC,

ordering_2,

ordering_3,

ordering_4

LIMIT 10

)

SELECT

p_brand AS P_BRAND,

p_type AS P_TYPE,

p_size AS P_SIZE,

supplier_count AS SUPPLIER_COUNT

FROM _t0_2

ORDER BY

ordering_1 DESC,

ordering_2,

ordering_3,

ordering_4

````

## File: tests/test_sql_refsols/tpch_q16_sqlite.sql

````sql

WITH _t1_2 AS (), ChunkSearchResult(score=0.029, text=## File: tests/test_plan_refsols/padding_functions.txt

````

ROOT(columns=[('original_name', original_name), ('ref_rpad', ref_rpad), ('ref_lpad', ref_lpad), ('right_padded', right_padded), ('left_padded', left_padded), ('truncated_right', truncated_right), ('truncated_left', truncated_left), ('zero_pad_right', zero_pad_right), ('zero_pad_left', zero_pad_left), ('right_padded_space', right_padded_space), ('left_padded_space', left_padded_space)], orderings=[(ordering_0):asc_first])

LIMIT(limit=Literal(value=5, type=Int64Type()), columns={'left_padded': left_padded, 'left_padded_space': left_padded_space, 'ordering_0': ordering_0, 'original_name': original_name, 'ref_lpad': ref_lpad, 'ref_rpad': ref_rpad, 'right_padded': right_padded, 'right_padded_space': right_padded_space, 'truncated_left': truncated_left, 'truncated_right': truncated_right, 'zero_pad_left': zero_pad_left, 'zero_pad_right': zero_pad_right}, orderings=[(ordering_0):asc_first])

PROJECT(columns={'left_padded': left_padded, 'left_padded_space': left_padded_space, 'ordering_0': name, 'original_name': original_name, 'ref_lpad': ref_lpad, 'ref_rpad': ref_rpad, 'right_padded': right_padded, 'right_padded_space': right_padded_space, 'truncated_left': truncated_left, 'truncated_right': truncated_right, 'zero_pad_left': zero_pad_left, 'zero_pad_right': zero_pad_right})

PROJECT(columns={'left_padded': LPAD(name, 30:int64, '#':string), 'left_padded_space': LPAD(name, 30:int64, ' ':string), 'name': name, 'original_name': name, 'ref_lpad': LPAD('Cust0001':string, 30:int64, '*':string), 'ref_rpad': RPAD('Cust0001':string, 30:int64, '*':string), 'right_padded': RPAD(name, 30:int64, '*':string), 'right_padded_space': RPAD(name, 30:int64, ' ':string), 'truncated_left': LPAD(name, 8:int64, '-':string), 'truncated_right': RPAD(name, 8:int64, '-':string), 'zero_pad_left': LPAD(name, 0:int64, '.':string), 'zero_pad_right': RPAD(name, 0:int64, '.':string)})

SCAN(table=main.sbCustomer, columns={'name': sbCustName})

````

## File: tests/test_plan_refsols/parts_quantity_increase_95_96.txt

````

ROOT(columns=[('name', name), ('qty_95', qty_95), ('qty_96', qty_96)], orderings=[(ordering_2):desc_last, (ordering_3):asc_first])

LIMIT(limit=Literal(value=3, type=Int64Type()), columns={'name': name, 'ordering_2': ordering_2, 'ordering_3': ordering_3, 'qty_95': qty_95, 'qty_96': qty_96}, orderings=[(ordering_2):desc_last, (ordering_3):asc_first])

PROJECT(columns={'name': name, 'ordering_2': qty_96 - qty_95, 'ordering_3': name, 'qty_95': qty_95, 'qty_96': qty_96})

PROJECT(columns={'name': name, 'qty_95': DEFAULT_TO(agg_0, 0:int64), 'qty_96': DEFAULT_TO(agg_1, 0:int64)})

JOIN(conditions=[t0.key == t1.part_key], types=['inner'], columns={'agg_0': t0.agg_0, 'agg_1': t1.agg_1, 'name': t0.name})

JOIN(conditions=[t0.key == t1.part_key], types=['inner'], columns={'agg_0': t1.agg_0, 'key': t0.key, 'name': t0.name})

FILTER(condition=STARTSWITH(container, 'SM':string), columns={'key': key, 'name': name})

SCAN(table=tpch.PART, columns={'container': p_container, 'key': p_partkey, 'name': p_name})

AGGREGATE(keys={'part_key': part_key}, aggregations={'agg_0': SUM(quantity)})

JOIN(conditions=[t0.order_key == t1.key], types=['inner'], columns={'part_key': t0.part_key, 'quantity': t0.quantity})

FILTER(condition=ship_mode == 'RAIL':string, columns={'order_key': order_key, 'part_key': part_key, 'quantity': quantity})

SCAN(table=tpch.LINEITEM, columns={'order_key': l_orderkey, 'part_key': l_partkey, 'quantity': l_quantity, 'ship_mode': l_shipmode})

FILTER(condition=YEAR(order_date) == 1995:int64, columns={'key': key})

SCAN(table=tpch.ORDERS, columns={'key': o_orderkey, 'order_date': o_orderdate})

AGGREGATE(keys={'part_key': part_key}, aggregations={'agg_1': SUM(quantity)})

JOIN(conditions=[t0.order_key == t1.key], types=['inner'], columns={'part_key': t0.part_key, 'quantity': t0.quantity})

FILTER(condition=ship_mode == 'RAIL':string, columns={'order_key': order_key, 'part_key': part_key, 'quantity': quantity})), ChunkSearchResult(score=0.029, text=AGGREGATE(keys={}, aggregations={'agg_0': MAX(total_revenue)})

PROJECT(columns={'total_revenue': DEFAULT_TO(agg_0, 0:int64)})

JOIN(conditions=[t0.key == t1.supplier_key], types=['left'], columns={'agg_0': t1.agg_0})

SCAN(table=tpch.SUPPLIER, columns={'key': s_suppkey})

AGGREGATE(keys={'supplier_key': supplier_key}, aggregations={'agg_0': SUM(expr_3)})

PROJECT(columns={'expr_3': extended_price * 1:int64 - discount, 'supplier_key': supplier_key})

FILTER(condition=ship_date < datetime.date(1996, 4, 1):date & ship_date >= datetime.date(1996, 1, 1):date, columns={'discount': discount, 'extended_price': extended_price, 'supplier_key': supplier_key})

SCAN(table=tpch.LINEITEM, columns={'discount': l_discount, 'extended_price': l_extendedprice, 'ship_date': l_shipdate, 'supplier_key': l_suppkey})

SCAN(table=tpch.SUPPLIER, columns={'address': s_address, 'key': s_suppkey, 'name': s_name, 'phone': s_phone})

AGGREGATE(keys={'supplier_key': supplier_key}, aggregations={'agg_1': SUM(expr_4)})

PROJECT(columns={'expr_4': extended_price * 1:int64 - discount, 'supplier_key': supplier_key})

FILTER(condition=ship_date < datetime.date(1996, 4, 1):date & ship_date >= datetime.date(1996, 1, 1):date, columns={'discount': discount, 'extended_price': extended_price, 'supplier_key': supplier_key})

SCAN(table=tpch.LINEITEM, columns={'discount': l_discount, 'extended_price': l_extendedprice, 'ship_date': l_shipdate, 'supplier_key': l_suppkey})

````

## File: tests/test_plan_refsols/tpch_q16.txt

````

ROOT(columns=[('P_BRAND', P_BRAND), ('P_TYPE', P_TYPE), ('P_SIZE', P_SIZE), ('SUPPLIER_COUNT', SUPPLIER_COUNT)], orderings=[(ordering_1):desc_last, (ordering_2):asc_first, (ordering_3):asc_first, (ordering_4):asc_first])

LIMIT(limit=Literal(value=10, type=Int64Type()), columns={'P_BRAND': P_BRAND, 'P_SIZE': P_SIZE, 'P_TYPE': P_TYPE, 'SUPPLIER_COUNT': SUPPLIER_COUNT, 'ordering_1': ordering_1, 'ordering_2': ordering_2, 'ordering_3': ordering_3, 'ordering_4': ordering_4}, orderings=[(ordering_1):desc_last, (ordering_2):asc_first, (ordering_3):asc_first, (ordering_4):asc_first])

PROJECT(columns={'P_BRAND': P_BRAND, 'P_SIZE': P_SIZE, 'P_TYPE': P_TYPE, 'SUPPLIER_COUNT': SUPPLIER_COUNT, 'ordering_1': SUPPLIER_COUNT, 'ordering_2': P_BRAND, 'ordering_3': P_TYPE, 'ordering_4': P_SIZE})

PROJECT(columns={'P_BRAND': p_brand, 'P_SIZE': p_size, 'P_TYPE': p_type, 'SUPPLIER_COUNT': agg_0})

AGGREGATE(keys={'p_brand': p_brand, 'p_size': p_size, 'p_type': p_type}, aggregations={'agg_0': NDISTINCT(supplier_key)})

FILTER(condition=NOT(LIKE(comment_2, '%Customer%Complaints%':string)), columns={'p_brand': p_brand, 'p_size': p_size, 'p_type': p_type, 'supplier_key': supplier_key})

JOIN(conditions=[t0.supplier_key == t1.key], types=['left'], columns={'comment_2': t1.comment, 'p_brand': t0.p_brand, 'p_size': t0.p_size, 'p_type': t0.p_type, 'supplier_key': t0.supplier_key})

JOIN(conditions=[t0.key == t1.part_key], types=['inner'], columns={'p_brand': t0.p_brand, 'p_size': t0.p_size, 'p_type': t0.p_type, 'supplier_key': t1.supplier_key})

PROJECT(columns={'key': key, 'p_brand': brand, 'p_size': size, 'p_type': part_type})

FILTER(condition=brand != 'BRAND#45':string & ISIN(size, [49, 14, 23, 45, 19, 3, 36, 9]:array[unknown]) & NOT(STARTSWITH(part_type, 'MEDIUM POLISHED%':string)), columns={'brand': brand, 'key': key, 'part_type': part_type, 'size': size})

SCAN(table=tpch.PART, columns={'brand': p_brand, 'key': p_partkey, 'part_type': p_type, 'size': p_size})

SCAN(table=tpch.PARTSUPP, columns={'part_key': ps_partkey, 'supplier_key': ps_suppkey})

SCAN(table=tpch.SUPPLIER, columns={'comment': s_comment, 'key': s_suppkey})

````

## File: tests/test_plan_refsols/tpch_q17.txt

````

ROOT(columns=[('AVG_YEARLY', AVG_YEARLY)], orderings=[])

PROJECT(columns={'AVG_YEARLY': DEFAULT_TO(agg_0, 0:int64) / 7.0:float64})

AGGREGATE(keys={}, aggregations={'agg_0': SUM(extended_price)})

FILTER(condition=quantity < 0.2:float64 * part_avg_quantity, columns={'extended_price': extended_price})), ChunkSearchResult(score=0.028, text=## File: tests/test_sql_refsols/tpch_q19_ansi.sql

````sql

WITH _t0_2 AS (

SELECT

SUM(lineitem.l_extendedprice * (

1 - lineitem.l_discount

)) AS agg_0

FROM tpch.lineitem AS lineitem

JOIN tpch.part AS part

ON (

(

lineitem.l_quantity <= 11

AND lineitem.l_quantity >= 1

AND part.p_brand = 'Brand#12'

AND part.p_container IN ('SM CASE', 'SM BOX', 'SM PACK', 'SM PKG')

AND part.p_size <= 5

)

OR (

lineitem.l_quantity <= 20

AND lineitem.l_quantity >= 10

AND part.p_brand = 'Brand#23'

AND part.p_container IN ('MED BAG', 'MED BOX', 'MED PACK', 'MED PKG')

AND part.p_size <= 10

)

OR (

lineitem.l_quantity <= 30

AND lineitem.l_quantity >= 20

AND part.p_brand = 'Brand#34'

AND part.p_container IN ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG')

AND part.p_size <= 15

)

)

AND lineitem.l_partkey = part.p_partkey

AND part.p_size >= 1

WHERE

(

(

lineitem.l_quantity <= 11

AND lineitem.l_quantity >= 1

AND part.p_brand = 'Brand#12'

AND part.p_container IN ('SM CASE', 'SM BOX', 'SM PACK', 'SM PKG')

AND part.p_size <= 5

)

OR (

lineitem.l_quantity <= 20

AND lineitem.l_quantity >= 10

AND part.p_brand = 'Brand#23'

AND part.p_container IN ('MED BAG', 'MED BOX', 'MED PACK', 'MED PKG')

AND part.p_size <= 10

)

OR (

lineitem.l_quantity <= 30

AND lineitem.l_quantity >= 20

AND part.p_brand = 'Brand#34'

AND part.p_container IN ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG')

AND part.p_size <= 15

)

)

AND lineitem.l_shipinstruct = 'DELIVER IN PERSON'

AND lineitem.l_shipmode IN ('AIR', 'AIR REG')

)

SELECT

COALESCE(agg_0, 0) AS REVENUE

FROM _t0_2

````

## File: tests/test_sql_refsols/tpch_q19_sqlite.sql

````sql

WITH _t0_2 AS (

SELECT

SUM(lineitem.l_extendedprice * (

1 - lineitem.l_discount

)) AS agg_0

FROM tpch.lineitem AS lineitem

JOIN tpch.part AS part

ON (

(

lineitem.l_quantity <= 11

AND lineitem.l_quantity >= 1

AND part.p_brand = 'Brand#12'

AND part.p_container IN ('SM CASE', 'SM BOX', 'SM PACK', 'SM PKG')

AND part.p_size <= 5

)

OR (

lineitem.l_quantity <= 20

AND lineitem.l_quantity >= 10

AND part.p_brand = 'Brand#23'

AND part.p_container IN ('MED BAG', 'MED BOX', 'MED PACK', 'MED PKG')

AND part.p_size <= 10

)

OR (

lineitem.l_quantity <= 30

AND lineitem.l_quantity >= 20

AND part.p_brand = 'Brand#34'

AND part.p_container IN ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG')

AND part.p_size <= 15

)

)

AND lineitem.l_partkey = part.p_partkey

AND part.p_size >= 1

WHERE

(

(

lineitem.l_quantity <= 11

AND lineitem.l_quantity >= 1

AND part.p_brand = 'Brand#12'

AND part.p_container IN ('SM CASE', 'SM BOX', 'SM PACK', 'SM PKG')

AND part.p_size <= 5

)

OR (

lineitem.l_quantity <= 20

AND lineitem.l_quantity >= 10

AND part.p_brand = 'Brand#23'

AND part.p_container IN ('MED BAG', 'MED BOX', 'MED PACK', 'MED PKG')

AND part.p_size <= 10

)

OR (

lineitem.l_quantity <= 30

AND lineitem.l_quantity >= 20

AND part.p_brand = 'Brand#34'

AND part.p_container IN ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG')

AND part.p_size <= 15

)

)

AND lineitem.l_shipinstruct = 'DELIVER IN PERSON'

AND lineitem.l_shipmode IN ('AIR', 'AIR REG')

)

SELECT

COALESCE(agg_0, 0) AS REVENUE

FROM _t0_2

````

## File: tests/test_sql_refsols/tpch_q2_ansi.sql

````sql

WITH _t4 AS (

SELECT

r_name AS name,

r_regionkey AS key

FROM tpch.region

WHERE

r_name = 'EUROPE'

), _t5 AS (

SELECT

ps_partkey AS part_key,

ps_suppkey AS supplier_key,

ps_supplycost AS supplycost

FROM tpch.partsupp

), _t16 AS (

SELECT

MIN(_t5.supplycost) AS best_cost,

part.p_partkey AS key_9

FROM tpch.nation AS nation

JOIN _t4 AS _t4

ON _t4.key = nation.n_regionkey

JOIN tpch.supplier AS supplier

ON nation.n_nationkey = supplier.s_nationkey

JOIN _t5 AS _t5

ON _t5.supplier_key = supplier.s_suppkey

JOIN tpch.part AS part

ON _t5.part_key = part.p_partkey AND part.p_size = 15 AND part.p_type LIKE '%BRASS'

GROUP BY

part.p_partkey

), _t17 AS (

SELECT

part.p_partkey AS key_19,

part.p_mfgr AS manufacturer,

nation.n_name,

supplier.s_acctbal,

supplier.s_address,

supplier.s_comment,

supplier.s_name,

supplier.s_phone,), ChunkSearchResult(score=0.028, text="source": [

"## Query 12\n",

"\n",

"This question seeks to determine **the impact of low cost shipping modes on delays for orders of varying priorities**. It does so by counting, by ship mode, for lineitems actually received by customers in a given year, the number of lineitems belonging to orders for which the receipt date exceeds the commit date for two different specified ship modes. Only lineitems that were actually shipped before the commit date are considered. The late lineitems are partitioned into two groups, those with priority `1-URGENT` or `2-HIGH`, and those with a priority other than `1-URGENT` or `2-HIGH`. The chosen year is 1994, and the two chosen ship modes are mail & ship.\n",

"\n",

"\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"SELECT\n",

" L_SHIPMODE,\n",

" SUM(CASE\n",

" WHEN O_ORDERPRIORITY = '1-URGENT'\n",

" OR O_ORDERPRIORITY = '2-HIGH'\n",

" THEN 1\n",

" ELSE 0\n",

" END) AS HIGH_LINE_COUNT,\n",

" SUM(CASE\n",

" WHEN O_ORDERPRIORITY <> '1-URGENT'\n",

" AND O_ORDERPRIORITY <> '2-HIGH'\n",

" THEN 1\n",

" ELSE 0\n",

" END) AS LOW_LINE_COUNT\n",

"FROM\n",

" ORDERS,\n",

" LINEITEM\n",

"WHERE\n",

" O_ORDERKEY = L_ORDERKEY\n",

" AND L_SHIPMODE IN ('MAIL', 'SHIP')\n",

" AND L_COMMITDATE < L_RECEIPTDATE\n",

" AND L_SHIPDATE < L_COMMITDATE\n",

" AND L_RECEIPTDATE >= DATE '1994-01-01'\n",

" AND L_RECEIPTDATE < DATE '1995-01-01'\n",

"GROUP BY\n",

" L_SHIPMODE\n",

"ORDER BY\n",

" L_SHIPMODE;\n",

"```"

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "7daa2e52-9afb-44dd-8d65-326011776532",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"selected_lines = lines.WHERE(\n",

" ((ship_mode == \"MAIL\") | (ship_mode == \"SHIP\"))\n",

" & (ship_date < commit_date)\n",

" & (commit_date < receipt_date)\n",

" & (receipt_date >= datetime.date(1994, 1, 1))\n",

" & (receipt_date < datetime.date(1995, 1, 1))\n",

").CALCULATE(\n",

" is_high_priority=(order.order_priority == \"1-URGENT\")\n",

" | (order.order_priority == \"2-HIGH\"),\n",

")\n",

"output = PARTITION(selected_lines, \"l\", by=ship_mode).CALCULATE(\n",

" L_SHIPMODE=ship_mode,\n",

" HIGH_LINE_COUNT=SUM(l.is_high_priority),\n",

" LOW_LINE_COUNT=SUM(~(l.is_high_priority)),\n",

").ORDER_BY(L_SHIPMODE.ASC())\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "f6f90a64-4a54-4790-bf80-d3b237f5b5a1",

"metadata": {},

"source": [

"## Query 13\n",

"\n",

"This question seeks to **understand the order count of each customer, including any customer who has not placed an order**. More specifically, it determines the distribution of customers by the number of orders they have made, including customers who have no record of orders, past or present. It counts and reports how many customers have no orders, how many have 1, 2, 3, etc. A check is made to ensure that the orders counted do not fall into one of several special categories of orders. Special categories are identified in the order comment column by looking for a particular pattern. The chosen pattern is comments that contain `'special'`, and later contain `'requests'`.\n",

"\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"SELECT\n",

" C_COUNT,\n",

" COUNT(*) AS CUSTDIST\n",

"FROM (\n",

" SELECT\n",

" C_CUSTKEY,\n",

" COUNT(O_ORDERKEY) AS C_COUNT\n",

" FROM\n",

" CUSTOMER\n",

" LEFT OUTER JOIN ORDERS ON C_CUSTKEY = O_CUSTKEY\n",

" AND O_COMMENT NOT LIKE '%special%requests%'\n",

" GROUP BY\n",

" C_CUSTKEY\n",

") C_ORDERS\n",

"GROUP BY\n",

" C_COUNT\n",

"ORDER BY\n",

" CUSTDIST DESC,\n",

" C_COUNT DESC;\n",

"```"

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "522ee934-1e88-4c93-847b-d1757c372eeb",

"metadata": {},

"outputs": [],), ChunkSearchResult(score=0.026, text=# Singular in CALCULATE & WHERE with multiple SINGULARs

⋮----

def singular3()

⋮----

# Singular in ORDER_BY

# Finds the names of the first 5 customers alphabetically, and sorts them

# by the date of the most expensive order they ever made.

⋮----

def singular4()

⋮----

# Singular in TOP_K

# Finds the names of the first 5 customers from nation #6

# by the date of the most expensive high-priority order they ever made.

⋮----

def singular5()

⋮----

# Find the ship date of the most expensive line item per each container

# presented in parts (breaking ties in favor of the smaller ship date).

# Find the 5 containers with the earliest such date, breaking ties

# alphabetically. For the purpose of this question, only shipments made by

# rail and for parts from Brand#13.

top_containers = PARTITION(

highest_price_line = (

⋮----

def singular6()

⋮----

# For each customer in nation #4, what is the first part they received in

# an order handled by clerk #17, and the nation it came from (breaking ties

# in favor of the one with the largest revenue)? Include the 5 customers

# with the earliest such received parts (breaking ties alphabetically by

# customer name).

revenue = extended_price * (1 - discount)

lq = (

selected_customers = Customers.WHERE((nation_key == 4) & HAS(lq))

⋮----

def singular7()

⋮----

# For each supplier in nation #20, what is the most popular part (by # of

# purchases) they supplied in 1994 (breaking ties alphabetically by part

# name)? Include the 5 suppliers with the highest number of purchases along

# with part name, and number of orders (breaking ties alphabetically by

# supplier name).

best_part = (

````

## File: tests/test_documentation.py

````python

"""

Verifies that various documentation files are up to date.

"""

⋮----

def test_function_list()

⋮----

"""

Tests that every function in the operator registry is also part of the

`functions.md` file, unless it is a special name that should not be

mentioned or it is a binary operator.

Note: this test should only be run from the root directory of the project.

"""

# Identify every function that should be documented

special_names = {"NOT", "SLICE"}

function_names: set[str] = set()

⋮----

# Identify every section header in the function documentation

headers: set[str] = set()

⋮----

# Remove any function name that is in the headers, and fail if there are

# any that remain

````

## File: tests/test_exploration.py

````python

"""

Unit tests for the PyDough exploration APIs.

"""

⋮----

"""

Testing data used for `test_metadata_exploration`. Creates a function that

takes in a `graph_fetcher` instance and returns the result of calling

`pydough.explain` on the requested information based on the input

tuple, as well as the expected output string. The input tuple is in one of

the following formats:

`(graph_name, None, None)` -> get metadata for the graph

`(graph_name, collection_name, None)` -> get metadata for a collection

`(graph_name, collection_name, property_name)` -> get metadata for a

property

Returns both the string representations when verbose=True and when

verbose=False.

"""

args: tuple[str, str | None, str | None] = request.param[0]

verbose_refsol: str = request.param[1]

non_verbose_refsol: str = request.param[2]

⋮----

graph_name: str = args[0]

collection_name: str | None = args[1]

property_name: str | None = args[2]

⋮----

def wrapped_test_impl(fetcher: graph_fetcher, verbose: bool)

⋮----

graph: GraphMetadata = fetcher(graph_name)

⋮----

"""

Verifies that `pydough.explain` called on metadata produces the exepcted

strings.

"""

⋮----

explanation_string: str = test_impl(get_sample_graph, verbose)

answer: str = verbose_answer if verbose else non_verbose_answer

⋮----

"""

Verifies that `pydough.explain` called on metadata produces the expected

strings.

"""

graph: GraphMetadata = get_sample_graph(graph_name)), ChunkSearchResult(score=0.026, text=SUM(lineitem.l_extendedprice * (

1 - lineitem.l_discount

)) AS agg_0,

_t7.name AS cust_nation,

EXTRACT(YEAR FROM lineitem.l_shipdate) AS l_year,

_t1.name AS supp_nation

FROM tpch.lineitem AS lineitem

LEFT JOIN tpch.supplier AS supplier

ON lineitem.l_suppkey = supplier.s_suppkey

JOIN _t1 AS _t1

ON _t1.key = supplier.s_nationkey

LEFT JOIN tpch.orders AS orders

ON lineitem.l_orderkey = orders.o_orderkey

JOIN tpch.customer AS customer

ON customer.c_custkey = orders.o_custkey

JOIN _t1 AS _t7

ON _t7.key = customer.c_nationkey

WHERE

(

_t1.name = 'FRANCE' OR _t1.name = 'GERMANY'

)

AND (

_t1.name = 'FRANCE' OR _t7.name = 'FRANCE'

)

AND (

_t1.name = 'GERMANY' OR _t7.name = 'GERMANY'

)

AND (

_t7.name = 'FRANCE' OR _t7.name = 'GERMANY'

)

AND lineitem.l_shipdate <= CAST('1996-12-31' AS DATE)

AND lineitem.l_shipdate >= CAST('1995-01-01' AS DATE)

GROUP BY

_t7.name,

EXTRACT(YEAR FROM lineitem.l_shipdate),

_t1.name

)

SELECT

supp_nation AS SUPP_NATION,

cust_nation AS CUST_NATION,

l_year AS L_YEAR,

COALESCE(agg_0, 0) AS REVENUE

FROM _t1_2

ORDER BY

supp_nation,

cust_nation,

l_year

````

## File: tests/test_sql_refsols/tpch_q7_sqlite.sql

````sql

WITH _t1 AS (

SELECT

n_nationkey AS key,

n_name AS name

FROM tpch.nation

), _t1_2 AS (

SELECT

SUM(lineitem.l_extendedprice * (

1 - lineitem.l_discount

)) AS agg_0,

_t7.name AS cust_nation,

CAST(STRFTIME('%Y', lineitem.l_shipdate) AS INTEGER) AS l_year,

_t1.name AS supp_nation

FROM tpch.lineitem AS lineitem

LEFT JOIN tpch.supplier AS supplier

ON lineitem.l_suppkey = supplier.s_suppkey

JOIN _t1 AS _t1

ON _t1.key = supplier.s_nationkey

LEFT JOIN tpch.orders AS orders

ON lineitem.l_orderkey = orders.o_orderkey

JOIN tpch.customer AS customer

ON customer.c_custkey = orders.o_custkey

JOIN _t1 AS _t7

ON _t7.key = customer.c_nationkey

WHERE

(

_t1.name = 'FRANCE' OR _t1.name = 'GERMANY'

)

AND (

_t1.name = 'FRANCE' OR _t7.name = 'FRANCE'

)

AND (

_t1.name = 'GERMANY' OR _t7.name = 'GERMANY'

)

AND (

_t7.name = 'FRANCE' OR _t7.name = 'GERMANY'

)

AND lineitem.l_shipdate <= '1996-12-31'

AND lineitem.l_shipdate >= '1995-01-01'

GROUP BY

_t7.name,

CAST(STRFTIME('%Y', lineitem.l_shipdate) AS INTEGER),

_t1.name

)

SELECT

supp_nation AS SUPP_NATION,

cust_nation AS CUST_NATION,

l_year AS L_YEAR,

COALESCE(agg_0, 0) AS REVENUE

FROM _t1_2

ORDER BY

supp_nation,

cust_nation,

l_year

````

## File: tests/test_sql_refsols/tpch_q8_ansi.sql

````sql

WITH _t0_2 AS (

SELECT

SUM(

CASE

WHEN nation.n_name = 'BRAZIL'

THEN lineitem.l_extendedprice * (

1 - lineitem.l_discount

)

ELSE 0

END

) AS agg_0,

SUM(lineitem.l_extendedprice * (

1 - lineitem.l_discount

)) AS agg_1,

EXTRACT(YEAR FROM orders.o_orderdate) AS o_year

FROM tpch.nation AS nation

JOIN tpch.supplier AS supplier

ON nation.n_nationkey = supplier.s_nationkey

JOIN tpch.partsupp AS partsupp

ON partsupp.ps_suppkey = supplier.s_suppkey

JOIN tpch.part AS part

ON part.p_partkey = partsupp.ps_partkey AND part.p_type = 'ECONOMY ANODIZED STEEL'

JOIN tpch.lineitem AS lineitem

ON lineitem.l_partkey = partsupp.ps_partkey

AND lineitem.l_suppkey = partsupp.ps_suppkey

JOIN tpch.orders AS orders

ON lineitem.l_orderkey = orders.o_orderkey

AND orders.o_orderdate <= CAST('1996-12-31' AS DATE)

AND orders.o_orderdate >= CAST('1995-01-01' AS DATE)

JOIN tpch.customer AS customer

ON customer.c_custkey = orders.o_custkey

JOIN tpch.nation AS nation_2

ON customer.c_nationkey = nation_2.n_nationkey

JOIN tpch.region AS region

ON nation_2.n_regionkey = region.r_regionkey AND region.r_name = 'AMERICA'

GROUP BY

EXTRACT(YEAR FROM orders.o_orderdate)

)

SELECT

o_year AS O_YEAR,

COALESCE(agg_0, 0) / COALESCE(agg_1, 0) AS MKT_SHARE

FROM _t0_2

````

## File: tests/test_sql_refsols/tpch_q8_sqlite.sql

````sql

WITH _t0_2 AS (

SELECT

SUM(

IIF(

nation.n_name = 'BRAZIL',

lineitem.l_extendedprice * (

1 - lineitem.l_discount

),

0

)

) AS agg_0,

SUM(lineitem.l_extendedprice * (

1 - lineitem.l_discount

)) AS agg_1,), ChunkSearchResult(score=0.016, text="source": [

"## Query 17\n",

"\n",

"This question seeks to determine **how much average yearly revenue would be lost if orders were no longer filled for small quantities of certain parts**. It does so by considering parts of a given brand and with a given container type and determines the average lineitem quantity of such parts ordered for all orders (past and pending) in the 7-year database. What would be the average yearly gross (undiscounted) loss in revenue if orders for these parts with a quantity of less than 20% of this average were no longer taken? The chosen brand and container type are `'Brand#23'` and `MED BOX`, respectively.\n",

"\n",

"\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"select\n",

" sum(l_extendedprice) / 7.0 as avg_yearly\n",

"from\n",

" lineitem,\n",

" part\n",

"where\n",

" p_partkey = l_partkey\n",

" and p_brand = 'Brand#23'\n",

" and p_container = 'MED BOX'\n",

" and l_quantity < (\n",

" select\n",

" 0.2 * avg(l_quantity)\n",

" from\n",

" lineitem\n",

" where\n",

" l_partkey = p_partkey\n",

" )\n",

"```\n",

"\n",

"PyDough bypasses the need for the correlated subquery by first aggregating lineitems by part, then stepping into the lineitems and backreferencing to compare against the per-part average value."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "4824db18-364b-4ba3-98a2-70ee8930c074",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"selected_lines = parts.WHERE(\n",

" (brand == \"Brand#23\") & (container == \"MED BOX\")\n",

").CALCULATE(\n",

" avg_quantity=AVG(lines.quantity)\n",

").lines.WHERE(quantity < 0.2 * avg_quantity)\n",

"output = TPCH.CALCULATE(AVG_YEARLY=SUM(selected_lines.extended_price) / 7.0)\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "ca71d07c-095b-4dd6-82a6-71cdd69be974",

"metadata": {},

"source": [

"## Query 18\n",

"\n",

"This question seeks to **ranks customers based on their status as having placed a large quantity order**. It does so by calculating a list of the top 100 customers who have ever placed large quantity orders. It lists the customer name, customer key, the order key, date and total price and the quantity for the order.\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"select\n",

" c_name,\n",

" c_custkey,\n",

" o_orderkey,\n",

" o_orderdate,\n",

" o_totalprice,\n",

" sum(l_quantity)\n",

"from\n",

" customer,\n",

" orders,\n",

" lineitem\n",

"where\n",

" o_orderkey in (\n",

" select\n",

" l_orderkey\n",

" from\n",

" lineitem\n",

" group by\n",

" l_orderkey \n",

" having\n",

" sum(l_quantity) > 300\n",

" )\n",

" and c_custkey = o_custkey\n",

" and o_orderkey = l_orderkey\n",

"group by\n",

" c_name,\n",

" c_custkey,\n",

" o_orderkey,\n",

" o_orderdate,\n",

" o_totalprice\n",

"order by\n",

" o_totalprice desc,\n",

" o_orderdate;\n",

"```\n",

"\n",

"Notice that PyDough can simplify this by phrasing this as an operation being done per-order, thus eliding the need to do any manual aggregation."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "87292649-b89a-4e0d-a438-74bd1aa9656d",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"output = orders.CALCULATE(\n",

" C_NAME=customer.name,\n",

" C_CUSTKEY=customer.key,\n",

" O_ORDERKEY=key,\n",

" O_ORDERDATE=order_date,\n",

" O_TOTALPRICE=total_price,\n",

" TOTAL_QUANTITY=SUM(lines.quantity),\n",

").WHERE(\n",

" TOTAL_QUANTITY > 300\n",

").TOP_K(100, by=(O_TOTALPRICE.DESC(), O_ORDERDATE.ASC()))\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "b27461d3-9720-4dee-9d40-e519ca01c71b",

"metadata": {},), ChunkSearchResult(score=0.015, text=]

},

{

"cell_type": "code",

"execution_count": null,

"id": "27365f94-32a0-48f1-9589-711d57cf145b",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"selected_parts = (\n",

" nations.CALCULATE(n_name=name)\n",

" .WHERE(region.name == \"EUROPE\")\n",

" .suppliers.CALCULATE(\n",

" s_acctbal=account_balance,\n",

" s_name=name,\n",

" s_address=address,\n",

" s_phone=phone,\n",

" s_comment=comment,\n",

" )\n",

" .supply_records.CALCULATE(\n",

" supplycost=supplycost,\n",

" )\n",

" .part.WHERE(ENDSWITH(part_type, \"BRASS\") & (size == 15))\n",

" )\n",

"part_groups = PARTITION(selected_parts, name=\"p\", by=key).CALCULATE(\n",

" best_cost=MIN(p.supplycost)\n",

")\n",

"output = part_groups.p.WHERE(\n",

" (supplycost == best_cost)\n",

" & ENDSWITH(part_type, \"BRASS\")\n",

" & (size == 15)\n",

").CALCULATE(\n",

" S_ACCTBAL=s_acctbal,\n",

" S_NAME=s_name,\n",

" N_NAME=n_name,\n",

" P_PARTKEY=key,\n",

" P_MFGR=manufacturer,\n",

" S_ADDRESS=s_address,\n",

" S_PHONE=s_phone,\n",

" S_COMMENT=s_comment,\n",

").TOP_K(\n",

" 100,\n",

" by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC()),\n",

")\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "c4979e37-388e-48df-9165-ecd3c71571c1",

"metadata": {},

"source": [

"## Query 3\n",

"\n",

"The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"SELECT\n",

" L_ORDERKEY,\n",

" SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE,\n",

" O_ORDERDATE,\n",

" O_SHIPPRIORITY\n",

"FROM\n",

" CUSTOMER,\n",

" ORDERS,\n",

" LINEITEM\n",

"WHERE\n",

" C_MKTSEGMENT = 'BUILDING'\n",

" AND C_CUSTKEY = O_CUSTKEY\n",

" AND L_ORDERKEY = O_ORDERKEY\n",

" AND O_ORDERDATE < DATE '1995-03-15'\n",

" AND L_SHIPDATE > DATE '1995-03-15'\n",

"GROUP BY\n",

" L_ORDERKEY,\n",

" O_ORDERDATE,\n",

" O_SHIPPRIORITY\n",

"ORDER BY\n",

" REVENUE DESC,\n",

" O_ORDERDATE\n",

"LIMIT 10;\n",

"```\n",

"\n",

"PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "95975cba-e8e2-4ac9-bbc2-874c0ab43418",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"cutoff_date = datetime.date(1995, 3, 15)\n",

"selected_orders = orders.CALCULATE(\n",

" order_date, ship_priority\n",

").WHERE(\n",

" (customer.mktsegment == \"BUILDING\") & (order_date < cutoff_date)\n",

")\n",

"selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)\n",

"output = PARTITION(\n",

" selected_lines, name=\"l\", by=(order_key, order_date, ship_priority)\n",

").CALCULATE(\n",

" L_ORDERKEY=order_key,\n",

" REVENUE=SUM(l.extended_price * (1 - l.discount)),\n",

" O_ORDERDATE=order_date,\n",

" O_SHIPPRIORITY=ship_priority,\n",

").TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "a72bd083-12c7-402e-8b44-22d640308a7f",

"metadata": {},), ChunkSearchResult(score=0.015, text="source": [

"## Query 4\n",

"\n",

"This question seeks to answer **how well the order priority system is working at ensuring that orders are delivered on time within a particular quarter**. It does this by counting the number of orders ordered in a given quarter of a given year in which at least one lineitem was received by the customer later than its committed date. The query lists the count of such orders for each order priority sorted in ascending priority order.\n",

"\n",

"\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"SELECT\n",

" O_ORDERPRIORITY,\n",

" COUNT(*) AS ORDER_COUNT\n",

"FROM\n",

" ORDERS\n",

"WHERE\n",

" O_ORDERDATE >= DATE '1993-07-01'\n",

" AND O_ORDERDATE < DATE '1993-10-01'\n",

" AND EXISTS (\n",

" SELECT 1\n",

" FROM LINEITEM\n",

" WHERE L_ORDERKEY = O_ORDERKEY\n",

" AND L_COMMITDATE < L_RECEIPTDATE\n",

" )\n",

"GROUP BY\n",

" O_ORDERPRIORITY\n",

"ORDER BY\n",

" O_ORDERPRIORITY;\n",

"```\n",

"\n",

"PyDough handles the `exists` functionality through its use of `HAS`, relying on the underlying relationship between collections to simplify the join/table logic."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "e7525d29-7edc-4c41-9c48-c1313d6f07a4",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"selected_lines = lines.WHERE(commit_date < receipt_date)\n",

"selected_orders = orders.WHERE(\n",

" (order_date >= datetime.date(1993, 7, 1))\n",

" & (order_date < datetime.date(1993, 10, 1))\n",

" & HAS(selected_lines)\n",

")\n",

"output = PARTITION(selected_orders, name=\"o\", by=order_priority).CALCULATE(\n",

" O_ORDERPRIORITY=order_priority,\n",

" ORDER_COUNT=COUNT(o),\n",

").ORDER_BY(O_ORDERPRIORITY.ASC())\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "d6fee20d",

"metadata": {},

"source": [

"## Query 5\n",

"\n",

"This question seeks to learn about domestic revenue from suppliers in Asian countries. It does so by calculating, for each Asian country, the total revenue generated by suppliers in that nation shipping a part to a customer from the same nation, only considering shipments ordered in 1994. Revenue volume for all qualifying lineitems in a particular nation is defined as `sum(l_extendedprice * (1 - l_discount))`.\n",

"\n",

"\n",

"\n",

"Here is the corresponding SQL:\n",

"\n",

"```SQL\n",

"select\n",

" N_NAME,\n",

" sum(l_extendedprice * (1 - l_discount)) as REVENUE\n",

"from\n",

" customer,\n",

" orders,\n",

" lineitem,\n",

" supplier,\n",

" nation,\n",

" region\n",

"where\n",

" c_custkey = o_custkey\n",

" and l_orderkey = o_orderkey\n",

" and l_suppkey = s_suppkey\n",

" and c_nationkey = s_nationkey\n",

" and s_nationkey = n_nationkey\n",

" and n_regionkey = r_regionkey\n",

" and r_name = 'ASIA'\n",

" and o_orderdate >= '1994-01-01'\n",

" and o_orderdate < '1995-01-01'\n",

"group by\n",

" n_name\n",

"order by\n",

" revenue desc\n",

"```"

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "4f8eb6d0",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"selected_lines = (\n",

" customers.orders.WHERE(\n",

" (order_date >= datetime.date(1994, 1, 1))\n",

" & (order_date < datetime.date(1995, 1, 1))\n",

" )\n",

" .lines.WHERE(supplier.nation.name == nation_name)\n",

" .CALCULATE(value=extended_price * (1 - discount))\n",

")\n",

"output = (\n",

" nations.CALCULATE(nation_name=name)\n",

" .WHERE(region.name == \"ASIA\")\n",

" .WHERE(HAS(selected_lines))\n",

" .CALCULATE(N_NAME=name, REVENUE=SUM(selected_lines.value))\n",

" .ORDER_BY(REVENUE.DESC())\n",

")\n",

"pydough.to_df(output)"

]

},

{

"cell_type": "markdown",

"id": "c5c4d84b-b3c0-4b58-8635-b1d30ea2946a",

"metadata": {},), ChunkSearchResult(score=0.014, text="source": [

"As you see, PyDough now knows that this expression is composed of `extended_price` and `discount`, but it doesn't know **WHICH** `extended_price` and `discount`. To ultimately develop a legal PyDough statement, we will need to bind uses of this expression to a context that can access `extended_price` and `discount`.\n",

"\n",

"This might seem very minor, but this allows us to define definitions up front, allowing reuse in vastly different contexts.\n",

"\n",

"Now let's use this definition to compute the total revenue."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "7899e4b6-3c41-4790-9855-49e46c7144ba",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"total_revenue = SUM(lines.CALCULATE(line_revenue=revenue_def).line_revenue)\n",

"total_revenue"

]

},

{

"cell_type": "markdown",

"id": "d22eed8e-27a7-4386-872b-80795074bbdf",

"metadata": {},

"source": [

"Now this expression is more meaningful, but it actually still doesn't have a context. If we assign this statement to the global context, our actual TPCH graph, then we can compute the total revenue across all lines."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "4da56ff3-c78e-4fd3-9b45-e5962517fa6a",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"pydough.to_df(TPCH.CALCULATE(total_line_revenue=total_revenue))"

]

},

{

"cell_type": "markdown",

"id": "c4d9df49-4d3f-4b01-a868-a5ae1bf97ac3",

"metadata": {},

"source": [

"In practice though, this may not solve our core question. Instead, we may want to apply a different **context**, say for example total_revenue for each order. We can instead represent that as follows."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "83b821fc-866b-4116-a38c-2797d2a651a0",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",

"order_total_price = orders.CALCULATE(order_revenue=total_revenue)\n",

"pydough.to_df(order_total_price)"

]

},

{

"cell_type": "markdown",

"id": "bfe461f5-f64f-4a37-a840-bc200ca90aa5",

"metadata": {},

"source": [

"Notice that are able to reuse the exact same code, but by swapping the context we can ultimately modify the semantics. This makes testing the underlying behavior much more scalable. To ask is this statement correct, we can instead compose our question to ask:\n",

"* Is this underlying expression correct?\n",

"* Is this context correct?\n",

"\n",

"Since these can be verify independently, we can develop greater confidence in our question since it arises from composable building blocks. We could also generate selected contexts to build clear testing. Here we show reusing the same code but with a selection of 5 lines. If we instead provide a testing context it could be done without any code rewrite"

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "db103386-dbac-41d1-98ef-3facbc4d466e",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"# Compute the sum of the first 5 line numbers, which can be known for testing.\n",

"top_five_lines = lines.TOP_K(5, by=(line_number.ASC(), order_key.ASC()))\n",

"top_five_line_price = TPCH.CALCULATE(total_line_revenue=SUM(top_five_lines.CALCULATE(line_revenue=revenue_def).line_revenue))\n",

"pydough.to_df(top_five_line_price)"

]

},

{

"cell_type": "markdown",

"id": "23e6c569-fc61-4338-ad28-ddbe20aa3b88",

"metadata": {},

"source": [

"Now let's return to extending our question. Building able to compute order sums is great, but we care about results per line. As a result, now we can even extend our orders to an additional context within lines. We will once again define more defintions. Our ratio definition will now ask us to propagate our previous `order_revenue` that we computed (down-streamed from an ancestor context) and compare it to the result of `revenue_def`."

]

},

{

"cell_type": "code",

"execution_count": null,

"id": "037addf9-36ed-440d-b99e-980a43f21303",

"metadata": {},

"outputs": [],

"source": [

"%%pydough\n",

"\n",)], graph_search_results=[], web_search_results=None, document_search_results=None), 'citations': [Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='23d4d72', object='citation', is_new=True, span=None, source_type=None, payload={'id': '23d4d72f-66fe-56e3-90b5-86d7b098ee8a', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.014492753623188406, 'text': '"source": [\n\n"As you see, PyDough now knows that this expression is composed of `extended_price` and `discount`, but it doesn\'t know **WHICH** `extended_price` and `discount`. To ultimately develop a legal PyDough statement, we will need to bind uses of this expression to a context that can access `extended_price` and `discount`.\\n",\n\n"\\n",\n\n"This might seem very minor, but this allows us to define definitions up front, allowing reuse in vastly different contexts.\\n",\n\n"\\n",\n\n"Now let\'s use this definition to compute the total revenue."\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "7899e4b6-3c41-4790-9855-49e46c7144ba",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"total_revenue = SUM(lines.CALCULATE(line_revenue=revenue_def).line_revenue)\\n",\n\n"total_revenue"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "d22eed8e-27a7-4386-872b-80795074bbdf",\n\n"metadata": {},\n\n"source": [\n\n"Now this expression is more meaningful, but it actually still doesn\'t have a context. If we assign this statement to the global context, our actual TPCH graph, then we can compute the total revenue across all lines."\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "4da56ff3-c78e-4fd3-9b45-e5962517fa6a",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"pydough.to_df(TPCH.CALCULATE(total_line_revenue=total_revenue))"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "c4d9df49-4d3f-4b01-a868-a5ae1bf97ac3",\n\n"metadata": {},\n\n"source": [\n\n"In practice though, this may not solve our core question. Instead, we may want to apply a different **context**, say for example total_revenue for each order. We can instead represent that as follows."\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "83b821fc-866b-4116-a38c-2797d2a651a0",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"order_total_price = orders.CALCULATE(order_revenue=total_revenue)\\n",\n\n"pydough.to_df(order_total_price)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "bfe461f5-f64f-4a37-a840-bc200ca90aa5",\n\n"metadata": {},\n\n"source": [\n\n"Notice that are able to reuse the exact same code, but by swapping the context we can ultimately modify the semantics. This makes testing the underlying behavior much more scalable. To ask is this statement correct, we can instead compose our question to ask:\\n",\n\n"* Is this underlying expression correct?\\n",\n\n"* Is this context correct?\\n",\n\n"\\n",\n\n"Since these can be verify independently, we can develop greater confidence in our question since it arises from composable building blocks. We could also generate selected contexts to build clear testing. Here we show reusing the same code but with a selection of 5 lines. If we instead provide a testing context it could be done without any code rewrite"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "db103386-dbac-41d1-98ef-3facbc4d466e",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"# Compute the sum of the first 5 line numbers, which can be known for testing.\\n",\n\n"top_five_lines = lines.TOP_K(5, by=(line_number.ASC(), order_key.ASC()))\\n",\n\n"top_five_line_price = TPCH.CALCULATE(total_line_revenue=SUM(top_five_lines.CALCULATE(line_revenue=revenue_def).line_revenue))\\n",\n\n"pydough.to_df(top_five_line_price)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "23e6c569-fc61-4338-ad28-ddbe20aa3b88",\n\n"metadata": {},\n\n"source": [\n\n"Now let\'s return to extending our question. Building able to compute order sums is great, but we care about results per line. As a result, now we can even extend our orders to an additional context within lines. We will once again define more defintions. Our ratio definition will now ask us to propagate our previous `order_revenue` that we computed (down-streamed from an ancestor context) and compare it to the result of `revenue_def`."\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "037addf9-36ed-440d-b99e-980a43f21303",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",', 'metadata': {'version': 'v0', 'chunk_order': 38, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 8, 'full_text_rank': 24, 'associated_query': '\n    Please provide documentation and explanation for the following Pydough code:\n    \n    Original User Question:\n    Provide a summary pricing report for all line items shipped as of September 2nd of 1998. The summary should list totals for extended price, discounted extended price, discounted extended price plus tax, average quantity, average extended price, average discount, and number of lines, all broken down by the return flag & line status. This is also known as TPC-H query #1.\n    \n    Pydough Generated Code Answering the User Question:\n    disc_price = l.extended_price * (1 - l.discount)\ncharge = disc_price * (1 + l.tax)\nselected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\npartitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))\nresult = partitioned_lines(\n    L_RETURNFLAG=return_flag,\n    L_LINESTATUS=status,\n    SUM_QTY=SUM(l.quantity),\n    SUM_BASE_PRICE=SUM(l.extended_price),\n    SUM_DISC_PRICE=SUM(disc_price),\n    SUM_CHARGE=SUM(charge),\n    AVG_QTY=AVG(l.quantity),\n    AVG_PRICE=AVG(l.extended_price),\n    AVG_DISC=AVG(l.discount),\n    COUNT_ORDER=COUNT(l),\n).ORDER_BY(return_flag.ASC(), status.ASC())\n    \n    Based on information on the provided document only, focus on explaining:\n    1. The Pydough-specific functions and patterns used\n    2. The data flow and transformations\n    3. Any important Pydough best practices demonstrated\n    4. How this code follows Pydough conventions\n    5. How the code addresses the original question\n    6. Include key examples from the search when available. \n    7. Include key code blocks, key descriptions and definitions in your response.\n    8. Don\'t make up any information or code.\n    \n    Key terms to consider: selected_lines = lines, SORTING, AVG_QTY=AVG(l, AVG_DISC=AVG(l, SUM_BASE_PRICE=SUM(l, SUM_QTY=SUM(l, ORDER_BY, COUNT, WHERE, charge = disc_price * (1 + l, AVG, ), PARTITION, disc_price = l, SUM, ASC, AVG_PRICE=AVG(l\n    '}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}}), Citation(id='1abb098', object='citation', is_new=True, span=None, source_type=None, payload={'id': '1abb0987-1386-571a-ba5a-8d688afec0f7', 'document_id': '4376f3de-092f-5691-84d5-66c8bb3ba69c', 'owner_id': 'c4adfdf4-3e3b-5da4-a121-e197b2350600', 'collection_ids': ['d73865ef-5062-5e8d-845a-000e00064c8f'], 'score': 0.04642338900734423, 'text': '"source": [\n\n"## Query 1\\n",\n\n"\\n",\n\n"This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"select\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus,\\n",\n\n"\\tsum(l_quantity) as sum_qty,\\n",\n\n"\\tsum(l_extendedprice) as sum_base_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\\n",\n\n"\\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\\n",\n\n"\\tavg(l_quantity) as avg_qty,\\n",\n\n"\\tavg(l_extendedprice) as avg_price,\\n",\n\n"\\tavg(l_discount) as avg_disc,\\n",\n\n"\\tcount(*) as count_order\\n",\n\n"from\\n",\n\n"\\tlineitem\\n",\n\n"where\\n",\n\n"\\tl_shipdate <= date \'1998-12-01\' - interval \'90\' day\\n",\n\n"group by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"order by\\n",\n\n"\\tl_returnflag,\\n",\n\n"\\tl_linestatus\\n",\n\n"```"\n\n]\n\n},\n\n{\n\n"cell_type": "code",\n\n"execution_count": null,\n\n"id": "59d6e822-f77e-4dc2-b7d8-5cbb41ddf9b6",\n\n"metadata": {},\n\n"outputs": [],\n\n"source": [\n\n"%%pydough\\n",\n\n"\\n",\n\n"disc_price = l.extended_price * (1 - l.discount)\\n",\n\n"charge = disc_price * (1 + l.tax)\\n",\n\n"selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\\n",\n\n"partitioned_lines = PARTITION(selected_lines, name=\\"l\\", by=(return_flag, status))\\n",\n\n"output = partitioned_lines.CALCULATE(\\n",\n\n" L_RETURNFLAG=return_flag,\\n",\n\n" L_LINESTATUS=status,\\n",\n\n" SUM_QTY=SUM(l.quantity),\\n",\n\n" SUM_BASE_PRICE=SUM(l.extended_price),\\n",\n\n" SUM_DISC_PRICE=SUM(disc_price),\\n",\n\n" SUM_CHARGE=SUM(charge),\\n",\n\n" AVG_QTY=AVG(l.quantity),\\n",\n\n" AVG_PRICE=AVG(l.extended_price),\\n",\n\n" AVG_DISC=AVG(l.discount),\\n",\n\n" COUNT_ORDER=COUNT(l),\\n",\n\n").ORDER_BY(return_flag.ASC(), status.ASC())\\n",\n\n"pydough.to_df(output)"\n\n]\n\n},\n\n{\n\n"cell_type": "markdown",\n\n"id": "419981b5-0159-47b2-bc7f-da4e44707f7c",\n\n"metadata": {},\n\n"source": [\n\n"## Query 2\\n",\n\n"\\n",\n\n"This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier\'s account balance, name and nation; the part\'s number and manufacturer; the supplier\'s address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.\\n",\n\n"\\n",\n\n"\\n",\n\n"\\n",\n\n"Here is the corresponding SQL:\\n",\n\n"\\n",\n\n"```SQL\\n",\n\n"SELECT\\n",\n\n" S_ACCTBAL,\\n",\n\n" S_NAME,\\n",\n\n" N_NAME,\\n",\n\n" P_PARTKEY,\\n",\n\n" P_MFGR,\\n",\n\n" S_ADDRESS,\\n",\n\n" S_PHONE,\\n",\n\n" S_COMMENT\\n",\n\n"FROM\\n",\n\n" PART,\\n",\n\n" SUPPLIER,\\n",\n\n" PARTSUPP,\\n",\n\n" NATION,\\n",\n\n" REGION\\n",\n\n"WHERE\\n",\n\n" P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND P_SIZE = 15\\n",\n\n" AND P_TYPE LIKE \'%BRASS\'\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" AND PS_SUPPLYCOST = (\\n",\n\n" SELECT MIN(PS_SUPPLYCOST)\\n",\n\n" FROM PARTSUPP, SUPPLIER, NATION, REGION\\n",\n\n" WHERE P_PARTKEY = PS_PARTKEY\\n",\n\n" AND S_SUPPKEY = PS_SUPPKEY\\n",\n\n" AND S_NATIONKEY = N_NATIONKEY\\n",\n\n" AND N_REGIONKEY = R_REGIONKEY\\n",\n\n" AND R_NAME = \'EUROPE\'\\n",\n\n" )\\n",\n\n"ORDER BY\\n",\n\n" S_ACCTBAL DESC,\\n",\n\n" N_NAME,\\n",\n\n" S_NAME,\\n",\n\n" P_PARTKEY\\n",\n\n"LIMIT 100;\\n",\n\n"```\\n",\n\n"\\n",\n\n"Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. "', 'metadata': {'version': 'v0', 'chunk_order': 22, 'document_type': 'md', 'unstructured_filetype': 'text/plain', 'unstructured_languages': ['eng'], 'partitioned_by_unstructured': True, 'semantic_rank': 7, 'full_text_rank': 1, 'associated_query': '2. Provide a detailed summary of pricing for line items that were shipped on or before September 2, 1998. This should include totals for extended price, discounted extended price, total with tax, as well as averages for quantity, extended price, discount, and the number of line items, organized'}})], 'metadata': {'id': 'msg_01B3Zitz7N63DvZqR63AEUc7', 'choices': [{'finish_reason': 'stop', 'index': 0, 'message': {'refusal': None, 'role': 'assistant', 'function_call': None, 'tool_calls': None, 'structured_content': None}}], 'created': 1746114790, 'model': 'claude-3-7-sonnet-20250219', 'object': 'chat.completion', 'service_tier': None, 'system_fingerprint': None, 'usage': {'prompt_tokens': 31953, 'completion_tokens': 1655, 'total_tokens': 33608}}, 'completion': '# Explanation of Pydough Code for TPC-H Query #1\n\nBased on the provided documentation, I\'ll explain the Pydough code that generates a summary pricing report for line items shipped as of September 2nd, 1998.\n\n## 1. Pydough-specific Functions and Patterns\n\nThe code uses several key Pydough functions and patterns:\n\n### WHERE Function\n```python\nselected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\n```\nThis filters the `lines` collection to only include records where the `ship_date` is on or before September 2nd, 1998 [1abb098].\n\n### PARTITION Function\n```python\npartitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))\n```\nThis groups the filtered lines by `return_flag` and `status`, creating partitions that can be aggregated [1abb098].\n\n### Aggregation Functions\nThe code uses several aggregation functions:\n- `SUM()` - Calculates the sum of values [1abb098]\n- `AVG()` - Calculates the average of values [1abb098]\n- `COUNT()` - Counts the number of records [1abb098]\n\n### ORDER_BY Function\n```python\n.ORDER_BY(return_flag.ASC(), status.ASC())\n```\nThis sorts the results by `return_flag` and `status` in ascending order [1abb098].\n\n## 2. Data Flow and Transformations\n\nThe data flow follows these steps:\n\n1. **Define calculated fields**: First, two expressions are defined for later use:\n   ```python\n   disc_price = l.extended_price * (1 - l.discount)\n   charge = disc_price * (1 + l.tax)\n   ```\n   These are contextless expressions that will be used in aggregations [1abb098].\n\n2. **Filter data**: The code filters line items to only those shipped on or before September 2nd, 1998:\n   ```python\n   selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))\n   ```\n\n3. **Partition data**: The filtered data is then grouped by return flag and line status:\n   ```python\n   partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))\n   ```\n\n4. **Calculate aggregations**: For each partition, various aggregations are calculated:\n   ```python\n   result = partitioned_lines(\n       L_RETURNFLAG=return_flag,\n       L_LINESTATUS=status,\n       SUM_QTY=SUM(l.quantity),\n       SUM_BASE_PRICE=SUM(l.extended_price),\n       SUM_DISC_PRICE=SUM(disc_price),\n       SUM_CHARGE=SUM(charge),\n       AVG_QTY=AVG(l.quantity),\n       AVG_PRICE=AVG(l.extended_price),\n       AVG_DISC=AVG(l.discount),\n       COUNT_ORDER=COUNT(l),\n   )\n   ```\n\n5. **Sort results**: Finally, the results are sorted by return flag and line status:\n   ```python\n   .ORDER_BY(return_flag.ASC(), status.ASC())\n   ```\n\n## 3. Pydough Best Practices Demonstrated\n\nThe code demonstrates several Pydough best practices:\n\n1. **Contextless expressions**: Defining `disc_price` and `charge` as contextless expressions allows them to be reused in different contexts [23d4d72].\n\n2. **Naming partitions**: Using `name="l"` in the PARTITION function creates a clear reference for the partitioned data [1abb098].\n\n3. **Clear column naming**: The output columns are given descriptive names that match the requirements of the query [1abb098].\n\n4. **Efficient data flow**: The code follows a logical flow of filtering, partitioning, aggregating, and sorting [1abb098].\n\n## 4. How This Code Follows Pydough Conventions\n\nThe code follows Pydough conventions in several ways:\n\n1. **Method chaining**: Operations are chained together in a readable sequence [1abb098].\n\n2. **Contextual references**: The code uses the partition name `l` to reference fields within the partition context [1abb098].\n\n3. **Expressive syntax**: The code uses expressive syntax like `return_flag.ASC()` to indicate sorting direction [1abb098].\n\n4. **Declarative style**: The code describes what to compute rather than how to compute it [1abb098].\n\n## 5. How the Code Addresses the Original Question\n\nThe code directly addresses the requirements in the original question:\n\n1. **Filtering by date**: It filters line items shipped as of September 2nd, 1998 [1abb098].\n\n2. **Grouping by return flag and line status**: It partitions data by these two fields [1abb098].\n\n3. **Calculating required metrics**:\n   - Sum of quantity (`SUM_QTY`)\n   - Sum of extended price (`SUM_BASE_PRICE`)\n   - Sum of discounted extended price (`SUM_DISC_PRICE`)\n   - Sum of discounted extended price plus tax (`SUM_CHARGE`)\n   - Average quantity (`AVG_QTY`)\n   - Average extended price (`AVG_PRICE`)\n   - Average discount (`AVG_DISC`)\n   - Count of lines (`COUNT_ORDER`) [1abb098]\n\n4. **Sorting results**: It sorts by return flag and line status as required [1abb098].\n\n## Comparison with SQL\n\nThe Pydough code is a more concise and readable alternative to the equivalent SQL query shown in the documentation [1abb098]:\n\n```sql\nselect\n    l_returnflag,\n    l_linestatus,\n    sum(l_quantity) as sum_qty,\n    sum(l_extendedprice) as sum_base_price,\n    sum(l_extendedprice * (1 - l_discount)) as sum_disc_price,\n    sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,\n    avg(l_quantity) as avg_qty,\n    avg(l_extendedprice) as avg_price,\n    avg(l_discount) as avg_disc,\n    count(*) as count_order\nfrom\n    lineitem\nwhere\n    l_shipdate <= date \'1998-12-01\' - interval \'90\' day\ngroup by\n    l_returnflag,\n    l_linestatus\norder by\n    l_returnflag,\n    l_linestatus\n```\n\nThe Pydough version makes the calculations more explicit by defining intermediate expressions (`disc_price` and `charge`), which improves readability and maintainability.'}
```
