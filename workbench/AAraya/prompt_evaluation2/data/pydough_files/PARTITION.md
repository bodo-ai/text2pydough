**IMPORTANT NOTES**

 - Partition keys must be scalar fields from the collection. 
 - You must use Aggregation functions to call plural values inside PARTITION.
 - Within a partition, you must use the `name` argument to be able to access any property or subcollections. 
 - PARTITION function ALWAYS need 3 parameters `Collection, name and by`. The ""by"" parameter must never have collections, subcollections or calculations. Any required variable or value must have been previously calculated, because the parameter only accept expressions. 

**PARTITION**  

- **Purpose**: Group records by keys.  

- **Syntax**: PARTITION(Collection, name='group_name', by=(key1, key2))  

  - **IMPORTANT**: The `name` argument is a string indicating the name that is to be used when accessing the partitioned data. 

  - **IMPORTANT**: Al the parameters in ""by=(key1, key2)"" must be use in CALCULATE without using the ""name"" of the PARTITION. As opposed to any other term, which needs the name because that is the context. 

- **Good Examples**:  

  - **Group addresses by state and count occupants**:  
    PARTITION(Addresses, name='addrs', by=state).CALCULATE(  
        state=state,  
        total_occupants=COUNT(addrs.current_occupants)  
    )  
    **IMPORTANT**: Look here, where we do not need to use  ""addrs.state"", we only use ""state"", because this is in the ""by"" sentence. 

  - **Group packages by year/month**:  
    PARTITION(Packages, name='packs', by=(YEAR(order_date), MONTH(order_date)))  

   - **For every year/month, find all packages that were below the average cost of all packages ordered in that year/month.**:  Notice how `packs` can access `avg_package_cost`, which was defined by its ancestor (at the `PARTITION` level).
    package_info = Packages.CALCULATE(order_year=YEAR(order_date), order_month=MONTH(order_date))
    PARTITION(package_info, name="packs", by=(order_year, order_month)).CALCULATE(
        avg_package_cost=AVG(packs.package_cost)
    ).packs.WHERE(
        package_cost < avg_package_cost
    )

- **Bad Examples**:
  - **Partition people by their birth year to find the number of people born in each year**: Invalid because the email property is referenced, which is not one of the properties accessible by the partition.
    PARTITION(People(birth_year=YEAR(birth_date)), name=\""ppl\"", by=birth_year)(
        birth_year,
        email,
        n_people=COUNT(ppl)
    )

  - **Count how many packages were ordered in each year**: Invalid because YEAR(order_date) is not allowed to be used as a partition term (it must be placed in a CALC so it is accessible as a named reference).
    PARTITION(Packages, name=\""packs\"", by=YEAR(order_date)).CALCULATE(
        n_packages=COUNT(packages)
    )

  - **Count how many people live in each state**: Invalid because current_address.state is not allowed to be used as a partition term (it must be placed in a CALC so it is accessible as a named reference).
    PARTITION(People, name=\""ppl\"", by=current_address.state).CALCULATE(
        n_packages=COUNT(packages)
    )

