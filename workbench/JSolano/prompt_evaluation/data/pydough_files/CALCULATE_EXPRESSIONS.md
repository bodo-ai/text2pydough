**VERY IMPORTANT NOTES**

  - Use aggregation functions (e.g., SUM, COUNT) for plural sub-collections.

  - Positional arguments must precede keyword arguments.

  - Terms defined in a CALCULATE do not take effect until after the CALCULATE completes.

  - Existing terms not included in a CALCULATE can still be referenced but are not part of the final result unless included in the last CALCULATE clause.

  - A CALCULATE on the graph itself creates a collection with one row and columns corresponding to the properties inside the CALCULATE.

  - PyDough does not support use different childs in operations, for example you cannot do: `total = SUM(orders.lines.extended_price * (1 - orders.lines.discount))` because you have two different calls. Instead use CALCULATE with a variable, for example: `total = SUM(orders.lines.CALCULATE(total = extended_price * (1 - discount)).total)`.

  - CALCULATE 

**CALCULATE EXPRESSIONS**  

- **Purpose**: Derive new fields, rename existing ones or select specific fields. 

- **Key Features**:
    - Positional Arguments: Use existing property names or get auto-generated names.

    - Keyword Arguments: Explicitly name output fields (e.g., full_name=...).

    - Scope: All original collection properties remain accessible but aren't included in the final output unless explicitly added.

    - Overrides: Duplicate names in CALCULATE override existing properties.

    - Order Matters: Terms in the same CALCULATE cannot reference each other. Use multiple CALCULATE steps for dependencies.

    - Graph-Level Aggregation: Use GRAPH.CALCULATE() to compute global metrics (e.g., total counts). 


- **Syntax**:  
  Collection.CALCULATE(field=expression, ...)  

- **Valid Expressions**
  - Expressions must be singular in the current context. Valid types include:

  - Scalar properties (e.g., first_name).

  - Literals (e.g., ""alphabet soup"").

  - Singular sub-collections (e.g., customer.first_name).

  - Non-aggregate functions on singular values (e.g., YEAR(...)).

  - Aggregate functions on plural sub-collections (e.g., COUNT(packages)).

- **Examples**:  

  - **Select fields**:  
    People.CALCULATE(first_name=first_name, last_name=last_name)  

  - **Derived fields**:  
    Packages.CALCULATE(  
        customer_name=JOIN_STRINGS(' ', customer.first_name, customer.last_name),  
        cost_per_unit=package_cost / quantity  
    )  