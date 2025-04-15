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

---

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

---

### The high-level graph `DermTreatment` collection contains the following collections:
- **Doctors**: Contains information about doctors.
- **Patients**: Contains information about patients.
- **Drugs**: Contains information about drugs used in treatments.
- **Diagnoses**: Contains information about medical diagnoses.
- **Treatments**: Contains records of treatments administered.
- **Outcomes**: Contains records of treatment outcomes.
- **ConcomitantMeds**: Contains records of concomitant medications taken during treatments.
- **AdverseEvents**: Contains records of adverse events reported during treatments.

### The `Doctors` collection contains the following columns:
- **doc_id**: A unique identifier for the doctor.
- **first_name**: The first name of the doctor.
- **last_name**: The last name of the doctor.
- **speciality**: The medical specialty of the doctor (from `specialty`).
- **year_reg**: The year the doctor was registered.
- **med_school_name**: The name of the medical school the doctor attended.
- **loc_city**: The city where the doctor practices.
- **loc_state**: The state where the doctor practices.
- **loc_zip**: The ZIP code where the doctor practices.
- **bd_cert_num**: The board certification number of the doctor.
- **prescribed_treatments**: The corresponding treatments prescribed by this doctor (reverse of `Treatments.doctor`).

### The `Patients` collection contains the following columns:
- **patient_id**: A unique identifier for the patient.
- **first_name**: The first name of the patient.
- **last_name**: The last name of the patient.
- **date_of_birth**: The patient's date of birth.
- **date_of_registration**: The date the patient registered.
- **gender**: The gender of the patient.
- **email**: The email address of the patient.
- **phone**: The phone number of the patient.
- **addr_city**: The city of the patient's address.
- **addr_state**: The state of the patient's address.
- **addr_zip**: The ZIP code of the patient's address.
- **ins_type**: The type of insurance the patient has.
- **ins_policy_num**: The patient's insurance policy number.
- **height_cm**: The patient's height in centimeters.
- **weight_kg**: The patient's weight in kilograms.
- **treatments_received**: A list of all treatments received by this patient (reverse of `Treatments.patient`).

### The `Drugs` collection contains the following columns:
- **drug_id**: A unique identifier for the drug.
- **drug_name**: The name of the drug.
- **manufacturer**: The manufacturer of the drug.
- **drug_type**: The type or category of the drug.
- **moa**: The mechanism of action for the drug.
- **fda_appr_dt**: The date the drug was approved by the FDA.
- **admin_route**: The administration route for the drug (e.g., 'Oral', 'Topical').
- **dos_amt**: The standard dosage amount.
- **dos_unit**: The unit for the dosage amount (e.g., 'mg').
- **dos_freq_hrs**: The standard dosage frequency in hours.
- **ndc**: The National Drug Code.
- **treatments_used_in**: A list of all treatments this drug was used in (reverse of `Treatments.drug`).

### The `Diagnoses` collection contains the following columns:
- **diag_id**: A unique identifier for the diagnosis.
- **diag_code**: The standardized code for the diagnosis (e.g., ICD-10 code).
- **diag_name**: The name of the diagnosis.
- **diag_desc**: A description of the diagnosis.
- **treatments_for**: A list of all treatments associated with this diagnosis (reverse of `Treatments.diagnosis`).

