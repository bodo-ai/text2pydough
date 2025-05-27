**CONTEXTLESS EXPRESSIONS**   

- **Purpose**: Reusable code snippets.  

- **Example**: Define and reuse filters:  

  is_high_value = package_cost > 1000  
  high_value_packages = Packages.WHERE(is_high_value)