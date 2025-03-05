**FILTERING (WHERE)**  

- **Syntax**: .WHERE(condition)  

- **Examples**:  

  - **Filter people with negative account balance**:  
    People.WHERE(acctbal < 0)  

  - **Filter packages ordered in 2023**:  
    Packages.WHERE(YEAR(order_date) == 2023)  

  - **Filter addresses with occupants**:  
    Addresses.WHERE(HAS(current_occupants))  

- **Warnings**:  
  - Use & (AND), | (OR), ~ (NOT) instead of and, or, not.  
  - Avoid chained comparisons (e.g., replace a < b < c with (a < b) & (b < c)).