### The `Treatments` collection contains the following columns:
- **treatment_id**: A unique identifier for the treatment record.
- **patient_id**: Foreign key referencing the `Patients` collection.
- **doc_id**: Foreign key referencing the `Doctors` collection.
- **drug_id**: Foreign key referencing the `Drugs` collection.
- **diag_id**: Foreign key referencing the `Diagnoses` collection.
- **start_dt**: The start date of the treatment.
- **end_dt**: The end date of the treatment.
- **is_placebo**: A flag indicating if the treatment was a placebo.
- **tot_drug_amt**: The total amount of the drug administered during the treatment.
- **drug_unit**: The unit for the total drug amount.
- **doctor**: The corresponding doctor who prescribed the treatment (reverse of `Doctors.prescribed_treatments`).
- **patient**: The corresponding patient who received the treatment (reverse of `Patients.treatments_received`).
- **drug**: The corresponding drug used in the treatment (reverse of `Drugs.treatments_used_in`).
- **diagnosis**: The corresponding diagnosis for which the treatment was administered (reverse of `Diagnoses.treatments_for`).
- **outcome_records**: A list of all outcome records associated with this treatment (reverse of `Outcomes.treatment`).
- **concomitant_meds**: A list of all concomitant medications taken during this treatment (reverse of `ConcomitantMeds.treatment`).
- **adverse_events**: A list of all adverse events reported during this treatment (reverse of `AdverseEvents.treatment`).

### The `Outcomes` collection contains the following columns:
- **outcome_id**: A unique identifier for the outcome record.
- **treatment_id**: Foreign key referencing the `Treatments` collection.
- **assess_dt**: The date the outcome assessment was performed.
- **day7_lesion_cnt**: Lesion count at day 7.
- **day30_lesion_cnt**: Lesion count at day 30.
- **day100_lesion_cnt**: Lesion count at day 100.
- **day7_pasi_score**: PASI score at day 7.
- **day30_pasi_score**: PASI score at day 30.
- **day100_pasi_score**: PASI score at day 100.
- **day7_tewl**: TEWL (Transepidermal Water Loss) measure at day 7.
- **day30_tewl**: TEWL measure at day 30.
- **day100_tewl**: TEWL measure at day 100.
- **day7_itch_vas**: Itch VAS (Visual Analog Scale) score at day 7.
- **day30_itch_vas**: Itch VAS score at day 30.
- **day100_itch_vas**: Itch VAS score at day 100.
- **day7_hfg**: HFG (Hair Follicle Grading) score at day 7.
- **day30_hfg**: HFG score at day 30.
- **day100_hfg**: HFG score at day 100.
- **treatment**: The corresponding treatment for this outcome record (reverse of `Treatments.outcome_records`).

### The `ConcomitantMeds` collection contains the following columns:
- **_id**: A unique identifier for the concomitant medication record.
- **treatment_id**: Foreign key referencing the `Treatments` collection.
- **med_name**: The name of the concomitant medication.
- **start_dt**: The start date of taking the medication.
- **end_dt**: The end date of taking the medication.
- **dose_amt**: The dosage amount of the medication.
- **dose_unit**: The unit for the dosage amount.
- **freq_hrs**: The frequency of dosage in hours.
- **treatment**: The corresponding treatment during which this medication was taken (reverse of `Treatments.concomitant_meds`).

### The `AdverseEvents` collection contains the following columns:
- **_id**: A unique identifier for the adverse event record.
- **treatment_id**: Foreign key referencing the `Treatments` collection.
- **reported_dt**: The date the adverse event was reported.
- **description**: A description of the adverse event.
- **treatment**: The corresponding treatment during which this adverse event occurred (reverse of `Treatments.adverse_events`).

---

### The high-level graph `Ewallet` collection contains the following collections:
- **Users**: Contains information about e-wallet users.
- **Merchants**: Contains information about merchants accepting the e-wallet.
- **Coupons**: Contains information about promotional coupons.
- **Transactions**: Contains records of e-wallet transactions.
- **UserBalances**: Contains daily balances for users.
- **MerchantBalances**: Contains daily balances for merchants.
- **Notifications**: Contains notification records sent to users.
- **UserSessions**: Contains user login session information.
- **UserSettingSnapshots**: Contains snapshots of user settings over time.

