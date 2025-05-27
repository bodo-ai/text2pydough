**15. DATETIME FUNCTIONS**

*   YEAR(dt): Extracts year.Example: YEAR(order\_date) == 1995.
    
*   MONTH(dt): Extracts month (1-12).Example: MONTH(order\_date) >= 6.
    
*   DAY(dt): Extracts day (1-31).Example: DAY(order\_date) == 1.
    
*   HOUR(dt): Extracts hour (0-23).Example: HOUR(order\_date) == 12.
    
*   MINUTE(dt): Extracts minute (0-59).Example: MINUTE(order\_date) == 30.
    
*   SECOND(dt): Extracts second (0-59).Example: SECOND(order\_date) < 30.

* DATETIME: The DATETIME function is used to build/augment date/timestamp values. The first argument is the base date/timestamp, and it can optionally take in a variable number of modifier arguments.
  
    - The base argument can be one of the following: A string literal indicating that the current timestamp should be built, which has to be one of the following: `now`, `current_date`, `current_timestamp`, `current date`, `current timestamp`. All of these aliases are equivalent, case-insensitive, and ignore leading/trailing whitespace.
    - A column of datetime data.

  The modifier arguments can be the following (all of the options are case-insensitive and ignore leading/trailing/extra whitespace):

  - A string literal in the format `start of <UNIT>` indicating to truncate the datetime value to a certain unit, which can be the following:
    - Years: Supported aliases are "years", "year", and "y".
    - Months: Supported aliases are "months", "month", and "mm".
    - Days: Supported aliases are "days", "day", and "d".
    - Hours: Supported aliases are "hours", "hour", and "h".
    - Minutes: Supported aliases are "minutes", "minute", and "m".
    - Seconds: Supported aliases are "seconds", "second", and "s".

  - A string literal in the form `±<AMT> <UNIT>` indicating to add/subtract a date/time interval to the datetime value. The sign can be `+` or `-`, and if omitted the default is `+`. The amount must be an integer. The unit must be one of the same unit strings allowed for truncation. For example, "Days", "DAYS", and "d" are all treated the same due to case insensitivity.

  If there are multiple modifiers, they operate left-to-right.
  Usage examples:
  ```python
  # Returns the following datetime moments:
  # 1. The current timestamp
  # 2. The start of the current month
  # 3. Exactly 12 hours from now
  # 4. The last day of the previous year
  # 5. The current day, at midnight
  TPCH.CALCULATE(
    ts_1=DATETIME('now'),
    ts_2=DATETIME('NoW', 'start of month'),
    ts_3=DATETIME(' CURRENT_DATE ', '12 hours'),
    ts_4=DATETIME('Current Timestamp', 'start of y', '- 1 D'),
    ts_5=DATETIME('NOW', '  Start  of  Day  '),
  )

  # For each order, truncates the order date to the first day of the year
  Orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))
  ```

* DATEDIFF: Calling DATEDIFF between 2 timestamps returns the difference in one of the following units of time:     years, months, days, hours, minutes, or seconds.

  - `DATEDIFF("years", x, y)`: Returns the number of full years since `x` that `y` occurred. For example, if `x` is December 31, 2009, and `y` is January 1, 2010, it counts as 1 year apart, even though they are only 1 day apart.
  - `DATEDIFF("months", x, y)`: Returns the number of full months since `x` that `y` occurred. For example, if `x` is January 31, 2014, and `y` is February 1, 2014, it counts as 1 month apart, even though they are only 1 day apart.
  - `DATEDIFF("days", x, y)`: Returns the number of full days since `x` that `y` occurred. For example, if `x` is 11:59 PM on one day, and `y` is 12:01 AM the next day, it counts as 1 day apart, even though they are only 2 minutes apart.
  - `DATEDIFF("hours", x, y)`: Returns the number of full hours since `x` that `y` occurred. For example, if `x` is 6:59 PM and `y` is 7:01 PM on the same day, it counts as 1 hour apart, even though the difference is only 2 minutes.
  - `DATEDIFF("minutes", x, y)`: Returns the number of full minutes since `x` that `y` occurred. For example, if `x` is 7:00 PM and `y` is 7:01 PM, it counts as 1 minute apart, even though the difference is exactly 60 seconds.
  - `DATEDIFF("seconds", x, y)`: Returns the number of full seconds since `x` that `y` occurred. For example, if `x` is at 7:00:01 PM and `y` is at 7:00:02 PM, it counts as 1 second apart.

  - Example:
  ```python
  # Calculates, for each order, the number of days since January 1st 1992
  # that the order was placed:
  Orders.CALCULATE( 
    days_since=DATEDIFF("days", datetime.date(1992, 1, 1), order_date)
  )
  ```