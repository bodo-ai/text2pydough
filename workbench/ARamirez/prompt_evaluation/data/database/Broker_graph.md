### The high-level graph `Broker` collection contains the following collections:
- **Customers**: Contains information about brokerage customers.
- **Tickers**: Contains information about stock tickers.
- **DailyPrices**: Contains daily price information for tickers.
- **Transactions**: Contains records of brokerage transactions.

### The `Customers` collection contains the following columns:
- **_id**: A unique identifier for the customer (from `sbCustId`).
- **name**: The name of the customer (from `sbCustName`).
- **email**: The email address of the customer (from `sbCustEmail`).
- **phone**: The phone number of the customer (from `sbCustPhone`).
- **address1**: The first line of the customer's address (from `sbCustAddress1`).
- **address2**: The second line of the customer's address (from `sbCustAddress2`).
- **city**: The city of the customer's address (from `sbCustCity`).
- **state**: The state of the customer's address (from `sbCustState`).
- **country**: The country of the customer's address (from `sbCustCountry`).
- **postal_code**: The postal code of the customer's address (from `sbCustPostalCode`).
- **join_date**: The date the customer joined (from `sbCustJoinDate`).
- **status**: The status of the customer account (from `sbCustStatus`).
- **transactions_made**: A list of all transactions made by the customer (reverse of `Transactions.customer`).

### The `Tickers` collection contains the following columns:
- **_id**: A unique identifier for the ticker (from `sbTickerId`).
- **symbol**: The stock symbol for the ticker (from `sbTickerSymbol`).
- **name**: The name of the company or asset associated with the ticker (from `sbTickerName`).
- **ticker_type**: The type of the ticker (e.g., 'stock', 'ETF') (from `sbTickerType`).
- **exchange**: The exchange where the ticker is traded (from `sbTickerExchange`).
- **currency**: The currency the ticker is traded in (from `sbTickerCurrency`).
- **db2x**: An additional identifier or property (from `sbTickerDb2x`).
- **is_active**: A flag indicating if the ticker is currently active (from `sbTickerIsActive`).
- **transactions_of**: A list of all transactions involving this ticker (reverse of `Transactions.ticker`).
- **historical_prices**: The corresponding daily prices for this ticker (reverse of `DailyPrices.ticker`).

### The `DailyPrices` collection contains the following columns:
- **ticker_id**: Foreign key referencing the `Tickers` collection (from `sbDpTickerId`).
- **date**: The date of the price record (from `sbDpDate`).
- **open**: The opening price for the day (from `sbDpOpen`).
- **high**: The highest price for the day (from `sbDpHigh`).
- **low**: The lowest price for the day (from `sbDpLow`).
- **close**: The closing price for the day (from `sbDpClose`).
- **volume**: The trading volume for the day (from `sbDpVolume`).
- **epoch_ms**: The date represented in epoch milliseconds (from `sbDpEpochMs`).
- **source**: The source of the price data (from `sbDpSource`).
- **ticker**: The corresponding ticker for this daily price record (reverse of `Tickers.historical_prices`).

### The `Transactions` collection contains the following columns:
- **transaction_id**: A unique identifier for the transaction (from `sbTxId`).
- **customer_id**: Foreign key referencing the `Customers` collection (from `sbTxCustId`).
- **ticker_id**: Foreign key referencing the `Tickers` collection (from `sbTxTickerId`).
- **date_time**: The timestamp of the transaction (from `sbTxDateTime`).
- **transaction_type**: The type of transaction (e.g., 'BUY', 'SELL') (from `sbTxType`).
- **shares**: The number of shares involved in the transaction (from `sbTxShares`).
- **price**: The price per share for the transaction (from `sbTxPrice`).
- **amount**: The total amount of the transaction (from `sbTxAmount`).
- **currency**: The currency of the transaction (from `sbTxCcy`).
- **tax**: The tax applied to the transaction (from `sbTxTax`).
- **commission**: The commission charged for the transaction (from `sbTxCommission`).
- **kpx**: An additional property or identifier related to the transaction (from `sbTxKpx`).
- **settlement_date_str**: The settlement date as a string (from `sbTxSettlementDateStr`).
- **status**: The status of the transaction (e.g., 'COMPLETED', 'PENDING') (from `sbTxStatus`).
- **customer**: The corresponding customer for this transaction (reverse of `Customers.transactions_made`).
- **ticker**: The corresponding ticker for this transaction (reverse of `Tickers.transactions_of`).
