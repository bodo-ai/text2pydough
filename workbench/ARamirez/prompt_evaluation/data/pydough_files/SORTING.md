**VERY IMPORTANT NOTES**

  - Always use TOP_K instead of ORDER_BY when you need to order but also select a the high, low or an specific "k" number of records.
  
  - TOP_K function ALWAYS need 2 parameters `k and by`. The “by” parameter must never have collections, subcollections or calculations. Any required variable or value must have been previously calculated, because the parameter only accept expressions. The k is the number of records you want to return

**SORTING (ORDER_BY)**  

- **Syntax**: .ORDER_BY(field.ASC()/DESC(), ...)  

- **Examples**:  

  - **Alphabetical sort**:  
    People.ORDER_BY(last_name.ASC(), first_name.ASC())  

  - **Most expensive packages first**:  
    Packages.ORDER_BY(package_cost.DESC())  

- **Parameters**:  

  .ASC(na_pos='last') → Sort ascending, nulls last.  

  .DESC(na_pos='first') → Sort descending, nulls first.

**5. SORTING TOP_K(k, by=field.DESC())**  

- **Select top k records.**

- **Syntax:**  
  .TOP_K(k, by=field.DESC())

- **Example:**  
  Top 10 customers by orders count:  
  customers.TOP_K(10, by=COUNT(orders).DESC())

  Top 10 customers by orders count (but also selecting only the name):  
  customers.CALCULATE(cust_name=name).TOP_K(10, by=COUNT(orders).DESC())