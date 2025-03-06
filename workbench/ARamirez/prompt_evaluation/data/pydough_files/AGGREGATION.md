**VERY IMPORTANT NOTES**

- Aggregations Function does not support calling aggregations inside of aggregations

- Functions must have one parameter (no optional).

**AGGREGATION FUNCTIONS**  

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
