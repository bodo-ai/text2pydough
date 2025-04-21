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