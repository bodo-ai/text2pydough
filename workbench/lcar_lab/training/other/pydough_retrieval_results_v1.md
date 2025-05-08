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
), ASC, disc_price = l, WHERE, AVG_QTY=AVG(l, COUNT, AVG, AVG_DISC=AVG(l, SUM, PARTITION, SORTING, charge = disc_price * (1 + l, ORDER_BY, SUM_QTY=SUM(l, AVG_PRICE=AVG(l, SUM_BASE_PRICE=SUM(l, selected_lines = lines

### Documentation Retrieval Results

#### Generated Documentation
# Explanation of Pydough Code

This code is written in Pydough, a Python-based data processing language that provides a declarative approach to data manipulation. Let me explain the code in detail:

## 1. Pydough-specific Functions and Patterns

### Variable Definitions and Calculations
```python
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
```
These lines define calculated fields that will be used in aggregations later. In Pydough, you can define intermediate calculations before using them in operations [86f2714].

### Data Filtering with WHERE
```python
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
```
The `WHERE` function filters the `lines` collection to include only records where the ship date is on or before September 2, 1998 [86f2714]. This is similar to SQL's WHERE clause.

### Partitioning Data
```python
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
```
The `PARTITION` function groups the filtered data by `return_flag` and `status` [86f2714]. The `name="l"` parameter creates an alias that can be referenced in subsequent operations.

### Aggregation Functions
The code uses several aggregation functions:
- `SUM()`: Calculates the sum of values [86f2714]
- `AVG()`: Calculates the average of values [86f2714]
- `COUNT()`: Counts the number of records [86f2714]

### Sorting with ORDER_BY
```python
.ORDER_BY(return_flag.ASC(), status.ASC())
```
The `ORDER_BY` function sorts the results by `return_flag` and `status` in ascending order [86f2714]. The `ASC()` method specifies ascending order.

## 2. Data Flow and Transformations

The data flows through several transformations:

1. **Initial Data Source**: The code starts with a collection called `lines` [86f2714].

2. **Filtering**: The data is filtered to include only records where `ship_date` is on or before September 2, 1998 [86f2714].

3. **Partitioning**: The filtered data is grouped by `return_flag` and `status` [86f2714].

4. **Calculation**: Two calculated fields are defined:
   - `disc_price`: The discounted price (extended price multiplied by (1 - discount))
   - `charge`: The total charge (discounted price multiplied by (1 + tax)) [86f2714]

5. **Aggregation**: Various aggregations are performed on the partitioned data [86f2714]:
   - Sum of quantity, extended price, discounted price, and charge
   - Average of quantity, extended price, and discount
   - Count of orders

6. **Sorting**: The results are sorted by `return_flag` and `status` in ascending order [86f2714].

## 3. Pydough Best Practices Demonstrated

1. **Meaningful Variable Names**: The code uses descriptive variable names like `disc_price` and `selected_lines` [86f2714].

2. **Intermediate Calculations**: Calculations are defined separately before being used in aggregations, making the code more readable and maintainable [86f2714].

3. **Chaining Operations**: The code chains operations together in a logical sequence, making the data flow clear [86f2714].

4. **Explicit Naming**: The code explicitly names output columns (e.g., `L_RETURNFLAG`, `SUM_QTY`) for clarity [86f2714].

5. **Partitioning with Aliases**: The `PARTITION` function uses the `name` parameter to create an alias, making it easier to reference the partitioned data in subsequent operations [86f2714].

## 4. Pydough Conventions

1. **Capitalized Function Names**: Pydough functions like `WHERE`, `PARTITION`, `SUM`, `AVG`, `COUNT`, and `ORDER_BY` are capitalized [86f2714].

2. **Method Chaining**: Operations are chained together using the dot notation [86f2714].

3. **Parameter Naming**: Parameters are named using lowercase with underscores (e.g., `return_flag`, `status`) [86f2714].

4. **Output Column Naming**: Output columns are named using uppercase with underscores (e.g., `L_RETURNFLAG`, `SUM_QTY`) [86f2714].

5. **Sorting Specification**: Sorting is specified using the `ASC()` method on column references [86f2714].

This code appears to be implementing a summary report of line items, calculating various metrics grouped by return flag and line status, similar to Query 1 in the TPC-H benchmark [86f2714].

#### Source Documentation

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

---


## Example 2

### Question
```
Find, within the European region, for each brass part of size 15, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, list the parts from suppliers with the 100 highest account balances. List the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. This is also known as TPC-H query #2.
```

### Pydough Code
```python
selected_parts = (
    nations.WHERE(region.name == "EUROPE")
    .suppliers.supply_records.part(
        s_acctbal=BACK(2).account_balance,
        s_name=BACK(2).name,
        n_name=BACK(3).name,
        s_address=BACK(2).address,
        s_phone=BACK(2).phone,
        s_comment=BACK(2).comment,
        supplycost=BACK(1).supplycost,
    )
    .WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
)
part_groups = PARTITION(selected_parts, name="p", by=key)(
    best_cost=MIN(p.supplycost)
)
result = part_groups.p.WHERE(
    (supplycost == BACK(1).best_cost)
    & ENDSWITH(part_type, "BRASS")
    & (size == 15)
)(
    S_ACCTBAL=s_acctbal,
    S_NAME=s_name,
    N_NAME=n_name,
    P_PARTKEY=key,
    P_MFGR=manufacturer,
    S_ADDRESS=s_address,
    S_PHONE=s_phone,
    S_COMMENT=s_comment,
).TOP_K(
    100,
    by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC()),
)
```

### Extracted Key Terms
s_name=BACK(2), TOP_K, WHERE, s_comment=BACK(2), PARTITION, s_acctbal=BACK(2), by=(S_ACCTBAL, SORTING, (supplycost == BACK(1), result = part_groups, MIN, n_name=BACK(3), s_address=BACK(2), s_phone=BACK(2), DESC, ), ASC, nations, best_cost=MIN(p, supplycost=BACK(1)

### Documentation Retrieval Results

#### Generated Documentation
# Explanation of Pydough Code

This Pydough code implements a query to find suppliers from Europe who can supply brass parts of size 15 at the minimum cost, sorted by specific criteria. Let me break down the code and explain the Pydough-specific functions, patterns, and best practices demonstrated.

## 1. Pydough-specific Functions and Patterns

### BACK Function
The `BACK` function [82a3091] is used to reference properties from previous steps in the data navigation chain:
```python
s_acctbal=BACK(2).account_balance
s_name=BACK(2).name
n_name=BACK(3).name
```
This allows accessing properties from parent objects in the relationship chain. For example, `BACK(2)` refers to the supplier object, while `BACK(3)` refers to the nation object.

### WHERE Function
The `WHERE` function [86f2714] is used for filtering data based on specified conditions:
```python
nations.WHERE(region.name == "EUROPE")
```
and
```python
.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
```
This filters nations by region and parts by type and size.

### PARTITION Function
The `PARTITION` function [86f2714] is used to group data by specified keys:
```python
part_groups = PARTITION(selected_parts, name="p", by=key)(
    best_cost=MIN(p.supplycost)
)
```
This groups parts by their key and calculates the minimum supply cost for each group.

### TOP_K Function
The `TOP_K` function [82a3091] limits the result set to a specified number of records, sorted by given criteria:
```python
.TOP_K(
    100,
    by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC()),
)
```
This returns the top 100 records sorted by account balance (descending), nation name, supplier name, and part key.

### Aggregation Functions
The code uses `MIN` [82a3091] to find the minimum supply cost for each part:
```python
best_cost=MIN(p.supplycost)
```

## 2. Data Flow and Transformations

The query follows these steps [82a3091]:

1. **Initial Selection**: Start with nations in Europe
   ```python
   nations.WHERE(region.name == "EUROPE")
   ```

2. **Navigation and Property Collection**: Navigate through suppliers, supply records, and parts, collecting properties along the way
   ```python
   .suppliers.supply_records.part(
       s_acctbal=BACK(2).account_balance,
       s_name=BACK(2).name,
       ...
   )
   ```

3. **Filtering Parts**: Filter for brass parts of size 15
   ```python
   .WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
   ```

4. **Partitioning**: Group parts by key and find minimum supply cost
   ```python
   part_groups = PARTITION(selected_parts, name="p", by=key)(
       best_cost=MIN(p.supplycost)
   )
   ```

5. **Final Selection**: Select parts with the minimum supply cost
   ```python
   part_groups.p.WHERE(
       (supplycost == BACK(1).best_cost)
       & ENDSWITH(part_type, "BRASS")
       & (size == 15)
   )
   ```

6. **Output Formatting**: Format the output with renamed columns
   ```python
   (
       S_ACCTBAL=s_acctbal,
       S_NAME=s_name,
       ...
   )
   ```

7. **Sorting and Limiting**: Sort and limit the results
   ```python
   .TOP_K(
       100,
       by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC()),
   )
   ```

## 3. Important Pydough Best Practices Demonstrated

1. **Chaining Operations** [1300cff]: The code chains operations together in a readable, fluent style.

2. **Descriptive Variable Names** [82a3091]: Variables like `selected_parts` and `part_groups` clearly indicate their purpose.

3. **Reusing Filters** [82a3091]: The filter for brass parts of size 15 is reused to ensure consistency.

4. **Efficient Data Navigation** [82a3091]: The code navigates through relationships efficiently, using `BACK` to reference properties from previous steps.

5. **Clear Transformation Steps** [86f2714]: Each step in the transformation is clearly defined and builds on the previous step.

## 4. How This Code Follows Pydough Conventions

1. **Consistent Naming** [82a3091]: The code uses consistent naming conventions, with lowercase for variables and uppercase for output column names.

2. **Proper Indentation** [82a3091]: The code is properly indented to show the structure of the operations.

3. **Logical Grouping** [82a3091]: Related operations are grouped together, making the code easier to understand.

4. **Explicit Column Selection** [82a3091]: The code explicitly selects and renames columns for the output, making the result schema clear.

5. **Efficient Use of Relationships** [ccce295][d6f5d58]: The code leverages the relationship model defined in the schema to navigate between related entities.

This Pydough code effectively implements a complex query to find suppliers from Europe who can supply brass parts of size 15 at the minimum cost, demonstrating many of Pydough's powerful features for data transformation and analysis.

#### Source Documentation

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
%%pydough
selected_lines = orders.WHERE(
 (order_date >= datetime.date(1993, 10, 1))
 & (order_date < datetime.date(1994, 1, 1))
).lines.WHERE(return_flag == "R").CALCULATE(amt=extended_price * (1 - discount))
output = customers.CALCULATE(
 C_CUSTKEY=key
 C_NAME=name
 REVENUE=SUM(selected_lines.amt)
 C_ACCTBAL=acctbal
 N_NAME=nation.name
 C_ADDRESS=address
 C_PHONE=phone
 C_COMMENT=comment
).TOP_K(20, by=(REVENUE.DESC(), C_CUSTKEY.ASC()))
pydough.to_df(output)
]
## Query 11
The question seeks **to identify the most import subset of available part supplies from a particular nation**. It does so by finding, from scanning the available stock of suppliers in a given nation, all the parts that represent a significant percentage of the total value of all available parts. The query displays the part number and the value of those parts in descending order of value. A significant fraction is chosen to mean as at least 0.01%, and the chosen nation is Germany.
Here is the corresponding SQL:
```SQL
SELECT
 PS_PARTKEY
 SUM(PS_SUPPLYCOST * PS_AVAILQTY) AS VALUE
FROM
 PARTSUPP
 SUPPLIER
 NATION
WHERE
 PS_SUPPKEY = S_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_NAME = 'GERMANY'
GROUP BY
 PS_PARTKEY
HAVING
 SUM(PS_SUPPLYCOST * PS_AVAILQTY) > (
 SELECT
 SUM(PS_SUPPLYCOST * PS_AVAILQTY) * 0.0001
 FROM
 PARTSUPP
 SUPPLIER
 NATION
 WHERE
 PS_SUPPKEY = S_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_NAME = 'GERMANY'
 )
ORDER BY
 VALUE DESC;
```
Notice that the SQL query requires a correlated subquery that leverages having to compute the corresponding SUM. PyDough uses a single filter to simplify this logic and ensure that through use of `BACK` the original results can be filtered.
]
outputs": []
%%pydough
is_german_supplier = supplier.nation.name == "GERMANY
selected_records = supply_records.WHERE(is_german_supplier).CALCULATE(metric=supplycost * availqty)
output = TPCH.CALCULATE(min_market_share=SUM(selected_records.metric) * 0.0001).PARTITION(
 selected_records, name="ps", by=part_key
).CALCULATE(
 PS_PARTKEY=part_key, VALUE=SUM(ps.metric)
).WHERE(VALUE > min_market_share).ORDER_BY(VALUE.DESC())
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
## Query 1
This query seeks to determine **the amount of business that was billed, shipped, and returned**. More specifically, it provides a summary pricing report for all line items shipped as of a given date. The date is within 90 days of the greatest ship date contained in the database.
Here is the corresponding SQL:
```SQL
select
\tl_returnflag
\tl_linestatus
\tsum(l_quantity) as sum_qty
\tsum(l_extendedprice) as sum_base_price
\tsum(l_extendedprice * (1 - l_discount)) as sum_disc_price
\tsum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge
\tavg(l_quantity) as avg_qty
\tavg(l_extendedprice) as avg_price
\tavg(l_discount) as avg_disc
\tcount(*) as count_order
from
\tlineitem
where
\tl_shipdate <= date '1998-12-01' - interval '90' day
group by
\tl_returnflag
\tl_linestatus
order by
\tl_returnflag
\tl_linestatus
```
]
outputs": []
%%pydough
disc_price = l.extended_price * (1 - l.discount)
charge = disc_price * (1 + l.tax)
selected_lines = lines.WHERE((ship_date <= datetime.date(1998, 9, 2)))
partitioned_lines = PARTITION(selected_lines, name="l", by=(return_flag, status))
output = partitioned_lines.CALCULATE(
 L_RETURNFLAG=return_flag
 L_LINESTATUS=status
 SUM_QTY=SUM(l.quantity)
 SUM_BASE_PRICE=SUM(l.extended_price)
 SUM_DISC_PRICE=SUM(disc_price)
 SUM_CHARGE=SUM(charge)
 AVG_QTY=AVG(l.quantity)
 AVG_PRICE=AVG(l.extended_price)
 AVG_DISC=AVG(l.discount)
 COUNT_ORDER=COUNT(l)
).ORDER_BY(return_flag.ASC(), status.ASC())
pydough.to_df(output)
]
## Query 2
This question seeks to determine **which supplier should be selected to place an order for a given part in a given region**. More verbosely, it finds, in a given region, for each part of a certain type and size, the supplier who can supply it at minimum cost. If several suppliers in that region offer the desired part type and size at the same (minimum) cost, the query lists the parts from suppliers with the 100 highest account balances. For each supplier, the query lists the supplier's account balance, name and nation; the part's number and manufacturer; the supplier's address, phone number and comment information. The chosen region, part type, and size are Europe, brass parts, and 15, respectively.
Here is the corresponding SQL:
```SQL
SELECT
 S_ACCTBAL
 S_NAME
 N_NAME
 P_PARTKEY
 P_MFGR
 S_ADDRESS
 S_PHONE
 S_COMMENT
FROM
 PART
 SUPPLIER
 PARTSUPP
 NATION
 REGION
WHERE
 P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND P_SIZE = 15
 AND P_TYPE LIKE '%BRASS'
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 AND PS_SUPPLYCOST = (
 SELECT MIN(PS_SUPPLYCOST)
 FROM PARTSUPP, SUPPLIER, NATION, REGION
 WHERE P_PARTKEY = PS_PARTKEY
 AND S_SUPPKEY = PS_SUPPKEY
 AND S_NATIONKEY = N_NATIONKEY
 AND N_REGIONKEY = R_REGIONKEY
 AND R_NAME = 'EUROPE'
 )
ORDER BY
 S_ACCTBAL DESC
 N_NAME
 S_NAME
 P_PARTKEY
LIMIT 100;
```
Notice the use of a correlated subqueries to determine the `PS_SUPPLYCOST` criteria. In PyDough this is handled naturally by simply first peforming the partition, applying the filter, and then navigating back to `selected_parts` in question, which avoids fully stepping out of the query. 

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
lines": {
type": "compound
primary_property": "supply_records
secondary_property": "lines
singular": false
no_collisions": true
inherited_properties": {"ps_part": "part", "ps_availqty": "availqty"}
reverse_relationship_name": "supplier
Lineitems": {
type": "simple_table
table_path": "tpch.LINEITEM
unique_properties": [["part_key", "supplier_key", "order_key"]]
properties": {
order_key": {"type": "table_column", "column_name": "l_orderkey", "data_type": "int64"}
part_key": {"type": "table_column", "column_name": "l_partkey", "data_type": "int64"}
supplier_key": {"type": "table_column", "column_name": "l_suppkey", "data_type": "int64"}
part_and_supplier": {
type": "simple_join
other_collection_name": "PartSupp
singular": true
no_collisions": false
keys": {"part_key": ["part_key"], "supplier_key": ["supplier_key"]}
reverse_relationship_name": "lines
PartSupp": {
type": "simple_table
table_path": "tpch.PARTSUPP
unique_properties": [["part_key", "supplier_key"]]
properties": {
part_key": {"type": "table_column", "column_name": "ps_partkey", "data_type": "int64"}
supplier_key": {"type": "table_column", "column_name": "ps_suppkey", "data_type": "int64"}
availqty": {"type": "table_column", "column_name": "ps_availqty", "data_type": "decimal[12,2]"}
PARTSUPP_FORMAT_48": {
Parts": {
type": "simple_table
table_path": "tpch.PART
unique_properties": ["key"]
properties": {
key": {"type": "table_column", "column_name": "p_partkey", "data_type": "int64"}
supply_records": {
type": "simple_join
other_collection_name": "PartSupp
singular": false
no_collisions": true
keys": {"key": ["part_key"]}
reverse_relationship_name": "part
suppliers_of_part": {
type": "compound
primary_property": "supply_records
secondary_property": "lines
singular": false
no_collisions": false
inherited_properties": {"ps_lines": "lines", "ps_availqty": "availqty"}
reverse_relationship_name": "parts_supplied
lines": {
type": "compound
primary_property": "supply_records
secondary_property": "suppliers_of_part
singular": false
no_collisions": true
inherited_properties": {"ps_supplier": "supplier", "ps_availqty": "availqty"}
reverse_relationship_name": "part
Suppliers": {
type": "simple_table
table_path": "tpch.SUPPLIER
unique_properties": ["key"]
properties": {
key": {"type": "table_column", "column_name": "s_suppkey", "data_type": "int64"}
supply_records": {
type": "simple_join
other_collection_name": "PartSupp
singular": false
no_collisions": true
keys": {"key": ["supplier_key"]}
reverse_relationship_name": "supplier
lines": {
type": "compound
primary_property": "supply_records
secondary_property": "lines
singular": false
no_collisions": true
inherited_properties": {"ps_part": "part", "ps_availqty": "availqty"}
reverse_relationship_name": "supplier
Lineitems": {
type": "simple_table
table_path": "tpch.LINEITEM
unique_properties": [["part_key", "supplier_key", "order_key"]]
properties": {
order_key": {"type": "table_column", "column_name": "l_orderkey", "data_type": "int64"}
part_key": {"type": "table_column", "column_name": "l_partkey", "data_type": "int64"}
supplier_key": {"type": "table_column", "column_name": "l_suppkey", "data_type": "int64"}
part_and_supplier": {
type": "simple_join
other_collection_name": "PartSupp
singular": true
no_collisions": false
keys": {"part_key": ["part_key"], "supplier_key": ["supplier_key"]}
reverse_relationship_name": "lines
PartSupp": {
type": "simple_table
table_path": "tpch.PARTSUPP
unique_properties": [["part_key", "supplier_key"]]
properties": {
part_key": {"type": "table_column", "column_name": "ps_partkey", "data_type": "int64"}
supplier_key": {"type": "table_column", "column_name": "ps_suppkey", "data_type": "int64"}

##### Source
properties": {
order_key": {"type": "table_column", "column_name": "l_orderkey", "data_type": "int64"}
part_key": {"type": "table_column", "column_name": "l_partkey", "data_type": "int64"}
supplier_key": {"type": "table_column", "column_name": "l_suppkey", "data_type": "int64"}
line_number": {"type": "table_column", "column_name": "l_linenumber", "data_type": "int8"}
quantity": {"type": "table_column", "column_name": "l_quantity", "data_type": "decimal[12,2]"}
extended_price": {"type": "table_column", "column_name": "l_extendedprice", "data_type": "decimal[12,2]"}
discount": {"type": "table_column", "column_name": "l_discount", "data_type": "decimal[12,2]"}
tax": {"type": "table_column", "column_name": "l_tax", "data_type": "decimal[12,2]"}
status": {"type": "table_column", "column_name": "l_linestatus", "data_type": "string"}
ship_date": {"type": "table_column", "column_name": "l_shipdate", "data_type": "date"}
commit_date": {"type": "table_column", "column_name": "l_commitdate", "data_type": "date"}
receipt_date": {"type": "table_column", "column_name": "l_receiptdate", "data_type": "date"}
ship_instruct": {"type": "table_column", "column_name": "l_shipinstruct", "data_type": "string"}
ship_mode": {"type": "table_column", "column_name": "l_shipmode", "data_type": "string"}
return_flag": {"type": "table_column", "column_name": "l_returnflag", "data_type": "string"}
comment": {"type": "table_column", "column_name": "l_comment", "data_type": "string"}
part_and_supplier": {
type": "simple_join
other_collection_name": "PartSupp
singular": true
no_collisions": false
keys": {"part_key": ["part_key"], "supplier_key": ["supplier_key"]}
reverse_relationship_name": "lines
order": {
type": "simple_join
other_collection_name": "Orders
singular": true
no_collisions": false
keys": {"order_key": ["key"]}
reverse_relationship_name": "lines
PartSupp": {
type": "simple_table
table_path": "tpch.PARTSUPP
unique_properties": [["part_key", "supplier_key"]]
properties": {
part_key": {"type": "table_column", "column_name": "ps_partkey", "data_type": "int64"}
supplier_key": {"type": "table_column", "column_name": "ps_suppkey", "data_type": "int64"}
availqty": {"type": "table_column", "column_name": "ps_availqty", "data_type": "decimal[12,2]"}
supplycost": {"type": "table_column", "column_name": "ps_supplycost", "data_type": "decimal[12,2]"}
comment": {"type": "table_column", "column_name": "ps_comment", "data_type": "string"}
Orders": {
type": "simple_table
table_path": "tpch.ORDERS
unique_properties": ["key"]
properties": {
key": {"type": "table_column", "column_name": "o_orderkey", "data_type": "int64"}
customer_key": {"type": "table_column", "column_name": "o_custkey", "data_type": "int64"}
order_status": {"type": "table_column", "column_name": "o_orderstatus", "data_type": "decimal[12,2]"}
total_price": {"type": "table_column", "column_name": "o_totalprice", "data_type": "decimal[12,2]"}
order_date": {"type": "table_column", "column_name": "o_orderdate", "data_type": "date"}
order_priority": {"type": "table_column", "column_name": "o_orderpriority", "data_type": "int64"}
clerk": {"type": "table_column", "column_name": "o_clerk", "data_type": "int64"}
ship_priority": {"type": "table_column", "column_name": "o_shippriority", "data_type": "int64"}
comment": {"type": "table_column", "column_name": "o_comment", "data_type": "string"}
customer": {
type": "simple_join
other_collection_name": "Customers
singular": true
no_collisions": false
keys": {"customer_key": ["key"]}
reverse_relationship_name": "orders
shipping_nation": {
type": "compound
primary_property": "customer
secondary_property": "nation
singular": true
no_collisions": false
inherited_properties": {}
reverse_relationship_name": "orders_shipped_to

---


## Example 3

### Question
```
Find the 10 unshipped orders with the highest value. Retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of March 15th, 1995. orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist meeting the criteria, only the 10 orders with the largest revenue are listed. This is also known as TPC-H query #3.
```

### Pydough Code
```python
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.WHERE(
    (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)(
    BACK(1).order_date,
    BACK(1).ship_priority,
)
result = PARTITION(
    selected_lines, name="l", by=(order_key, order_date, ship_priority)
)(
    L_ORDERKEY=order_key,
    REVENUE=SUM(l.extended_price * (1 - l.discount)),
    O_ORDERDATE=order_date,
    O_SHIPPRIORITY=ship_priority,
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
```

### Extracted Key Terms
), ASC, (customer, BACK(1), TOP_K, WHERE, selected_orders = orders, REVENUE=SUM(l, cutoff_date = datetime, DESC, SUM, PARTITION, selected_lines = selected_orders, SORTING

### Documentation Retrieval Results

#### Generated Documentation
# Explanation of Pydough Code

This code is implementing a query that finds the top 10 unshipped orders with the highest revenue potential. Let me break down the Pydough code and explain its components, patterns, and best practices.

## 1. Pydough-specific Functions and Patterns

### WHERE Function
The `WHERE` function [82a3091] is used to filter collections based on specified conditions:
```python
selected_orders = orders.WHERE(
    (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
```
This filters orders to only include those from customers in the "BUILDING" market segment and with order dates before the cutoff date.

### BACK Function
The `BACK` function [82a3091] is used to reference parent collections in a chain. In this code:
```python
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)(
    BACK(1).order_date,
    BACK(1).ship_priority,
)
```
`BACK(1)` refers to the parent collection (`selected_orders`), allowing access to its fields.

### PARTITION Function
The `PARTITION` function [82a3091] groups data by specified keys and allows aggregations within those groups:
```python
result = PARTITION(
    selected_lines, name="l", by=(order_key, order_date, ship_priority)
)
```
This groups the selected line items by order key, order date, and shipping priority.

### TOP_K Function
The `TOP_K` function [acf5471] sorts and limits results to the top K records based on specified ordering criteria:
```python
.TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
```
This returns the top 10 results ordered by revenue (descending), order date (ascending), and order key (ascending).

## 2. Data Flow and Transformations

The code follows a clear data transformation pipeline [82a3091]:

1. **Initial Filtering**: First, it filters orders based on market segment and order date.
   ```python
   cutoff_date = datetime.date(1995, 3, 15)
   selected_orders = orders.WHERE(
       (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
   )
   ```

2. **Relationship Navigation and Secondary Filtering**: It then navigates to the line items of those orders and applies another filter for unshipped items.
   ```python
   selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)(
       BACK(1).order_date,
       BACK(1).ship_priority,
   )
   ```

3. **Grouping and Aggregation**: The filtered line items are grouped by order key, order date, and shipping priority, and revenue is calculated.
   ```python
   result = PARTITION(
       selected_lines, name="l", by=(order_key, order_date, ship_priority)
   )(
       L_ORDERKEY=order_key,
       REVENUE=SUM(l.extended_price * (1 - l.discount)),
       O_ORDERDATE=order_date,
       O_SHIPPRIORITY=ship_priority,
   )
   ```

4. **Sorting and Limiting**: Finally, it sorts the results by revenue (descending), order date, and order key, and returns the top 10.
   ```python
   .TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
   ```

## 3. Important Pydough Best Practices Demonstrated

1. **Clear Variable Naming** [82a3091]: Variables like `cutoff_date`, `selected_orders`, and `selected_lines` clearly indicate their purpose.

2. **Logical Filtering Order** [82a3091]: The code filters data as early as possible in the pipeline, reducing the amount of data processed in later steps.

3. **Efficient Relationship Navigation** [82a3091]: The code uses relationship navigation (`orders.lines`) to efficiently access related data.

4. **Proper Use of BACK** [82a3091]: The code uses `BACK(1)` to reference parent collection fields when needed.

5. **Explicit Field Naming** [82a3091]: In the final result, fields are explicitly named (e.g., `L_ORDERKEY=order_key`), making the output schema clear.

6. **Appropriate Sorting** [acf5471]: The code uses appropriate sorting criteria with `TOP_K`, including proper use of `DESC()` and `ASC()` to specify sort direction.

## 4. How This Code Follows Pydough Conventions

1. **Consistent Capitalization** [82a3091]: Pydough functions like `WHERE`, `PARTITION`, and `TOP_K` are capitalized, while variables and fields use lowercase with underscores.

2. **Chained Method Calls** [82a3091]: The code uses method chaining for readability and conciseness.

3. **Parentheses for Conditions** [82a3091]: Complex conditions in `WHERE` clauses are properly grouped with parentheses.

4. **Named Parameters** [82a3091]: The code uses named parameters for clarity (e.g., `name="l"`, `by=(...)`).

5. **Consistent Formatting** [82a3091]: The code maintains consistent indentation and formatting throughout.

This query is equivalent to SQL Query 3 from the TPC-H benchmark [82a3091], which finds the shipping priority and potential revenue of orders with the largest revenue among those that had not been shipped as of a given date.

#### Source Documentation

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
People.ORDER_BY(first_name, last_name.DESC(), COUNT(packages))
```
This is valid because the collation term is by default ascending based on the `collation_default_asc` config. Setting the `propagate_collation` config to `True` will cause the collation to be propagated to the `COUNT(packages)` term. Hence its equivalent to:
```py
%%pydough
People.ORDER_BY(first_name.ASC(), last_name.DESC(), COUNT(packages).DESC())
```
`COUNT(packages)` becomes a descending term because `propagate_collation` is `True` and the previous term `last_name.DESC()` is descending.
`first_name` is ascending because `collation_default_asc` is `True` and `first_name` is the first term. The `propagate_collation` config does not affect the collation of the first term.
**Bad Example #1**: Sort each person by their account balance in descending order. This is invalid because the `People` collection does not have an `account_balance` property.
```py
%%pydough
People.ORDER_BY(account_balance.DESC())
```
**Bad Example #2**: Sort each address by the birth date of the people who live there. This is invalid because `current_occupants` is a plural property of `Addresses`, so `current_occupants.birth_date` is plural and cannot be used as an ordering term unless aggregated.
```py
%%pydough
Addresses.ORDER_BY(current_occupants.ASC())
```
**Bad Example #3**: Same as good example #5, but incorrect because `state` and `city` were not made available for down-streaming.
```py
%%pydough
Addresses.WHERE(
state == "OHIO
).current_occupants.ORDER_BY(
state.ASC()
city.ASC()
ssn.ASC()
)
```
**Bad Example #4**: Sort every person. This is invalid because no collation terms are provided.
```py
%%pydough
People.ORDER_BY()
```
<!-- TOC --><a name="top_k"></a>
### TOP_K
A similar operation to `ORDER_BY` is `TOP_K`. The `TOP_K` operation also sorts a collection, but then uses the ordered results in order to pick the first `k`, values, where `k` is a provided constant.
The syntax for this is `.TOP_K(k, by=...)` where `k` is a positive integer and the `by` clause is either a single collation term (as seen in `ORDER_BY`) or an iterable of collation terms (e.g. a list or tuple). The same restrictions as `ORDER_BY` apply to `TOP_K` regarding their collation terms.
PyDough provides `collation_default_asc` and `propagate_collation` configs to control the default collation and whether to propagate the collation if the current expression is not a collation expression. Please see the [Session Configs](./usage.md#session-configs) documentation for more details.
The terms in the collection are unchanged by the `TOP_K` clause, since the only change is the order of the records and which ones are kept/dropped.
**Good Example #1**: Find the 10 people who have ordered the most packages, including their first/last name, birth date, and the number of packages. If there is a tie, break it by the lowest ssn.
```py
%%pydough
People.CALCULATE(
first_name
last_name
birth_date
n_packages=COUNT(packages)
).TOP_K(10, by=(n_packages.DESC(), ssn.ASC()))
```
**Good Example #2**: Find the 5 most recently shipped packages, with ties broken arbitrarily.
```py
%%pydough
Packages.TOP_K(5, by=order_date.DESC())
```
**Good Example #3**: Find the 100 addresses that have most recently had packages either shipped or billed to them, breaking ties arbitrarily.
```py
%%pydough
default_date = datetime.date(1970, 1, 1)
most_recent_ship = DEFAULT_TO(MAX(packages_shipped.order_date), default_date)
most_recent_bill = DEFAULT_TO(MAX(packages_billed.order_date), default_date)
most_recent_package = IFF(most_recent_ship < most_recent_bill, most_recent_ship, most_recent_bill)
Addresses.TOP_K(10, by=most_recent_package.DESC())
```
**Good Example #4**: Find the top 3 people who have spent the most money on packages, including their first/last name, and the total cost of all of their packages.
```py
%%pydough
People.CALCULATE(
first_name
last_name
total_package_cost=SUM(packages.package_cost)

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
People.ORDER_BY(first_name, last_name.DESC(), COUNT(packages))
```
This is valid because the collation term is by default ascending based on the `collation_default_asc` config. Setting the `propagate_collation` config to `True` will cause the collation to be propagated to the `COUNT(packages)` term. Hence its equivalent to:
```py
%%pydough
People.ORDER_BY(first_name.ASC(), last_name.DESC(), COUNT(packages).DESC())
```
`COUNT(packages)` becomes a descending term because `propagate_collation` is `True` and the previous term `last_name.DESC()` is descending.
`first_name` is ascending because `collation_default_asc` is `True` and `first_name` is the first term. The `propagate_collation` config does not affect the collation of the first term.
**Bad Example #1**: Sort each person by their account balance in descending order. This is invalid because the `People` collection does not have an `account_balance` property.
```py
%%pydough
People.ORDER_BY(account_balance.DESC())
```
**Bad Example #2**: Sort each address by the birth date of the people who live there. This is invalid because `current_occupants` is a plural property of `Addresses`, so `current_occupants.birth_date` is plural and cannot be used as an ordering term unless aggregated.
```py
%%pydough
Addresses.ORDER_BY(current_occupants.ASC())
```
**Bad Example #3**: Same as good example #5, but incorrect because `state` and `city` were not made available for down-streaming.
```py
%%pydough
Addresses.WHERE(
state == "OHIO
).current_occupants.ORDER_BY(
state.ASC()
city.ASC()
ssn.ASC()
)
```
**Bad Example #4**: Sort every person. This is invalid because no collation terms are provided.
```py
%%pydough
People.ORDER_BY()
```
<!-- TOC --><a name="top_k"></a>
### TOP_K
A similar operation to `ORDER_BY` is `TOP_K`. The `TOP_K` operation also sorts a collection, but then uses the ordered results in order to pick the first `k`, values, where `k` is a provided constant.
The syntax for this is `.TOP_K(k, by=...)` where `k` is a positive integer and the `by` clause is either a single collation term (as seen in `ORDER_BY`) or an iterable of collation terms (e.g. a list or tuple). The same restrictions as `ORDER_BY` apply to `TOP_K` regarding their collation terms.
PyDough provides `collation_default_asc` and `propagate_collation` configs to control the default collation and whether to propagate the collation if the current expression is not a collation expression. Please see the [Session Configs](./usage.md#session-configs) documentation for more details.
The terms in the collection are unchanged by the `TOP_K` clause, since the only change is the order of the records and which ones are kept/dropped.
**Good Example #1**: Find the 10 people who have ordered the most packages, including their first/last name, birth date, and the number of packages. If there is a tie, break it by the lowest ssn.
```py
%%pydough
People.CALCULATE(
first_name
last_name
birth_date
n_packages=COUNT(packages)
).TOP_K(10, by=(n_packages.DESC(), ssn.ASC()))
```
**Good Example #2**: Find the 5 most recently shipped packages, with ties broken arbitrarily.
```py
%%pydough
Packages.TOP_K(5, by=order_date.DESC())
```
**Good Example #3**: Find the 100 addresses that have most recently had packages either shipped or billed to them, breaking ties arbitrarily.
```py
%%pydough
default_date = datetime.date(1970, 1, 1)
most_recent_ship = DEFAULT_TO(MAX(packages_shipped.order_date), default_date)
most_recent_bill = DEFAULT_TO(MAX(packages_billed.order_date), default_date)
most_recent_package = IFF(most_recent_ship < most_recent_bill, most_recent_ship, most_recent_bill)
Addresses.TOP_K(10, by=most_recent_package.DESC())
```
**Good Example #4**: Find the top 3 people who have spent the most money on packages, including their first/last name, and the total cost of all of their packages.
```py
%%pydough
People.CALCULATE(
first_name
last_name
total_package_cost=SUM(packages.package_cost)

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

##### Source
]
outputs": []
%%pydough
selected_parts = (
 nations.CALCULATE(n_name=name)
 .WHERE(region.name == "EUROPE")
 .suppliers.CALCULATE(
 s_acctbal=account_balance
 s_name=name
 s_address=address
 s_phone=phone
 s_comment=comment
 )
 .supply_records.CALCULATE(
 supplycost=supplycost
 )
 .part.WHERE(ENDSWITH(part_type, "BRASS") & (size == 15))
 )
part_groups = PARTITION(selected_parts, name="p", by=key).CALCULATE(
 best_cost=MIN(p.supplycost)
)
output = part_groups.p.WHERE(
 (supplycost == best_cost)
 & ENDSWITH(part_type, "BRASS")
 & (size == 15)
).CALCULATE(
 S_ACCTBAL=s_acctbal
 S_NAME=s_name
 N_NAME=n_name
 P_PARTKEY=key
 P_MFGR=manufacturer
 S_ADDRESS=s_address
 S_PHONE=s_phone
 S_COMMENT=s_comment
).TOP_K(
 100
 by=(S_ACCTBAL.DESC(), N_NAME.ASC(), S_NAME.ASC(), P_PARTKEY.ASC())
)
pydough.to_df(output)
]
## Query 3
The question seeks to find **the 10 unshipped orders with the highest value**. More verbosely, it retrieves the shipping priority and potential revenue, defined as the sum of the extended price times one minus the discount, of the orders having the largest revenue among those that had not been shipped as of a given date. Orders are listed in decreasing order of revenue. If more than 10 unshipped orders exist, only the 10 orders with the largest revenue are listed.
Here is the corresponding SQL:
```SQL
SELECT
 L_ORDERKEY
 SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) AS REVENUE
 O_ORDERDATE
 O_SHIPPRIORITY
FROM
 CUSTOMER
 ORDERS
 LINEITEM
WHERE
 C_MKTSEGMENT = 'BUILDING'
 AND C_CUSTKEY = O_CUSTKEY
 AND L_ORDERKEY = O_ORDERKEY
 AND O_ORDERDATE < DATE '1995-03-15'
 AND L_SHIPDATE > DATE '1995-03-15'
GROUP BY
 L_ORDERKEY
 O_ORDERDATE
 O_SHIPPRIORITY
ORDER BY
 REVENUE DESC
 O_ORDERDATE
LIMIT 10;
```
PyDough allows us to first derive `selected_lines` as the data to be partitioned, before grouping it by certain partition keys to compute the aggregations.
]
outputs": []
%%pydough
cutoff_date = datetime.date(1995, 3, 15)
selected_orders = orders.CALCULATE(
 order_date, ship_priority
).WHERE(
 (customer.mktsegment == "BUILDING") & (order_date < cutoff_date)
)
selected_lines = selected_orders.lines.WHERE(ship_date > cutoff_date)
output = PARTITION(
 selected_lines, name="l", by=(order_key, order_date, ship_priority)
).CALCULATE(
 L_ORDERKEY=order_key
 REVENUE=SUM(l.extended_price * (1 - l.discount))
 O_ORDERDATE=order_date
 O_SHIPPRIORITY=ship_priority
).TOP_K(10, by=(REVENUE.DESC(), O_ORDERDATE.ASC(), L_ORDERKEY.ASC()))
pydough.to_df(output)
]

---
