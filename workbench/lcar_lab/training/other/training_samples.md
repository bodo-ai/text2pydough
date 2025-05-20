# Pydough Training Examples

## Question
How many singers do we have?
Database Schema:
{"concert_singer": {"concerts": {"type": "simple_table", "table_path": "main.concert", "unique_properties": ["concert_id"], "properties": {"concert_id": {"type": "table_column", "column_name": "concert_id", "data_type": "string"}, "concert_name": {"type": "table_column", "column_name": "concert_name", "data_type": "string"}, "theme": {"type": "table_column", "column_name": "theme", "data_type": "string"}, "stadium_id": {"type": "table_column", "column_name": "stadium_id", "data_type": "string"}, "year": {"type": "table_column", "column_name": "year", "data_type": "string"}, "stadium": {"type": "simple_join", "other_collection_name": "stadiums", "singular": true, "no_collisions": false, "keys": {"stadium_id": ["stadium_id"]}, "reverse_relationship_name": "concerts"}}}, "singers": {"type": "simple_table", "table_path": "main.singer", "unique_properties": ["singer_id"], "properties": {"singer_id": {"type": "table_column", "column_name": "singer_id", "data_type": "string"}, "name": {"type": "table_column", "column_name": "name", "data_type": "string"}, "country": {"type": "table_column", "column_name": "country", "data_type": "string"}, "song_name": {"type": "table_column", "column_name": "song_name", "data_type": "string"}, "song_release_year": {"type": "table_column", "column_name": "song_release_year", "data_type": "string"}, "age": {"type": "table_column", "column_name": "age", "data_type": "string"}, "is_male": {"type": "table_column", "column_name": "is_male", "data_type": "string"}}}, "singer_in_concerts": {"type": "simple_table", "table_path": "main.singer_in_concert", "unique_properties": [["concert_id", "singer_id"]], "properties": {"concert_id": {"type": "table_column", "column_name": "concert_id", "data_type": "string"}, "singer_id": {"type": "table_column", "column_name": "singer_id", "data_type": "string"}, "singer": {"type": "simple_join", "other_collection_name": "singers", "singular": true, "no_collisions": false, "keys": {"singer_id": ["singer_id"]}, "reverse_relationship_name": "singer_in_concerts"}, "concert": {"type": "simple_join", "other_collection_name": "concerts", "singular": true, "no_collisions": false, "keys": {"concert_id": ["concert_id"]}, "reverse_relationship_name": "singer_in_concerts"}}}, "stadiums": {"type": "simple_table", "table_path": "main.stadium", "unique_properties": ["stadium_id"], "properties": {"stadium_id": {"type": "table_column", "column_name": "stadium_id", "data_type": "string"}, "location": {"type": "table_column", "column_name": "location", "data_type": "string"}, "name": {"type": "table_column", "column_name": "name", "data_type": "string"}, "capacity": {"type": "table_column", "column_name": "capacity", "data_type": "string"}, "highest": {"type": "table_column", "column_name": "highest", "data_type": "string"}, "lowest": {"type": "table_column", "column_name": "lowest", "data_type": "string"}, "average": {"type": "table_column", "column_name": "average", "data_type": "string"}}}}}

## Answer
1. Analysis of the question:
The question asks for the total number of singers in the database. This can be achieved by counting the number of records in the `singers` collection.

2. Step-by-step explanation of the solution:
- Access the `singers` collection.
- Use the `COUNT` function to count the number of singers.
- Assign the result to a variable named `num_singers`.

3. The PyDough code in a Python code block:
```python
num_singers = concert_singer.singers.CALCULATE(number_of_singers=COUNT(singers)).SINGULAR().number_of_singers
```

4. Explanation of how the code works:
- `concert_singer.singers`: This accesses the `singers` collection.
- `.CALCULATE(number_of_singers=COUNT(singers))`: This calculates the count of all records in the `singers` collection and assigns it to a new field named `number_of_singers`.
- `.SINGULAR().number_of_singers`: This extracts the singular value of `number_of_singers` from the result.

