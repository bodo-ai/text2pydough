### The high-level graph `Dealership` collection contains the following collections:
- **Cars**: Contains information about cars in the dealership.
- **Salespersons**: Contains information about the sales staff.
- **Customers**: Contains information about dealership customers.
- **PaymentsMade**: Contains records of payments made by the dealership.
- **PaymentsReceived**: Contains records of payments received by the dealership.
- **Sales**: Contains records of car sales.
- **InventorySnapshots**: Contains snapshots of the car inventory over time.

### The `Cars` collection contains the following columns:
- **_id**: A unique identifier for the car.
- **make**: The manufacturer of the car.
- **model**: The model of the car.
- **year**: The manufacturing year of the car.
- **color**: The color of the car.
- **vin_number**: The Vehicle Identification Number.
- **engine_type**: The type of engine in the car.
- **transmission**: The type of transmission in the car.
- **cost**: The cost of the car to the dealership.
- **crtd_ts**: The timestamp when the car record was created.
- **sale_records**: A list of all sales records for this car (reverse of `Sales.car`).
- **inventory_snapshots**: A list of all inventory snapshots for this car (reverse of `InventorySnapshots.car`).

### The `Salespersons` collection contains the following columns:
- **_id**: A unique identifier for the salesperson.
- **first_name**: The first name of the salesperson.
- **last_name**: The last name of the salesperson.
- **email**: The email address of the salesperson.
- **phone**: The phone number of the salesperson.
- **hire_date**: The date the salesperson was hired.
- **termination_date**: The date the salesperson's employment ended (if applicable).
- **crtd_ts**: The timestamp when the salesperson record was created.
- **sales_made**: A list of all sales made by this salesperson (reverse of `Sales.salesperson`).

### The `Customers` collection contains the following columns:
- **_id**: A unique identifier for the customer.
- **first_name**: The first name of the customer.
- **last_name**: The last name of the customer.
- **email**: The email address of the customer.
- **phone**: The phone number of the customer.
- **address**: The street address of the customer.
- **city**: The city of the customer's address.
- **state**: The state of the customer's address.
- **zip_code**: The ZIP code of the customer's address.
- **crtd_ts**: The timestamp when the customer record was created.
- **car_purchases**: A list of all cars purchased by this customer (via Sales) (reverse of `Sales.customer`).

### The `PaymentsMade` collection contains the following columns:
- **_id**: A unique identifier for the payment record.
- **vendor_name**: The name of the vendor who received the payment.
- **payment_date**: The date the payment was made.
- **payment_amount**: The amount of the payment.
- **payment_method**: The method used for payment (e.g., 'Credit Card', 'Bank Transfer').
- **invoice_number**: The invoice number related to the payment.
- **invoice_date**: The date of the related invoice.
- **due_date**: The due date of the related invoice.
- **crtd_ts**: The timestamp when the payment record was created.

### The `PaymentsReceived` collection contains the following columns:
- **_id**: A unique identifier for the payment received record.
- **sale_id**: Foreign key referencing the `Sales` collection.
- **payment_date**: The date the payment was received.
- **payment_amount**: The amount of the payment received.
- **payment_method**: The method by which payment was received.
- **crtd_ts**: The timestamp when the payment received record was created.
- **sale_record**: The corresponding sale record for this payment (reverse of `Sales.payment`).

### The `Sales` collection contains the following columns:
- **_id**: A unique identifier for the sale record.
- **car_id**: Foreign key referencing the `Cars` collection.
- **salesperson_id**: Foreign key referencing the `Salespersons` collection.
- **customer_id**: Foreign key referencing the `Customers` collection.
- **sale_price**: The price the car was sold for.
- **sale_date**: The date the sale occurred.
- **crtd_ts**: The timestamp when the sale record was created.
- **payment**: A list of all payments received for this sale (reverse of `PaymentsReceived.sale_record`).
- **car**: The corresponding car sold in this record (reverse of `Cars.sale_records`).
- **salesperson**: The corresponding salesperson who made the sale (reverse of `Salespersons.sales_made`).
- **customer**: The corresponding customer who bought the car (reverse of `Customers.car_purchases`).

### The `InventorySnapshots` collection contains the following columns:
- **_id**: A unique identifier for the inventory snapshot record.
- **snapshot_date**: The date the inventory snapshot was taken.
- **car_id**: Foreign key referencing the `Cars` collection.
- **is_in_inventory**: A flag indicating whether the car was in inventory on the snapshot date.
- **crtd_ts**: The timestamp when the snapshot record was created.
- **car**: The corresponding car for this inventory snapshot (reverse of `Cars.inventory_snapshots`).
