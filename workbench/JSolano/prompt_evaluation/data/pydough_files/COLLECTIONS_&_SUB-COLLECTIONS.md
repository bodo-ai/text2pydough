**COLLECTIONS & SUB-COLLECTIONS**  

- **Syntax**: Access collections/sub-collections using dot notation.  

- **Examples**:  
  - `People` → Access all records in the 'People' collection.  
  - `People.current_address` → Access current addresses linked to people.  
  - `Packages.customer` → Access customers linked to packages.  

- **Warnings**:  
  - Sub-collections must exist in the metadata graph (e.g., `People.packages` is valid; undefined sub-collections like `People.orders` are invalid).  
  - Avoid reassigning collection names to variables (e.g., `Addresses = 42` breaks subsequent access).