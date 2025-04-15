### The high-level graph `Broker` collection contains the following tables:
- **Customers**: A list of all customers.
- **Tickers**: A list of all ticker symbols and related data.
- **DailyPrices**: A list of all daily price records.
- **Transactions**: A list of all financial transactions.

### The `Customers` collection contains the following columns:
- **_id**: A unique identifier for the customer.
- **name**: The name of the customer.
- **email**: The email address of the customer.
- **phone**: The phone number of the customer.
- **address1**: The primary address line of the customer.
- **address2**: The secondary address line of the customer.
- **city**: The city of the customer's residence.
- **state**: The state of the customer's residence.
- **country**: The country of the customer's residence.
- **postal_code**: The postal code of the customer's address.
- **join_date**: The date when the customer joined.
- **status**: The status of the customer.
- **transactions_made**: A list of all transactions made by the customer (reverse of `Transactions.customer`).

### The `Tickers` collection contains the following columns:
- **_id**: A unique identifier for the ticker.
- **symbol**: The stock ticker symbol.
- **name**: The name of the stock or asset.
- **ticker_type**: The type of ticker (e.g., stock, index, commodity).
- **exchange**: The stock exchange where the ticker is listed.
- **currency**: The currency in which the ticker is traded.
- **db2x**: A database reference value.
- **is_active**: Indicates if the ticker is active.
- **transactions_of**: A list of all transactions related to this ticker (reverse of `Transactions.ticker`).
- **historical_prices**: A list of all historical prices for this ticker (reverse of `DailyPrices.ticker`).

### The `DailyPrices` collection contains the following columns:
- **ticker_id**: A foreign key referencing the `Tickers` collection.
- **date**: The date of the price record.
- **open**: The opening price.
- **high**: The highest price of the day.
- **low**: The lowest price of the day.
- **close**: The closing price.
- **volume**: The number of shares traded.
- **epoch_ms**: The timestamp in milliseconds.
- **source**: The data source for the price record.
- **ticker**: The corresponding ticker (reverse of `Tickers.historical_prices`).

### The `Transactions` collection contains the following columns:
- **transaction_id**: A unique identifier for the transaction.
- **customer_id**: A foreign key referencing the `Customers` collection.
- **ticker_id**: A foreign key referencing the `Tickers` collection.
- **date_time**: The timestamp of the transaction.
- **transaction_type**: The type of transaction (e.g., buy, sell).
- **shares**: The number of shares traded.
- **price**: The price per share.
- **amount**: The total amount of the transaction.
- **currency**: The currency in which the transaction was conducted.
- **tax**: The tax applied to the transaction.
- **commission**: The commission charged.
- **kpx**: A reference identifier.
- **settlement_date_str**: The settlement date as a string.
- **status**: The status of the transaction.

### Getting the total count of transactions:
To get the total transactions:
```python
total_transactions = Broker.CALCULATE(total_transactions= COUNT(Transactions))
```

### Retrieving Transactions for a Customer
To get all transactions made by a specific customer:
```python
customer_transactions = Customers.transactions_made.CALCULATE(transaction_id, date_time, transaction_type, shares, price, amount, currency, tax, commission, status)
```

### Retrieving Ticker Information for a Transaction
For each transaction, the corresponding ticker can be accessed as follows:
```python
ticker_for_transaction = Transactions.ticker.CALCULATE(symbol, name, exchange, currency)
```

### Retrieving Historical Prices for a Ticker
To get all historical daily prices for a specific ticker:
```python
ticker_prices = Tickers.historical_prices.CALCULATE(date, open, high, low, close, volume, source)
```

### Retrieving Transactions per Ticker
To join all the transactions for each ticker:
```python
ticker_transactions = Tickers.transactions_of.CALCULATE(transaction_id, date_time, transaction_type, shares, price, amount, currency, tax, commission, status)
```

### Retrieving the Customer for a Transaction
For each transaction, the corresponding customer can be accessed as follows:
```python
customer_for_transaction = Transactions.customer.CALCULATE(_id, name, email, phone, address1, city, state, country)
```

### Retrieving Customers for a Ticker
To get all customers who made transactions for a specific ticker:
```python
ticker_customers = Tickers.transactions_of.customer.CALCULATE(_id, name, email, phone, address1, city, state, country)
```

### Retrieving Transactions for a Specific Date Range
To filter transactions for a specific date range:
```python
transactions_in_date_range = Transactions.CALCULATE(transaction_id, customer_id, ticker_id, date_time, transaction_type, shares, price, amount, currency, status).WHERE=((date_time >= start_date) & (date_time <= end_date))
```