## Pydough Code
```python
num_singers = concert_singer.singers.CALCULATE(number_of_singers=COUNT(singers)).SINGULAR().number_of_singers
```

## Code Context
# Explanation of PyDough Code for Counting Singers

I'll analyze the following PyDough code that answers the question "How many singers do we have?":

```python
num_singers = concert_singer.singers.CALCULATE(number_of_singers=COUNT(singers)).SINGULAR().number_of_singers
```

## 1. PyDough-Specific Functions and Patterns Used

### CALCULATE
The `CALCULATE` function [fcc80aa] is used to derive new properties via calculated expressions. In this code, it's creating a new property called `number_of_singers` by counting the singers.

```python
# From example in documentation
People.CALCULATE(
  name=JOIN_STRINGS("", first_name, last_name),
  n_packages_ordered=COUNT(packages),
)
```

### COUNT
`COUNT` is an aggregation function [b78dc8c] that:
- When called on a subcollection, returns how many records of it exist for each record of the current collection
- When called on an expression, counts how many non-null values exist in a plural expression

### SINGULAR
The `SINGULAR()` modifier [edc4690] is used to tell PyDough that the data should be treated as singular. This is necessary when accessing a sub-collection in a collection context that would normally be plural, but we know will return a single record.

## 2. Data Flow and Transformations

The code follows this flow:
1. Starts with `concert_singer.singers` - accessing the `singers` subcollection of the `concert_singer` collection
2. Applies `CALCULATE(number_of_singers=COUNT(singers))` - creates a new property that counts the number of singers
3. Uses `SINGULAR()` - indicates that the result should be treated as a singular record
4. Accesses `.number_of_singers` - extracts just the count value from the result
5. Assigns the final count to the variable `num_singers`

## 3. PyDough Best Practices Demonstrated

The code demonstrates several best practices:
- Using `CALCULATE` to create a meaningful named property (`number_of_singers`) [fcc80aa]
- Using `SINGULAR()` appropriately to handle what would otherwise be a plural result [edc4690]
- Using aggregation functions like `COUNT` to perform calculations on collections [b78dc8c]
- Following the pattern of chaining operations to transform data step by step

## 4. How This Code Follows PyDough Conventions

The code follows PyDough conventions by:
- Using dot notation to navigate from collections to subcollections (`concert_singer.singers`)
- Using uppercase for PyDough operations (`CALCULATE`, `COUNT`, `SINGULAR`)
- Using keyword arguments in `CALCULATE` to name the output expression (`number_of_singers=COUNT(singers)`)
- Chaining operations in a logical sequence

## 5. How the Code Addresses the Original Question

The original question was "How many singers do we have?" The code directly answers this by:
1. Accessing the collection of singers via `concert_singer.singers`
2. Counting them with `COUNT(singers)`
3. Extracting the single count value with `.SINGULAR().number_of_singers`
4. Storing the result in the variable `num_singers`

## 6. Key Examples from Documentation

From the documentation [edc4690], a similar pattern using `SINGULAR()`:

```python
# Good Example #2: Access the email of the current occupant of each address
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

From the documentation [fcc80aa] on `CALCULATE`:

```python
# Good Example #3: For every person, find their full name and count how many packages they purchased
People.CALCULATE(
    name=JOIN_STRINGS("", first_name, last_name),
    n_packages_ordered=COUNT(packages),
)
```

## 7. Key Code Blocks and Definitions

### SINGULAR Definition [edc4690]:
"In PyDough, it is required that if we are accessing a sub-collection in a collection context, the collection must be singular with regards to the sub-collection. Certain PyDough operations, such as specific filters, can cause plural data to become singular. In this case, PyDough will still ban the plural data from being treated as singular unless the `.SINGULAR()` modifier is used to tell PyDough that the data should be treated as singular."

### CALCULATE Definition [fcc80aa]:
"The examples so far just show selecting all properties from records of a collection. Most of the time, an analytical question will only want a subset of the properties, and may want to derive new properties via calculated expressions. The way to do this is with a `CALCULATE` term. This method contains the expressions that should be derived by the `CALCULATE` operation."

### COUNT Definition [b78dc8c]:
"Collection Aggregations: `COUNT`: if called on a subcollection, returns how many records of it exist for each record of the current collection (if called on an expression instead of collection, see simple aggregations)."

---

## Question
What is the total number of singers?
Database Schema:
{"concert_singer": {"concerts": {"type": "simple_table", "table_path": "main.concert", "unique_properties": ["concert_id"], "properties": {"concert_id": {"type": "table_column", "column_name": "concert_id", "data_type": "string"}, "concert_name": {"type": "table_column", "column_name": "concert_name", "data_type": "string"}, "theme": {"type": "table_column", "column_name": "theme", "data_type": "string"}, "stadium_id": {"type": "table_column", "column_name": "stadium_id", "data_type": "string"}, "year": {"type": "table_column", "column_name": "year", "data_type": "string"}, "stadium": {"type": "simple_join", "other_collection_name": "stadiums", "singular": true, "no_collisions": false, "keys": {"stadium_id": ["stadium_id"]}, "reverse_relationship_name": "concerts"}}}, "singers": {"type": "simple_table", "table_path": "main.singer", "unique_properties": ["singer_id"], "properties": {"singer_id": {"type": "table_column", "column_name": "singer_id", "data_type": "string"}, "name": {"type": "table_column", "column_name": "name", "data_type": "string"}, "country": {"type": "table_column", "column_name": "country", "data_type": "string"}, "song_name": {"type": "table_column", "column_name": "song_name", "data_type": "string"}, "song_release_year": {"type": "table_column", "column_name": "song_release_year", "data_type": "string"}, "age": {"type": "table_column", "column_name": "age", "data_type": "string"}, "is_male": {"type": "table_column", "column_name": "is_male", "data_type": "string"}}}, "singer_in_concerts": {"type": "simple_table", "table_path": "main.singer_in_concert", "unique_properties": [["concert_id", "singer_id"]], "properties": {"concert_id": {"type": "table_column", "column_name": "concert_id", "data_type": "string"}, "singer_id": {"type": "table_column", "column_name": "singer_id", "data_type": "string"}, "singer": {"type": "simple_join", "other_collection_name": "singers", "singular": true, "no_collisions": false, "keys": {"singer_id": ["singer_id"]}, "reverse_relationship_name": "singer_in_concerts"}, "concert": {"type": "simple_join", "other_collection_name": "concerts", "singular": true, "no_collisions": false, "keys": {"concert_id": ["concert_id"]}, "reverse_relationship_name": "singer_in_concerts"}}}, "stadiums": {"type": "simple_table", "table_path": "main.stadium", "unique_properties": ["stadium_id"], "properties": {"stadium_id": {"type": "table_column", "column_name": "stadium_id", "data_type": "string"}, "location": {"type": "table_column", "column_name": "location", "data_type": "string"}, "name": {"type": "table_column", "column_name": "name", "data_type": "string"}, "capacity": {"type": "table_column", "column_name": "capacity", "data_type": "string"}, "highest": {"type": "table_column", "column_name": "highest", "data_type": "string"}, "lowest": {"type": "table_column", "column_name": "lowest", "data_type": "string"}, "average": {"type": "table_column", "column_name": "average", "data_type": "string"}}}}}

## Answer
1. **Analysis of the question:**
The question asks for the total number of singers in the database. This requires counting all records in the `singers` collection.

2. **Step-by-step explanation of the solution:**
   - Access the `singers` collection.
   - Use the `COUNT` function to count the number of records in the `singers` collection.
   - Assign the result to a variable named `total_singers`.

3. **The PyDough code:**

```python
total_singers = concert_singer.singers.CALCULATE(num_singers=COUNT(concert_singer.singers)).SINGULAR().num_singers
```

4. **Explanation of how the code works:**
   - `concert_singer.singers`: Accesses the `singers` collection.
   - `.CALCULATE(num_singers=COUNT(concert_singer.singers))`: Calculates the count of all records in the `singers` collection and assigns it to the field `num_singers`.
   - `.SINGULAR().num_singers`: Accesses the calculated value `num_singers` from the single record created by the `CALCULATE` function.
   - `total_singers = ...`: Assigns the final count to the variable `total_singers`.

## Pydough Code
```python
total_singers = concert_singer.singers.CALCULATE(num_singers=COUNT(concert_singer.singers)).SINGULAR().num_singers
```

## Code Context
# Explanation of PyDough Code for Counting Total Singers

Let me explain the PyDough code that answers the question "What is the total number of singers?":

```python
total_singers = concert_singer.singers.CALCULATE(num_singers=COUNT(concert_singer.singers)).SINGULAR().num_singers
```

## PyDough Functions and Patterns Used

### COUNT Function
The code uses the `COUNT` aggregation function [0a7d61d], which returns the number of non-null records in a collection. In this case, it's counting all records in the `concert_singer.singers` collection.

### CALCULATE Operation
The `CALCULATE` operation [b320089] is used to define new terms or expressions based on the current collection context. Here, it's creating a new term called `num_singers` that contains the count of all singers.

### SINGULAR Operation
The `.SINGULAR()` modifier [edc4690] is used to tell PyDough that the collection should be treated as singular (containing only one record). This is necessary because the code needs to access a scalar property (`num_singers`) from what would otherwise be treated as a plural collection.

## Data Flow and Transformations

The data flow in this code follows these steps:

1. Start with the `concert_singer.singers` collection
2. Apply `CALCULATE` to create a new term `num_singers` that counts all records in the collection
3. Apply `SINGULAR()` to indicate that the result should be treated as a single record
4. Access the `num_singers` property from this singular result
5. Assign the final scalar value to the variable `total_singers`

## PyDough Best Practices Demonstrated

The code demonstrates several PyDough best practices:

1. **Using aggregation functions for counting**: The code uses the `COUNT` function to count records, which is the proper way to perform aggregation in PyDough [0a7d61d].

2. **Using SINGULAR() appropriately**: The code uses `.SINGULAR()` to access a scalar property from what would otherwise be a plural collection [edc4690]. This is necessary when you need to extract a single value from a collection.

3. **Hierarchical thinking**: The code follows PyDough's approach of expressing analytical questions with hierarchical thinking [988171e], which is closer to human linguistics than a relational model.

## How This Code Follows PyDough Conventions

The code follows PyDough conventions by:

1. Using the proper collection access pattern (`concert_singer.singers`)
2. Using the standard aggregation function (`COUNT`) for counting records
3. Using `CALCULATE` to define new terms
4. Using `SINGULAR()` to properly handle the transition from a collection to a scalar value

## How the Code Addresses the Original Question

The original question asks for the total number of singers. The PyDough code directly answers this by:

1. Accessing the `singers` collection within the `concert_singer` context
2. Counting all records in this collection using `COUNT(concert_singer.singers)`
3. Extracting this count as a scalar value using `.SINGULAR().num_singers`
4. Storing the result in the variable `total_singers`

The final result is a single number representing the total count of all singers in the database.

## Comparable Examples from the Search Results

A similar pattern can be seen in this example from the search results [eb3ac75]:

```python
nation_4 = nations.WHERE(key == 4).SINGULAR()
pydough.to_df(regions.CALCULATE(name, nation_4_name=nation_4.name))
```

This example also uses `.SINGULAR()` to access a scalar property (`name`) from what would otherwise be a plural collection.

Another relevant example [b320089]:

```python
People.CALCULATE(
  n_packages=COUNT(packages),
  home_has_had_packages_billed=HAS(current_address.billed_packages),
  avg_package_cost=AVG(packages.package_cost)
)
```

This shows how `COUNT` is used to count records in a collection, similar to how it's used in our code to count singers.

---

## Question
Show name, country, age for all singers ordered by age from the oldest to the youngest.
Database Schema:
{"concert_singer": {"concerts": {"type": "simple_table", "table_path": "main.concert", "unique_properties": ["concert_id"], "properties": {"concert_id": {"type": "table_column", "column_name": "concert_id", "data_type": "string"}, "concert_name": {"type": "table_column", "column_name": "concert_name", "data_type": "string"}, "theme": {"type": "table_column", "column_name": "theme", "data_type": "string"}, "stadium_id": {"type": "table_column", "column_name": "stadium_id", "data_type": "string"}, "year": {"type": "table_column", "column_name": "year", "data_type": "string"}, "stadium": {"type": "simple_join", "other_collection_name": "stadiums", "singular": true, "no_collisions": false, "keys": {"stadium_id": ["stadium_id"]}, "reverse_relationship_name": "concerts"}}}, "singers": {"type": "simple_table", "table_path": "main.singer", "unique_properties": ["singer_id"], "properties": {"singer_id": {"type": "table_column", "column_name": "singer_id", "data_type": "string"}, "name": {"type": "table_column", "column_name": "name", "data_type": "string"}, "country": {"type": "table_column", "column_name": "country", "data_type": "string"}, "song_name": {"type": "table_column", "column_name": "song_name", "data_type": "string"}, "song_release_year": {"type": "table_column", "column_name": "song_release_year", "data_type": "string"}, "age": {"type": "table_column", "column_name": "age", "data_type": "string"}, "is_male": {"type": "table_column", "column_name": "is_male", "data_type": "string"}}}, "singer_in_concerts": {"type": "simple_table", "table_path": "main.singer_in_concert", "unique_properties": [["concert_id", "singer_id"]], "properties": {"concert_id": {"type": "table_column", "column_name": "concert_id", "data_type": "string"}, "singer_id": {"type": "table_column", "column_name": "singer_id", "data_type": "string"}, "singer": {"type": "simple_join", "other_collection_name": "singers", "singular": true, "no_collisions": false, "keys": {"singer_id": ["singer_id"]}, "reverse_relationship_name": "singer_in_concerts"}, "concert": {"type": "simple_join", "other_collection_name": "concerts", "singular": true, "no_collisions": false, "keys": {"concert_id": ["concert_id"]}, "reverse_relationship_name": "singer_in_concerts"}}}, "stadiums": {"type": "simple_table", "table_path": "main.stadium", "unique_properties": ["stadium_id"], "properties": {"stadium_id": {"type": "table_column", "column_name": "stadium_id", "data_type": "string"}, "location": {"type": "table_column", "column_name": "location", "data_type": "string"}, "name": {"type": "table_column", "column_name": "name", "data_type": "string"}, "capacity": {"type": "table_column", "column_name": "capacity", "data_type": "string"}, "highest": {"type": "table_column", "column_name": "highest", "data_type": "string"}, "lowest": {"type": "table_column", "column_name": "lowest", "data_type": "string"}, "average": {"type": "table_column", "column_name": "average", "data_type": "string"}}}}}

## Answer
1. **Analysis of the question**
The question asks to retrieve the name, country, and age of all singers, sorted by age in descending order (oldest to youngest). This requires accessing the `singers` collection, selecting the specified fields, and ordering the results by the `age` field.

2. **Step-by-step explanation of the solution**
- Start with the `singers` collection.
- Use `CALCULATE` to select the `name`, `country`, and `age` fields, aliasing them to `singer_name`, `singer_country`, and `singer_age` respectively.
- Use `ORDER_BY` to sort the results by `age` in descending order (`age.DESC()`).

3. **The PyDough code in a Python code block**
```python
singers_ordered = singers.CALCULATE(singer_name=name, singer_country=country, singer_age=age).ORDER_BY(age.DESC())
```

4. **Explanation of how the code works**
- `singers.CALCULATE(singer_name=name, singer_country=country, singer_age=age)`: This part selects the `name`, `country`, and `age` fields from the `singers` collection and renames them to `singer_name`, `singer_country`, and `singer_age` respectively.
- `.ORDER_BY(age.DESC())`: This part sorts the resulting collection by the `age` field in descending order, ensuring that the oldest singers appear first.

## Pydough Code
```python
singers_ordered = singers.CALCULATE(singer_name=name, singer_country=country, singer_age=age).ORDER_BY(age.DESC())
```

## Code Context
# Explanation of the Pydough Code

The provided Pydough code answers a question about displaying singer information ordered by age from oldest to youngest. Let me break down this code and explain how it works based on the documentation provided.

## Code Analysis

```python
singers_ordered = singers.CALCULATE(singer_name=name, singer_country=country, singer_age=age).ORDER_BY(age.DESC())
```

## 1. Pydough-specific Functions and Patterns Used

### CALCULATE
The code uses the `CALCULATE` operation [988171e], which is a core Pydough operation that allows you to derive new terms from a collection. In this case, it's creating three new terms (`singer_name`, `singer_country`, and `singer_age`) based on existing properties of the `singers` collection (`name`, `country`, and `age`).

### ORDER_BY
After calculating these terms, the code applies the `ORDER_BY` operation [9c4448e], which sorts the collection based on specified criteria. Here, it's sorting by the `age` property in descending order using the `.DESC()` modifier.

## 2. Data Flow and Transformations

The data flow in this code follows a clear pattern:

1. Start with the `singers` collection (the base data)
2. Apply `CALCULATE` to create new terms with more descriptive names
3. Apply `ORDER_BY` to sort the results by age in descending order
4. Store the final result in the variable `singers_ordered`

This transformation pipeline is a common pattern in Pydough, where operations are chained together to progressively transform data [988171e].

## 3. Important Pydough Best Practices Demonstrated

The code demonstrates several Pydough best practices:

- **Descriptive naming**: Renaming fields to more descriptive names (`name` → `singer_name`, etc.) improves readability [9c4448e]
- **Chaining operations**: Operations are chained together in a logical sequence [988171e]
- **Explicit sorting direction**: The code explicitly specifies the sorting direction with `.DESC()` rather than relying on defaults [9c4448e]

## 4. How This Code Follows Pydough Conventions

The code follows Pydough conventions by:

- Using the dot notation to chain operations [988171e]
- Using `CALCULATE` to derive new terms [988171e]
- Using `ORDER_BY` with a collation expression (age.DESC()) to specify sorting [9c4448e]
- Storing the result in a variable that can be used for further operations or output [988171e]

## 5. How the Code Addresses the Original Question

The original question asks to "Show name, country, age for all singers ordered by age from the oldest to the youngest." The code addresses this by:

1. Selecting the required fields (name, country, age) using `CALCULATE`
2. Renaming them with more descriptive prefixes for clarity
3. Ordering the results by age in descending order (oldest to youngest) using `ORDER_BY(age.DESC())`

## 6. Key Examples from Documentation

From the documentation [9c4448e], we can see similar examples of `ORDER_BY` usage:

```python
# Good Example #1: Order every person alphabetically by last name, then first name, then middle name
People.ORDER_BY(last_name.ASC(), first_name.ASC(), middle_name.ASC(na_pos="last"))

# Good Example #2: For every person list their SSN & how many packages they have ordered, and order them from highest number of orders to lowest
People.CALCULATE(
    ssn, n_packages=COUNT(packages).DESC()
).ORDER_BY(
    n_packages.DESC(), birth_date.ASC()
)
```

## 7. Key Descriptions and Definitions

### ORDER_BY [9c4448e]
"Another operation that can be done onto PyDough collections is sorting them. This is done by appending a collection with `.ORDER_BY(...)` which will order the collection by the collation terms between the parenthesis."

The `.DESC()` modifier indicates that the expression should be used to sort in descending order. The default for `.DESC()` is to place null values last.

### CALCULATE [988171e]
PyDough allows expressing analytical questions with hierarchical thinking. The `CALCULATE` operation derives new terms from existing data.

As shown in the example: "for every person their name & the total income they've made from all jobs minus the total tuition paid to all schools."

```python
result = People.CALCULATE(
    name,
    net_income = SUM(jobs.income_earned) - SUM(schools.tuition_paid)
)
```

In conclusion, the provided Pydough code efficiently answers the original question by selecting the required singer information and ordering it by age from oldest to youngest using Pydough's expressive data transformation capabilities.

---

