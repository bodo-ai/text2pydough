# SQL Cheatsheet

## Basic SQL Syntax

### SELECT Statement
```sql
SELECT column1, column2, ...
FROM table_name
WHERE condition;
```

### JOIN Types
- INNER JOIN: Returns records that have matching values in both tables
- LEFT JOIN: Returns all records from the left table and matched records from the right table
- RIGHT JOIN: Returns all records from the right table and matched records from the left table
- FULL JOIN: Returns all records when there is a match in either left or right table

### Common Functions
- COUNT(): Counts the number of rows
- SUM(): Adds up the values in a column
- AVG(): Calculates the average of values in a column
- MAX(): Returns the maximum value in a column
- MIN(): Returns the minimum value in a column

### GROUP BY
```sql
SELECT column1, COUNT(column2)
FROM table_name
GROUP BY column1;
```

### ORDER BY
```sql
SELECT column1, column2
FROM table_name
ORDER BY column1 ASC|DESC;
```

### HAVING
```sql
SELECT column1, COUNT(column2)
FROM table_name
GROUP BY column1
HAVING COUNT(column2) > value;
``` 