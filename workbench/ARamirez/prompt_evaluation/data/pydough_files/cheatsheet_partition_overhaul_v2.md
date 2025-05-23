<PyDoughCheatSheet>
  The examples shown are not from the current database; just treat them as examples.
  <GeneralRules>
    <Rules>
    Use `HAS` function to verify the 1 to N relationship between tables, and you can identify them because the related subcollection has a plural name.
    This is NOT SQL, so don't make assumptions about its syntax or behavior.
    Always use TOP_K instead of ORDER_BY when you need to order but also select a the high, low or an specific "k" number of records.
    If a query does not specify an specific year, and want that you calculate for all the year, for example "compare year over year", then the requested calculation must be performed for each year available in TPC: 1995, 1996, 1995 and 1998. You need to use SINGULAR function to call every year in the final result.
    If you need to use an attribute of a previous collection, you must have calculated the attribute using CALCULATE.
    CALCULATE ONLY supports singular expressions. If you need to use plural sub-collections, you MUST use aggregation functions.
    RANKING is used as a function instead of method.
    When using functions like TOP_K, ORDER_BY, you must ALWAYS provide an expression, not a collection.
    PARTITION function ALWAYS need 2 parameters `name and by`. The "by" parameter must never have collections, subcollections or calculations.
    PARTITION must always be used as a method. Never do PARTITION by the key or the collection key.
    CALCULATE function ALWAYS needs an expression, not a collection.
    In PyDough, complex calculations can often be expressed concisely by combining filters, transformations, and aggregations at the appropriate hierarchical level.
    PyDough does not support use different childs in operations, for example you cannot do: `total_order_value = SUM(orders.lines.extended_price * (1 - orders.lines.discount))` because you have two different calls.
    If you need to get the best rankings within a CALCULATE method, you can use the RANKING method instead of TOP_K, and then filter them by the ranking number.</Rules>
  </GeneralRules>

  <CollectionsSubCollections>
    <Syntax>Access collections/sub-collections using dot notation.</Syntax>
    <Examples>
      People → Access all records in the 'People' collection.
      People.current_address → Access current addresses linked to people.
      Packages.customer → Access customers linked to packages.
    </Examples>
  </CollectionsSubCollections>

  <CalculateExpressions>
    <Purpose>Derive new fields, rename existing ones or select specific fields.</Purpose>
    <Syntax>Collection.CALCULATE(field=expression, ...)</Syntax>
    <Examples>
      Select fields: People.CALCULATE(first_name=first_name, last_name=last_name)
      Derived fields= Packages.CALCULATE(  
              customer_name=JOIN_STRINGS(' ', customer.first_name, customer.last_name),  
              cost_per_unit=package_cost / quantity  
          )
    </Examples>
    <Rules>
      Use aggregation functions (e.g., SUM, COUNT) for plural sub-collections.
      Positional arguments must precede keyword arguments.
      New fields defined in a CALCULATE do not take effect until after the CALCULATE completes.
      Existing new fields not included in a CALCULATE can still be referenced but are not part of the final result unless included in the last CALCULATE clause.
      A CALCULATE on the graph itself creates a collection with one row and columns corresponding to the properties inside the CALCULATE.
    </Rules>
  </CalculateExpressions>

  <Filtering>
    <Syntax>.WHERE(condition)</Syntax>
    <Examples>
      Filter people with negative account balance: ```People.WHERE(acctbal < 0)```
      Filter packages ordered in 2023: ```Packages.WHERE(YEAR(order_date) == 2023)```
      Filter addresses with occupants: ```Addresses.WHERE(HAS(current_occupants)==1)```
    </Examples>
    <Rules>
      Use &amp; (AND), | (OR), ~ (NOT) instead of and, or, not.
      Avoid chained comparisons (e.g., replace a &lt; b &lt; c with (a &lt; b) &amp; (b &lt; c)).
    </Rules>
  </Filtering>

  <Sorting>
    <Syntax>.ORDER_BY(field.ASC()/DESC(), ...)</Syntax>
    <Parameters>
      .ASC(na_pos='last') → Sort ascending, nulls last.
      .DESC(na_pos='first') → Sort descending, nulls first.
    </Parameters>
    <Examples>
      Alphabetical sort: ```People.ORDER_BY(last_name.ASC(), first_name.ASC())```
      Most expensive packages first: ```Packages.ORDER_BY(package_cost.DESC())```
    </Examples>
  </Sorting>

  <TopK>
    <Purpose>Select top k records.</Purpose>
    <Syntax>.TOP_K(k, by=field.DESC())</Syntax>
    <Example>
      Top 10 customers by orders count: ```customers.TOP_K(10, by=COUNT(orders).DESC())```
    </Example>
    <Rules>
      The two parameters are obligatory.
    </Rules>
  </TopK>

  <AggregationFunctions>
    <Functions>
      <Function>
        <Name>HAS(collection)</Name>
        <Description>True if ≥1 record exists.</Description>
        <Example>HAS(People.packages)==1</Example>
      </Function>
      <Function>
        <Name>HASNOT(collection)</Name>
        <Description>True if collection is empty.</Description>
        <Example>HASNOT(orders)==1</Example>
      </Function>
      <Function>
        <Name>COUNT(collection)</Name>
        <Description>Count non-null records.</Description>
        <Example>COUNT(People.packages)</Example>
      </Function>
      <Function>
        <Name>SUM(collection)</Name>
        <Description>Sum values.</Description>
        <Example>SUM(Packages.package_cost)</Example>
      </Function>
      <Function>
        <Name>AVG(collection)</Name>
        <Description>Average values.</Description>
        <Example>AVG(Packages.quantity)</Example>
      </Function>
      <Function>
        <Name>MIN/MAX(collection)</Name>
        <Description>Min/Max value.</Description>
        <Example>MIN(Packages.order_date)</Example>
      </Function>
      <Function>
        <Name>NDISTINCT(collection)</Name>
        <Description>Distinct count.</Description>
        <Example>NDISTINCT(Addresses.state)</Example>
      </Function>
    </Functions>
    <Rules>
      Aggregations Function does not support calling aggregations inside of aggregations
    </Rules>
  </AggregationFunctions>

  <Partition>
    <Purpose>Group records by keys.</Purpose>
    <Syntax>PARTITION(name='group_name', by=(key1, key2))</Syntax>
    <Rules>
      All the parameters in "by=(key1, key2)" must be use in CALCULATE without using the "name" of the PARTITION.
      Partition keys must be scalar fields from the collection.
      You must use Aggregation functions to call plural values inside PARTITION.
    </Rules>
    <Examples>
      1. Group addresses by state and count occupants: 
      ```
      Addresses.PARTITION(name="states", by=(state)).CALCULATE(
        state,
        n_people=COUNT(Addresses.current_occupants)
      )
      ```
      2. Group packages by year/month:
      ```
      package_info = Packages.CALCULATE(order_year=YEAR(order_date), order_month=MONTH(order_date))
      package_info.PARTITION(name='packs', by=(order_year, order_month))
      ```
      3. Find packages below average cost for their year/month:
      ```
        package_info = Packages.CALCULATE(order_year=YEAR(order_date), order_month=MONTH(order_date))
        package_info.PARTITION(name="months", by=(order_year, order_month)).CALCULATE(
        avg_package_cost=AVG(Packages.package_cost)).Packages.WHERE(package_cost &lt; avg_package_cost)
      ```
        
      4. Find the top 5 years with the most people born in that year who have yahoo email accounts:
      ```  
        yahoo_people = People.CALCULATE(
            birth_year=YEAR(birth_date)
        ).WHERE(ENDSWITH(email, "@yahoo.com"))
        yahoo_people.PARTITION(name="years", by=birth_year).CALCULATE(
            birth_year,
            n_people=COUNT(People)
        ).TOP_K(5, by=n_people.DESC())
      ```
      5: Identify the states whose current occupants account for at least 1% of all packages purchased:
      ```
          GRAPH.CALCULATE(
              total_packages=COUNT(Packages)
          ).Addresses.WHERE(
            HAS(current_occupants.package) == 1
          ).PARTITION(name="states", by=state).CALCULATE(
              state,
              pct_of_packages=100.0 * COUNT(Addresses.current_occupants.package) / total_packages
          ).WHERE(pct_of_packages >= 1.0)
        ```

    6: Identify which months of the year have numbers of packages shipped in that month that are above the average for all months:
    ```
        pack_info = Packages.CALCULATE(order_month=MONTH(order_date))
        month_info = pack_info.PARTITION(name="months", by=order_month).CALCULATE(
            n_packages=COUNT(Packages)
        )
        GRAPH.CALCULATE(
            avg_packages_per_month=AVG(month_info.n_packages)
        ).PARTITION(pack_info, name="months", by=order_month).CALCULATE(
            month,
        ).WHERE(COUNT(Packages) > avg_packages_per_month)
      ```
     

    <Example>
      <Name>Good Example #6: Find the 10 most frequent combinations of the state that the person lives in and the first letter of that person's name</Name>
      <Code>
        people_info = Addresses.WHERE(
          HAS(current_occupants) == 1
        ).CALCULATE(state).current_occupants.CALCULATE(
            first_letter=first_name[:1],
        )
        people_info.PARTITION(name="combinations", by=(state, first_letter)).CALCULATE(
            state,
            first_letter,
            n_people=COUNT(current_occupants),
        ).TOP_K(10, by=n_people.DESC())
      </Code>
    </Example>

    <Example>
      <Name>Good Example #7: Same as good example #6, but written differently so it will include people without a current address</Name>
      <Code>
        people_info = People.CALCULATE(
            state=DEFAULT_TO(current_address.state, "N/A"),
            first_letter=first_name[:1],
        )
        people_info.PARTITION(name="state_letter_combos", by=(state, first_letter)).CALCULATE(
            state,
            first_letter,
            n_people=COUNT(People),
        ).TOP_K(10, by=n_people.DESC())
      </Code>
    </Example>

    <Example>
      <Name>Good Example #8: Partition the current occupants of each address by their birth year and filter to include individuals born in years with at least 10,000 births</Name>
      <Code>
        people_info = Addresses.WHERE(
          HAS(current_occupants)==1
        ).CALCULATE(state).current_occupants.CALCULATE(birth_year=YEAR(birth_date))
        people_info.PARTITION(name="years", by=birth_year).WHERE(
            COUNT(current_occupants) >= 10000
        ).current_occupants.CALCULATE(
            first_name,
            last_name,
            state
        )
      </Code>
    </Example>

    <Example>
      <Name>Good Example #9: Find all packages that meet the following criteria: they were ordered in the last year that any package in the database was ordered, their cost was below the average of all packages ever ordered, and the state it was shipped to received at least 10,000 packages that year</Name>
      <Code>
        GRAPH.CALCULATE(
            avg_cost=AVG(Packages.package_cost),
            final_year=MAX(Packages.order_year),
        ).Packages.CALCULATE(
            order_year=YEAR(order_date),
            shipping_state=shipping_address.state
        ).WHERE(order_year == final_year
        ).PARTITION(
            name="states",
            by=shipping_state
        ).WHERE(
            COUNT(Packages) > 10000
        ).Packages.WHERE(
            package_cost < avg_cost
        ).CALCULATE(
            shipping_state,
            package_id,
            order_date,
        )
      </Code>
    </Example>

    <Example>
      <Name>Good Example #10: For each state, finds the largest number of packages shipped to a single city in that state</Name>
      <Code>
        pack_info = Addresses.CALCULATE(city, state).packages_shipped_to
        city_groups = pack_info.PARTITION(
            name="cities", by=(city, state)
        ).CALCULATE(n_packages=COUNT(packages_shipped_to))
        city_groups.PARTITION(
            name="states", by=state
        ).CALCULATE(state, max_packs=MAX(cities.n_packages))
      </Code>
    </Example>
    <Examples>
  </Partition>

  <WindowFunctions>
    <Ranking>
      <Syntax>RANKING(by=field.DESC(), per='collection', allow_ties=False)</Syntax>
      <Parameters>
        by: Ordering criteria (e.g., acctbal.DESC())
        per: Hierarchy level (e.g.,per="nation" for per-nation ranking)
        allow_ties (default False): Allow tied ranks
        dense (default False): Use dense ranking
      </Parameters>
      <Examples>
        <Example>
          <Code>
            # Rank every customer relative to all other customers by acctbal
            Regions.nations.customers.CALCULATE(r=RANKING(by=acctbal.DESC()))
          </Code>
        </Example>
        <Example>
          <Code>
            # Rank every customer relative to other customers in the same nation, by acctbal
            Regions.nations.customers.CALCULATE(r=RANKING(by=acctbal.DESC(), per="nations"))
          </Code>
        </Example>
      </Examples>
    </Ranking>
    
    <Percentile>
      <Syntax>PERCENTILE(by=field.ASC(), n_buckets=100, per="name_antecesor")</Syntax>
      <Parameters>
        by: Ordering criteria
        per (optional): optional argument (default None) for the same per argument as all other window functions
        n_buckets (default 100): Number of percentile buckets
      </Parameters>
      <Example>
        <Code>
          # Keep the top 0.1% of customers with the highest account balances
          Customers.WHERE(PERCENTILE(by=acctbal.ASC(), n_buckets=1000) == 1000)
        </Code>
      </Example>
    </Percentile>
    
    <RelSum>
      <Syntax>RELSUM(expression, per=None)</Syntax>
      <Parameters>
        expression: the singular expression to take the sum of across multiple rows
        per (optional): optional argument (default None) for the same per argument as all other window functions
      </Parameters>
      <Example>
        <Code>
          # Finds the ratio between each customer's account balance and the global sum
          Customers.CALCULATE(ratio=acctbal / RELSUM(acctbal))
        </Code>
      </Example>
    </RelSum>
    
    <RelAvg>
      <Syntax>RELAVG(expression, per=None)</Syntax>
      <Parameters>
        expression: the singular expression to take the average of across multiple rows
        per (optional): optional argument (default None) for the same per argument as all other window functions
      </Parameters>
      <Example>
        <Code>
          # Finds all customers whose account balance is above the global average
          Customers.WHERE(acctbal > RELAVG(acctbal))
        </Code>
      </Example>
    </RelAvg>
    
    <RelCount>
      <Syntax>RELCOUNT(expression, per=None)</Syntax>
      <Parameters>
        expression: the singular expression to count the number of non-null entries across multiple rows
        per (optional): optional argument (default None) for the same per argument as all other window functions
      </Parameters>
      <Example>
        <Code>
          # Divides each customer's account balance by the total number of positive account balances globally
          Customers.CALCULATE(ratio = acctbal / RELCOUNT(KEEP_IF(acctbal, acctbal > 0.0)))
        </Code>
      </Example>
    </RelCount>
    
    <RelSize>
      <Syntax>RELSIZE(per=None)</Syntax>
      <Parameters>
        per (optional): optional argument (default None) for the same per argument as all other window functions
      </Parameters>
      <Example>
        <Code>
          # Divides each customer's account balance by the number of total customers
          Customers.CALCULATE(ratio = acctbal / RELSIZE())
        </Code>
      </Example>
    </RelSize>
  </WindowFunctions>

  <ContextlessExpressions>
    <Purpose>Reusable code snippets.</Purpose>
    <Example>
      <Code>
        is_high_value = package_cost > 1000  
        high_value_packages = Packages.WHERE(is_high_value)
      </Code>
    </Example>
  </ContextlessExpressions>

  <Singular>
    <Purpose>SINGULAR in PyDough ensures data is explicitly treated as singular in sub-collection contexts, preventing undefined behavior if used correctly.</Purpose>
    <Examples>
      <Description>Access the package cost of the most recent package ordered by each person</Description>
      <Code>
        most_recent_package = packages.WHERE(
            RANKING(by=order_date.DESC(), levels=1) == 1
        ).SINGULAR()
        People.CALCULATE(
            ssn,
            first_name,
            middle_name,
            last_name,
            most_recent_package_cost=most_recent_package.package_cost
        )
        </Code>
    </Examples>
  </Singular>

  <BinaryOperators>
    <Arithmetic>
      <Operators>+, -, *, /, ** (addition, subtraction, multiplication, division, exponentiation)</Operators>
      <Example>Lineitems(value = (extended_price * (1 - (discount ** 2)) + 1.0) / part.retail_price)</Example>
      <Warning>Division by 0 behavior depends on the database.</Warning>
    </Arithmetic>
    <Comparisons>
      <Operators>&lt;=, &lt;, ==, !=, >, >=</Operators>
      <Example>Customers(in_debt = acctbal &lt; 0, is_european = nation.region.name == "EUROPE")</Example>
      <Warning>Avoid chained inequalities (e.g., a &lt;= b &lt;= c). Use (a &lt;= b) &amp; (b &lt;= c) or MONOTONIC.</Warning>
    </Comparisons>
    <Logical>
      <Operators>&amp; (AND), | (OR), ~ (NOT)</Operators>
      <Example>Customers(is_eurasian = (nation.region.name == "ASIA") | (nation.region.name == "EUROPE"))</Example>
      <Warning>Use &amp;, |, ~ instead of Python's and, or, not.</Warning>
    </Logical>
  </BinaryOperators>

  <UnaryOperators>
    <Negation>
      <Operator>- (flips sign)</Operator>
      <Example>Lineitems(lost_value = extended_price * (-discount))</Example>
    </Negation>
  </UnaryOperators>

  <OtherOperators>
    <Slicing>
      <Syntax>string[start:stop:step]</Syntax>
      <Example>Customers(country_code = phone[:3])</Example>
      <Rules>
        Step must be 1 or omitted; start/stop non-negative or omitted.
      </Rules>
    </Slicing>
  </OtherOperators>

  <StringFunctions>
    <Function>
      <Name>LOWER(s)</Name>
      <Description>Converts string to lowercase</Description>
      <Example>LOWER(name) → "apple"</Example>
    </Function>
    <Function>
      <Name>UPPER(s)</Name>
      <Description>Converts string to uppercase</Description>
      <Example>UPPER(name) → "APPLE"</Example>
    </Function>
    <Function>
      <Name>LENGTH(s)</Name>
      <Description>Returns character count</Description>
      <Example>LENGTH(comment) → 42</Example>
    </Function>
    <Function>
      <Name>STARTSWITH(s, prefix)</Name>
      <Description>Checks prefix match</Description>
      <Example>STARTSWITH(name, "yellow") → True/False</Example>
    </Function>
    <Function>
      <Name>ENDSWITH(s, suffix)</Name>
      <Description>Checks suffix match</Description>
      <Example>ENDSWITH(name, "chocolate") → True/False</Example>
    </Function>
    <Function>
      <Name>CONTAINS(s, substr)</Name>
      <Description>Checks substring presence</Description>
      <Example>CONTAINS(name, "green") → True/False</Example>
    </Function>
    <Function>
      <Name>LIKE(s, pattern)</Name>
      <Description>SQL-style pattern matching (%, _)</Description>
      <Example>LIKE(comment, "%special%") → True/False</Example>
    </Function>
    <Function>
      <Name>JOIN_STRINGS(delim, s1, s2, ...)</Name>
      <Description>Joins strings with a delimiter</Description>
      <Example>JOIN_STRINGS("-", "A", "B") → "A-B"</Example>
    </Function>
  </StringFunctions>

  <DateTimeFunctions>
    <Function>
      <Name>YEAR(dt)</Name>
      <Description>Extracts year</Description>
      <Example>YEAR(order_date) == 1995</Example>
    </Function>
    <Function>
      <Name>MONTH(dt)</Name>
      <Description>Extracts month (1-12)</Description>
      <Example>MONTH(order_date) >= 6</Example>
    </Function>
    <Function>
      <Name>DAY(dt)</Name>
      <Description>Extracts day (1-31)</Description>
      <Example>DAY(order_date) == 1</Example>
    </Function>
    <Function>
      <Name>HOUR(dt)</Name>
      <Description>Extracts hour (0-23)</Description>
      <Example>HOUR(order_date) == 12</Example>
    </Function>
    <Function>
      <Name>MINUTE(dt)</Name>
      <Description>Extracts minute (0-59)</Description>
      <Example>MINUTE(order_date) == 30</Example>
    </Function>
    <Function>
      <Name>SECOND(dt)</Name>
      <Description>Extracts second (0-59)</Description>
      <Example>SECOND(order_date) &lt; 30</Example>
    </Function>
    <Function>
      <Name>DATETIME</Name>
      <Description>Builds/augments date/timestamp values</Description>
      <Example>
        <Code>
          # Returns the current timestamp
          TPCH.CALCULATE(ts_1=DATETIME('now'))
          
          # For each order, truncates the order date to the first day of the year
          Orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))
        </Code>
      </Example>
    </Function>
    <Function>
      <Name>DATEDIFF</Name>
      <Description>Returns the difference between two timestamps in specified units</Description>
      <Example>
        <Code>
          # Calculates, for each order, the number of days since January 1st 1992
          Orders.CALCULATE( 
            days_since=DATEDIFF("days", datetime.date(1992, 1, 1), order_date)
          )
        </Code>
      </Example>
    </Function>
  </DateTimeFunctions>

  <ConditionalFunctions>
    <Function>
      <Name>IFF(cond, a, b)</Name>
      <Description>Returns a if cond is True, else b</Description>
      <Example>IFF(acctbal > 0, acctbal, 0)</Example>
    </Function>
    <Function>
      <Name>ISIN(val, (x, y))</Name>
      <Description>Checks membership in a list</Description>
      <Example>ISIN(size, (10, 11)) → True/False</Example>
    </Function>
    <Function>
      <Name>DEFAULT_TO(a, b)</Name>
      <Description>Returns first non-null value</Description>
      <Example>DEFAULT_TO(tax, 0)</Example>
    </Function>
    <Function>
      <Name>KEEP_IF(a, cond)</Name>
      <Description>Returns a if cond is True, else null</Description>
      <Example>KEEP_IF(acctbal, acctbal > 0)</Example>
    </Function>
    <Function>
      <Name>MONOTONIC(a, b, c)</Name>
      <Description>Checks ascending order</Description>
      <Example>MONOTONIC(5, part.size, 10) → True/False</Example>
    </Function>
  </ConditionalFunctions>

  <NumericalFunctions>
    <Function>
      <Name>ABS(x)</Name>
      <Description>Absolute value</Description>
      <Example>ABS(-5) → 5</Example>
    </Function>
    <Function>
      <Name>ROUND(x, decimals)</Name>
      <Description>Rounds to decimals places</Description>
      <Example>ROUND(3.1415, 2) → 3.14</Example>
    </Function>
    <Function>
      <Name>POWER(x, exponent)</Name>
      <Description>Raises x to a power</Description>
      <Example>POWER(3, 2) → 9</Example>
    </Function>
    <Function>
      <Name>SQRT(x)</Name>
      <Description>Square root of x</Description>
      <Example>SQRT(16) → 4</Example>
    </Function>
  </NumericalFunctions>

  <ExampleQueries>
    <Query>
      <Description>Top 5 States by Average Occupants</Description>
      <Code>
        addr_info = Addresses.WHERE(
          HAS(current_occupants) == 1
        ).CALCULATE(n_occupants=COUNT(current_occupants))  
        average_occupants=PARTITION(addr_info, name="addrs", by=state).CALCULATE(  
            state=state,  
            avg_occupants=AVG(addrs.n_occupants)  
        ).TOP_K(5, by=avg_occupants.DESC())
      </Code>
    </Query>
    <Query>
      <Description>Monthly Trans-Coastal Shipments</Description>
      <Code>
        west_coast = ("CA", "OR", "WA")  
        east_coast = ("NY", "NJ", "MA")  
        monthly_shipments= Packages.WHERE(  
            ISIN(customer.current_address.state, west_coast) &amp;  
            ISIN(shipping_address.state, east_coast)  
        ).CALCULATE(  
            month=MONTH(order_date),  
            year=YEAR(order_date)  
        )
      </Code>
    </Query>
    <Query>
      <Description>Calculates, for each order, the number of days since January 1st 1992</Description>
      <Code>
        Orders.CALCULATE( 
          days_since=DATEDIFF("days",datetime.date(1992, 1, 1), order_date)
        )
      </Code>
    </Query>
    <Query>
      <Description>Filter Nations by Name</Description>
      <Code>
        nations_startwith = nations.CALCULATE(n_name=name, n_comment=comment).WHERE(STARTSWITH(name, 'A'))  
        nations_like = nations.CALCULATE(n_name=name, n_comment=comment).WHERE(LIKE(name, 'A%'))
      </Code>
    </Query>
    <Query>
      <Description>Customers in Debt from Specific Region</Description>
      <Code>
        customer_in_debt = customers.CALCULATE(customer_name = name).WHERE(  
            (acctbal &lt; 0) &amp;  
            (COUNT(orders) >= 5) &amp;  
            (nation.region.name == "AMERICA") &amp;  
            (nation.name != "BRAZIL")  
        )
      </Code>
    </Query>
    <Query>
      <Description>For each order, truncates the order date to the first day of the year</Description>
      <Code>
        Orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))
      </Code>
    </Query>
    <Query>
      <Description>Orders per Customer in 1998</Description>
      <Code>
        customer_order_counts = customers.WHERE(
          HAS(orders) == 1
        ).CALCULATE(  
            key=key, 
            name=name,  
            num_orders=COUNT(orders.WHERE(YEAR(order_date) == 1998))  
        ).ORDER_BY(num_orders.DESC())
      </Code>
    </Query>
    <Query>
      <Description>High-Value Customers in Asia</Description>
      <Code>
        high_value_customers_in_asia = customers.WHERE(
          HAS(orders) == 1
        ).CALCULATE(  
            customer_key=key, 
            customer_name=name,  
            total_spent=SUM(orders.total_price)  
        ).WHERE((total_spent > 1000) &amp; (nation.region.name == "ASIA"))
      </Code>
    </Query>
    <Query>
      <Description>Top 5 Most Profitable Nations</Description>
      <Code>
        selected_regions = nations.WHERE(
          HAS(customers.orders) == 1
        ).CALCULATE(  
            region_name=name,  
            Total_revenue=SUM(customers.orders.total_price)  
        ).TOP_K(5, Total_revenue.DESC())
      </Code>
    </Query>
    <Query>
      <Description>Inactive Customers</Description>
      <Code>
        customers_without_orders = customers.WHERE(HASNOT(orders)==1).CALCULATE(  
            customer_key=key,  
            customer_name=name  
        )
      </Code>
    </Query>
    <Query>
      <Description>Customer Activity by Nation</Description>
      <Code>
        cust_info = customers.CALCULATE(is_active=HAS(orders)==1)  
        nation_summary = nations.CALCULATE(  
            nation_name=name,  
            total_customers=COUNT(cust_info),  
            active_customers=SUM(cust_info.is_active),  
            inactive_customers=COUNT(cust_info) - SUM(cust_info.is_active)  
        ).ORDER_BY(total_customers.DESC())
      </Code>
    </Query>
    <Query>
      <Description>High Balance, Low Spending Customers</Description>
      <Code>
        customers_in_low_percentiles = customers.WHERE(  
            (PERCENTILE(by=acctbal.DESC()) &lt;= 10) &amp;  
            (PERCENTILE(by=COUNT(orders.key).ASC()) &lt;= 25)  
        )
      </Code>
    </Query>
    <Query>
      <Description>For every part of the market segment find the total quantity sold</Description>
      <Code>
        # Step 1: Filter lines for 1998 and gather necessary info (segment, part name)
        # Navigate from lines -> order -> customer -> mktsegment and lines -> part -> name
        lines_1998_info = lines.WHERE(YEAR(order.order_date) == 1998).CALCULATE(
            mktsegment = order.customer.mktsegment,
            part_name = part.name
        )

        # Step 2: Group by market segment and part name, summing the quantity
        # PARTITION the filtered lines info by segment and part name
        part_totals_per_segment = lines_1998_info.PARTITION(
            name="part_segment_groups", by=(mktsegment, part_name)
        ).CALCULATE(
            mktsegment = mktsegment,
            part_name = part_name,
            # SUM the quantity from the original collection context within the PARTITION group
            total_quantity = SUM(lines.quantity)
        )
      </Code>
    </Query>

    <Query>
      <Description>Identify the states whose current occupants account for at least 1% of all packages purchased</Description>
      <Code>
        GRAPH.CALCULATE(
            total_packages=COUNT(Packages)
        ).Addresses.WHERE(
          HAS(current_occupants.package) == 1
        ).PARTITION(name="states", by=state).CALCULATE(
            state,
            pct_of_packages=100.0 * COUNT(Addresses.current_occupants.package) / total_packages
        ).WHERE(pct_of_packages >= 1.0)
      </Code>
    </Query>

    <Query>
      <Description>Find the 10 most frequent combinations of the state that the person lives in and the first letter of that person's name</Description>
      <Code>
        people_info = Addresses.WHERE(
          HAS(current_occupants) == 1
        ).CALCULATE(state).current_occupants.CALCULATE(
            first_letter=first_name[:1],
        )
        people_info.PARTITION(name="combinations", by=(state, first_letter)).CALCULATE(
            state,
            first_letter,
            n_people=COUNT(current_occupants),
        ).TOP_K(10, by=n_people.DESC())
      </Code>
    </Query>
  </ExampleQueries>

  <GeneralNotes>
    <Note>Use &amp;, |, ~ for logical operations (not and, or, not).</Note>
    <Note>For chained inequalities, use MONOTONIC or explicit comparisons.</Note>
    <Note>Aggregation functions convert plural values (e.g., collections) to singular values.</Note>
  </GeneralNotes>
</PyDoughCheatSheet>