### The `Users` collection contains the following columns:
- **uid**: A unique identifier for the user.
- **username**: The username of the user.
- **email**: The email address of the user.
- **phone_number**: The phone number of the user.
- **created_at**: The timestamp when the user account was created.
- **last_login_at**: The timestamp of the user's last login.
- **user_type**: The type of user account (e.g., 'Personal', 'Business').
- **status**: The status of the user account (e.g., 'Active', 'Suspended').
- **country**: The country of the user.
- **address_billing**: The billing address of the user.
- **address_delivery**: The delivery address of the user.
- **kyc_status**: The Know Your Customer verification status.
- **kyc_verified_at**: The timestamp when KYC verification was completed.
- **transactions_sent**: A list of all transactions sent by this user (reverse of `Transactions.sending_user`).
- **transactions_received**: A list of all transactions received by this user (reverse of `Transactions.receiving_user`).
- **balances**: A list of all balance records for this user (reverse of `UserBalances.user`).
- **notifications**: A list of all notifications sent to this user (reverse of `Notifications.user`).
- **sessions**: A list of all login sessions for this user (reverse of `UserSessions.user`).
- **setting_snapshots**: A list of all setting snapshots for this user (reverse of `UserSettingSnapshots.user`).

### The `Merchants` collection contains the following columns:
- **mid**: A unique identifier for the merchant.
- **name**: The name of the merchant.
- **description**: A description of the merchant's business.
- **website_url**: The URL of the merchant's website.
- **logo_url**: The URL of the merchant's logo.
- **created_at**: The timestamp when the merchant account was created.
- **country**: The country where the merchant is located.
- **state**: The state where the merchant is located.
- **city**: The city where the merchant is located.
- **postal_code**: The postal code where the merchant is located.
- **address**: The street address of the merchant.
- **status**: The status of the merchant account (e.g., 'Active', 'Verified').
- **category**: The business category of the merchant.
- **sub_category**: The business sub-category of the merchant.
- **mcc**: The Merchant Category Code.
- **contact_name**: The name of the contact person at the merchant.
- **contact_email**: The email address of the contact person.
- **contact_phone**: The phone number of the contact person.
- **transactions_sent**: A list of all transactions sent by this merchant (reverse of `Transactions.sending_merchant`).
- **transactions_received**: A list of all transactions received by this merchant (reverse of `Transactions.receiving_merchant`).
- **balances**: A list of all balance records for this merchant (reverse of `MerchantBalances.merchant`).
- **coupons**: A list of all coupons issued by this merchant (reverse of `Coupons.merchant`).

### The `Coupons` collection contains the following columns:
- **cid**: A unique identifier for the coupon.
- **merchant_id**: Foreign key referencing the `Merchants` collection.
- **code**: The code for the coupon.
- **description**: A description of the coupon offer.
- **start_date**: The date the coupon becomes valid.
- **end_date**: The date the coupon expires.
- **discount_type**: The type of discount (e.g., 'Percentage', 'Fixed Amount').
- **discount_value**: The value of the discount.
- **min_purchase_amount**: The minimum purchase amount required to use the coupon.
- **max_discount_amount**: The maximum discount amount applicable.
- **redemption_limit**: The maximum number of times the coupon can be redeemed.
- **status**: The status of the coupon (e.g., 'Active', 'Expired').
- **created_at**: The timestamp when the coupon was created.
- **updated_at**: The timestamp when the coupon was last updated.
- **transaction_used_in**: A list of all transactions where this coupon was used (reverse of `Transactions.coupon`).
- **merchant**: The corresponding merchant who issued this coupon (reverse of `Merchants.coupons`).

