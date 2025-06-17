# TPCH Database Structure

This document describes the structure of the TPCH (Transactional Processing Benchmark) database schema. The schema consists of several tables, each with specific properties, relationships, and attributes. Below is a breakdown of each table in the schema, along with their unique properties, columns, and relationships.

# TPCH

The high-level graph  `TPCH` collection contains the all database:

**WARNING**:
TPCH should be used only for operations like computing averages, totals, frequencies, sum, etc. Do not use it for any other purposes. Also, avoid starting with TPCH unless you need to perform an operation.

### Table: `TPCH`

- **Properties**:
   - `customers`: A list of all customer.
   - `lines`: A list of all lines items.
   - `nations`: A list of all nations.
   - `orders`: A list of all orders placed.
   - `parts`: A list of all parts available.
   - `regions`: A list of all regions.
   - `suppliers`: A list of all suppliers
   - `supply_records`: A list of all supply records for suppliers and parts.


## Regions
The `regions` table contains information about different regions.

### Table: `regions`
- **Unique Properties**: `key`
- **Properties**:
  - `key`: The unique identifier for each region.
  - `name`: The name of the region.
  - `comment`: Additional comments about the region.

### Relationships:
- **nations**: A region can have many nations. (reverse of `nations.region`).

---

## Nations
The `nations` table contains information about different nations, including the region they belong to.

### Table: `nations`
- **Unique Properties**: `key`
- **Properties**:
  - `key`: The unique identifier for each nation.
  - `name`: The name of the nation.
  - `region_key`: The key that links to the `regions` table.
  - `comment`: Additional comments about the nation.

### Relationships:
- **customers**: A list of customers associated with this nation (reverse of `customers.nation`).
- **region**: The corresponding region this nation belongs to (reverse of `regions.nations`).
- **suppliers**: A list of suppliers associated with this nation (reverse of `suppliers.nation`).
---

## Parts
The `parts` table stores information about various parts.

### Table: `parts`
- **Unique Properties**: `key`
- **Properties**:
  - `key`: The unique identifier for each part.
  - `name`: The name of the part.
  - `manufacturer`: The manufacturer of the part.
  - `brand`: The brand of the part.
  - `part_type`: The type of the part.
  - `size`: The size of the part.
  - `container`: The container in which the part is stored.
  - `retail_price`: The retail price of the part.
  - `comment`: Additional comments about the part.

### Relationships:
- **Supply Records**: A part can have multiple supply records, which link to the `suppliers` table.  (reverse of `supply_records.part`)
- **Lines**: A part can appear in many line items, which link to the `lines` table. (reverse of `lines.part`).

---

## Suppliers
The `suppliers` table stores information about suppliers.

### Table: `suppliers`
- **Unique Properties**: `key`
- **Properties**:
  - `key`: The unique identifier for each supplier.
  - `name`: The name of the supplier.
  - `address`: The address of the supplier.
  - `nation_key`: The key linking the supplier to the `nations` table.
  - `phone`: The phone number of the supplier.
  - `account_balance`: The account balance of the supplier.
  - `comment`: Additional comments about the supplier.

### Relationships:
- **lines**: A supplier can have multiple supply records. (reverse of `lines.supplier`).
- **nation**: The corresponding nation of the supplier (reverse of `nations.suppliers`).
- **supply_records**: A list of all supply records for this supplier (reverse of `supply_records.supplier`).

---

## Line Items
The `lines` table stores information about each item in an order.

### Table: `lines`
- **Unique Properties**: `["order_key", "line_number"]`, `["part_key", "supplier_key", "order_key"]`
- **Properties**:
  - `order_key`: The key of the associated order.
  - `part_key`: The key of the part.
  - `supplier_key`: The key of the supplier.
  - `line_number`: The line number of the item in the order.
  - `quantity`: The quantity of the part ordered.
  - `extended_price`: The extended price for the line item.
  - `discount`: The discount applied to the item.
  - `tax`: The tax applied to the item.
  - `status`: The status of the line item.
  - `ship_date`: The ship date of the line item.
  - `commit_date`: The commit date of the line item.
  - `receipt_date`: The receipt date of the line item.
  - `ship_instruct`: Shipping instructions for the line item.
  - `ship_mode`: The mode of shipping for the line item.
  - `return_flag`: Return flag for the line item.
  - `comment`: Additional comments about the line item.

### Relationships:
- **order**: The corresponding order for this line item (reverse of `orders.lines`).
- **part**: The corresponding part for this line item (reverse of `parts.lines`).
- **part_and_supplier**: The corresponding supply record (reverse of `supply_records.lines`).
- **supplier**: The corresponding supplier for this line item (reverse of `suppliers.lines`).
---

## Supply Records
The `supply_records` table tracks the supply of parts from suppliers.

### Table: `supply_records`
- **Unique Properties**: `["part_key", "supplier_key"]`
- **Properties**:
  - `part_key`: The key of the part.
  - `supplier_key`: The key of the supplier.
  - `availqty`: The available quantity of the part.
  - `supplycost`: The cost of the part from the supplier.
  - `comment`: Additional comments about the supply record.


### Relationships:
- **part**: The corresponding part for this supply record (reverse of `parts.supply_records`).
- **supplier**: The corresponding supplier for this supply record (reverse of `suppliers.supply_records`).
---

## Orders
The `orders` table contains information about customer orders.

### Table: `orders`
- **Unique Properties**: `key`
- **Properties**:
  - `key`: The unique identifier for each order.
  - `customer_key`: The key linking to the `customers` table.
  - `order_status`: The status of the order.
  - `total_price`: The total price of the order.
  - `order_date`: The date the order was placed.
  - `order_priority`: The priority of the order.
  - `clerk`: The clerk handling the order.
  - `ship_priority`: The shipping priority of the order.
  - `comment`: Additional comments about the order.

### Relationships:
- **customer**: The corresponding customer who placed the order (reverse of `customers.orders`).
- **lines**: A list of all line items in this order (reverse of `lines.order`).

---

## Customers
The `customers` table contains information about customers.

### Table: `customers`
- **Unique Properties**: `key`
- **Properties**:
  - `key`: The unique identifier for each customer.
  - `name`: The name of the customer.
  - `address`: The address of the customer.
  - `nation_key`: The key linking to the `nations` table.
  - `phone`: The phone number of the customer.
  - `acctbal`: The account balance of the customer.
  - `mktsegment`: The market segment to which the customer belongs.
  - `comment`: Additional comments about the customer.

---
