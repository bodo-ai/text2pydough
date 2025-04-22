### The `regions` collection contains the following columns:
- **key**: A unique identifier for the region.
- **name**: The name of the region.
- **comment**: Additional notes or descriptions about the region.
- **nations**: A list of all nations associated with this record (reverse of `nations.region`).

### The `nations` collection contains the following columns:
- **key**: A unique identifier for the nation.
- **name**: The name of the nation.
- **region_key**: A foreign key referencing the `regions` collection.
- **comment**: Additional notes or descriptions about the nation.
- **suppliers**: A list of all suppliers associated with this record (reverse of `suppliers.nation`).
- **customers**: A list of all customers associated with this record (reverse of `customers.nation`).
- **region**: The corresponding regions for this record (reverse of `regions.nations`).

### The `parts` collection contains the following columns:
- **key**: A unique identifier for the part.
- **name**: The name of the part.
- **manufacturer**: The manufacturer of the part.
- **brand**: The brand of the part.
- **part_type**: The type or category of the part.
- **size**: The size of the part.
- **container**: The type of container used for packaging the part.
- **retail_price**: The retail price of the part.
- **comment**: Additional notes or descriptions about the part.
- **supply_records**: A list of all supply_records associated with this record (reverse of `supply_records.part`).
- **lines**: A list of all lines associated with this record (reverse of `lines.part`).

### The `suppliers` collection contains the following columns:
- **key**: A unique identifier for the supplier.
- **name**: The name of the supplier.
- **address**: The address of the supplier.
- **nation_key**: A foreign key referencing the `nations` collection.
- **phone**: The supplier's phone number.
- **account_balance**: The account balance of the supplier.
- **comment**: Additional notes or descriptions about the supplier.
- **supply_records**: A list of all supply_records associated with this record (reverse of `supply_records.supplier`).
- **lines**: A list of all lines associated with this record (reverse of `lines.supplier`).
- **nation**: The corresponding nations for this record (reverse of `nations.suppliers`).

### The `lines` collection contains the following columns:
- **order_key**: A foreign key referencing the `orders` collection.
- **part_key**: A foreign key referencing the `parts` collection.
- **supplier_key**: A foreign key referencing the `suppliers` collection.
- **line_number**: The line number within the order.
- **quantity**: The quantity ordered.
- **extended_price**: The extended price of the line item.
- **discount**: The discount applied to the line item.
- **tax**: The tax applied to the line item.
- **status**: The status of the line item.
- **ship_date**: The shipping date of the line item.
- **commit_date**: The committed delivery date for the line item.
- **receipt_date**: The date the line item was received.
- **ship_instruct**: Shipping instructions for the line item.
- **ship_mode**: The shipping mode for the line item.
- **return_flag**: A flag indicating whether the item was returned.
- **comment**: Additional comments or notes about the line item.
- **part_and_supplier**: The corresponding supply_records for this record (reverse of `supply_records.lines`).
- **order**: The corresponding orders for this record (reverse of `orders.lines`).
- **part**: The corresponding parts for this record (reverse of `parts.lines`).
- **supplier**: The corresponding suppliers for this record (reverse of `suppliers.lines`).

### The `supply_records` collection contains the following columns:
- **part_key**: A foreign key referencing the `parts` collection.
- **supplier_key**: A foreign key referencing the `suppliers` collection.
- **availqty**: The available quantity of the part supplied.
- **supplycost**: The cost of supplying this part.
- **comment**: Additional notes or descriptions about the supply record.
- **part**: The corresponding parts for this record (reverse of `parts.supply_records`).
- **supplier**: The corresponding suppliers for this record (reverse of `suppliers.supply_records`).
- **lines**: A list of all lines associated with this record (reverse of `lines.part_and_supplier`).

### The `orders` collection contains the following columns:
- **key**: A unique identifier for the order.
- **customer_key**: A foreign key referencing the `customers` collection.
- **order_status**: The current status of the order (e.g., 'PENDING', 'SHIPPED').
- **total_price**: The total price of the order.
- **order_date**: The date when the order was placed.
- **order_priority**: The priority level of the order (e.g., 'HIGH', 'LOW').
- **clerk**: The name of the clerk handling the order.
- **ship_priority**: The priority level for shipping.
- **comment**: Additional comments or notes about the order.
- **customer**: The corresponding customers for this record (reverse of `customers.orders`).
- **lines**: A list of all lines associated with this record (reverse of `lines.order`).

### The `customers` collection contains the following columns:
- **key**: A unique identifier for the customer.
- **name**: The name of the customer.
- **address**: The address of the customer.
- **nation_key**: A foreign key referencing the `nations` collection.
- **phone**: The customer's phone number.
- **acctbal**: The account balance of the customer.
- **mktsegment**: The market segment the customer belongs to.
- **comment**: Additional comments or notes about the customer.
- **nation**: The corresponding nations for this record (reverse of `nations.customers`).
- **orders**: A list of all orders associated with this record (reverse of `orders.customer`).