### The `Transactions` collection contains the following columns:
- **txid**: A unique identifier for the transaction.
- **sender_id**: The identifier of the sender (User uid or Merchant mid).
- **sender_type**: The type of the sender (e.g., 1 for User, 2 for Merchant).
- **receiver_id**: The identifier of the receiver (User uid or Merchant mid).
- **receiver_type**: The type of the receiver (e.g., 1 for User, 2 for Merchant).
- **amount**: The amount of the transaction.
- **status**: The status of the transaction (e.g., 'Completed', 'Failed').
- **transaction_type**: The type of transaction (e.g., 'Transfer', 'Payment') (from `type`).
- **description**: A description of the transaction.
- **coupon_id**: Foreign key referencing the `Coupons` collection, if applicable.
- **created_at**: The timestamp when the transaction was initiated.
- **completed_at**: The timestamp when the transaction was completed or finalized.
- **transaction_ref**: An external reference for the transaction.
- **gateway_name**: The name of the payment gateway used, if any.
- **gateway_ref**: A reference identifier from the payment gateway.
- **device_id**: The identifier of the device used for the transaction.
- **ip_address**: The IP address from which the transaction originated.
- **user_agent**: The user agent string of the client initiating the transaction.
- **sending_user**: The corresponding user who sent this transaction (reverse of `Users.transactions_sent`).
- **receiving_user**: The corresponding user who received this transaction (reverse of `Users.transactions_received`).
- **sending_merchant**: The corresponding merchant who sent this transaction (reverse of `Merchants.transactions_sent`).
- **receiving_merchant**: The corresponding merchant who received this transaction (reverse of `Merchants.transactions_received`).
- **coupon**: The corresponding coupon used in this transaction (reverse of `Coupons.transaction_used_in`).

### The `UserBalances` collection contains the following columns:
- **user_id**: Foreign key referencing the `Users` collection.
- **balance**: The user's balance at the end of the day.
- **updated_at**: The timestamp (usually date) for which the balance is recorded.
- **user**: The corresponding user for this balance record (reverse of `Users.balances`).

### The `MerchantBalances` collection contains the following columns:
- **merchant_id**: Foreign key referencing the `Merchants` collection.
- **balance**: The merchant's balance at the end of the day.
- **updated_at**: The timestamp (usually date) for which the balance is recorded.
- **merchant**: The corresponding merchant for this balance record (reverse of `Merchants.balances`).

### The `Notifications` collection contains the following columns:
- **_id**: A unique identifier for the notification.
- **user_id**: Foreign key referencing the `Users` collection.
- **message**: The content of the notification message.
- **notification_type**: The type of notification (e.g., 'Transaction', 'Promotion') (from `type`).
- **status**: The status of the notification (e.g., 'Sent', 'Read').
- **created_at**: The timestamp when the notification was created.
- **read_at**: The timestamp when the notification was read by the user.
- **device_type**: The type of device the notification was sent to (e.g., 'iOS', 'Android').
- **device_id**: The specific device identifier.
- **action_url**: A URL associated with the notification for user action.
- **user**: The corresponding user who received this notification (reverse of `Users.notifications`).

### The `UserSessions` collection contains the following columns:
- **user_id**: Foreign key referencing the `Users` collection.
- **session_start_ts**: The timestamp when the user session started.
- **session_end_ts**: The timestamp when the user session ended.
- **device_type**: The type of device used for the session.
- **device_id**: The identifier of the device used for the session.
- **user**: The corresponding user for this session record (reverse of `Users.sessions`).

### The `UserSettingSnapshots` collection contains the following columns:
- **user_id**: Foreign key referencing the `Users` collection.
- **snapshot_date**: The date the settings snapshot was taken.
- **tx_limit_daily**: The user's daily transaction limit at the time of the snapshot.
- **tx_limit_monthly**: The user's monthly transaction limit at the time of the snapshot.
- **membership_status**: The user's membership status level.
- **password_hash**: The hash of the user's password (for historical reference, potentially sensitive).
- **api_key**: The user's API key, if applicable.
- **verified_devices**: A list or representation of devices verified for the user.
- **verified_ips**: A list or representation of IP addresses verified for the user.
- **mfa_enabled**: A flag indicating if Multi-Factor Authentication was enabled.
- **marketing_opt_in**: A flag indicating if the user opted into marketing communications.
- **created_at**: The timestamp when the snapshot record was created.
- **user**: The corresponding user for this settings snapshot (reverse of `Users.setting_snapshots`).