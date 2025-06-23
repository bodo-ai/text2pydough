(* 
 PyDough EBNF Grammar 

 This EBNF grammar defines the structure and syntax of the PyDough DSL,
 including expressions, collections, functions, operators, and statements.
 It is designed to be clear, concise, and maintainable.
*)

#################################
###        Core Grammar       ###
#################################

Expression    = Collection | FunctionCall | BinaryOp | UnaryOp | Literal ;
Collection    = identifier | SubCollection ;
SubCollection = Collection "." identifier ;
FunctionCall  = Function "(" Expression { "," Expression } ")" ;
BinaryOp      = Expression ArithmeticOperator Expression |
                BooleanExpression LogicalOperator BooleanExpression ;
UnaryOp       = UnaryArithmeticOperator Expression |
                UnaryBooleanOperator BooleanExpression ;
Assignment    = identifier "=" Expression ;
Literal       = number | string | BooleanLiteral ;


#################################
###        Operators          ###
#################################

operator = ArithmeticOperator | ComparisonOperator | LogicalOperator |
           UnaryArithmeticOperator | UnaryBooleanOperator ;

ArithmeticOperator      = "+" | "-" | "*" | "/" ;
UnaryArithmeticOperator = "+" | "-" ;
ComparisonOperator      = "<" | "<=" | "==" | "!=" | ">" | ">=" ;
LogicalOperator         = "&" | "|" ;
UnaryBooleanOperator    = "~" ;

identifier = letter { letter | digit | "_" } ;
integer    = digit { digit } ;
number     = { UnaryArithmeticOperator } integer [ "." digit { digit } ] [ exponent ] ;
string     = "\"" { character } "\"" ;
BooleanLiteral = "True" | "False" ;
exponent = ("E" | "e") [ "+" | "-" ] integer ;


#################################
###   Boolean Expressions     ###
#################################

BooleanExpression   = BooleanTerm { LogicalOperator BooleanTerm } ;
BooleanTerm         = BooleanFactor | ComparisonExpression ;
ComparisonExpression = Expression ComparisonOperator Expression ;
BooleanFactor       = BooleanLiteral
                    | UnaryBooleanOperator BooleanFactor
                    | "(" BooleanExpression ")"
                    | FunctionCall ;    (* For functions returning boolean values *)


#################################
###    String Expressions     ###
#################################

StringExpression  = string | identifier | SubCollection | StringFunction | StringSlice ;
StringSlice       = StringExpression "[" [ integer ] ":" [ integer ] "]" ;
LikePattern       = string ; (* Must be a valid LIKE pattern using % and _ *)

#################################
###  Aggregation Functions    ###
#################################

(* SUMFunction: Returns the sum of the set of numerical values. *)
SUMFunction       = "SUM" "(" Expression ")" ;

(* AVGFunction: Returns the average of the set of numerical values. *)
AVGFunction       = "AVG" "(" Expression ")" ;

(* MEDIANFunction: Returns the median value from the set, ignoring absent records. *)
MEDIANFunction    = "MEDIAN" "(" Expression ")" ;

(* MINFunction: Returns the smallest value from the set of values. *)
MINFunction       = "MIN" "(" Expression ")" ;

(* MAXFunction: Returns the largest value from the set of values. *)
MAXFunction       = "MAX" "(" Expression ")" ;

(* ANYTHINGFunction: Returns an arbitrary value from the set of values. *)
ANYTHINGFunction  = "ANYTHING" "(" Expression ")" ;

(* COUNTFunction: Returns the number of non-null records in the set of values. *)
COUNTFunction     = "COUNT" "(" Expression ")" ;

(* NDISTINCTFunction: Returns the count of distinct values in the set. *)
NDISTINCTFunction = "NDISTINCT" "(" Expression ")" ;

(* HASFunction: Returns True if the sub-collection has at least one record. *)
HASFunction       = "HAS" "(" Expression ")" ;

(* HASNOTFunction: Returns True if the sub-collection has no records. *)
HASNOTFunction    = "HASNOT" "(" Expression ")" ;

(* VARFunction: Returns the variance of the set of numerical values.
   Optional 'type' argument specifies 'population' (default) or 'sample'. *)
VARFunction       = "VAR" "(" Expression [ "," VarTypeArg ] ")" ;
VarTypeArg        = "type" "=" string ;

(* STDFunction: Returns the standard deviation.
   Optional 'type' argument specifies 'population' (default) or 'sample'. *)
STDFunction       = "STD" "(" Expression [ "," StdTypeArg ] ")" ;
StdTypeArg        = "type" "=" string ;

AggregationFunction = SUMFunction  | AVGFunction | MEDIANFunction 
                      | MINFunction | MAXFunction | ANYTHINGFunction 
                      | COUNTFunction  | NDISTINCTFunction 
                      | HASFunction | HASNOTFunction 
                      | VARFunction | STDFunction ;

#################################
###     Window Functions      ###
#################################

(* ByArg: Specifies ordering using one or more expressions. *)
ByArg         = "by" "=" OrderExpression ;
(* PerArg: Specifies a collection for partitioning. *)
PerArg        = "per" "=" Collection ;
(* AllowTiesArg: Indicates whether tied values should be allowed in ranking. *)
AllowTiesArg  = "allow_ties" "=" BooleanLiteral ;
(* DenseArg: Indicates whether ranking should be dense. *)
DenseArg      = "dense" "=" BooleanLiteral ;
(* NBucketsArg: Specifies the number of buckets as an integer. *)
NBucketsArg   = "n_buckets" "=" integer ;
(* NArg: Specifies the number of records to shift (for PREV/NEXT functions). *)
NArg          = "n" "=" integer ;
(* DefaultArg: Specifies a default value for PREV/NEXT functions when no record exists. *)
DefaultArg    = "default" "=" Literal ;
(* CumulativeArg: Indicates a cumulative aggregation in window functions. *)
CumulativeArg = "cumulative" "=" BooleanLiteral ;
(* FrameArg: Specifies a sliding window frame as a tuple of limits. *)
FrameArg      = "frame" "=" "(" FrameLimits ")" ;
(* FrameLimits: A tuple of frame limit values. *)
FrameLimits   = FrameLimit "," FrameLimit ;
(* FrameLimit: A frame limit can be an integer or "None". *)
FrameLimit    = integer | "None" ;


(* RANKINGFunction: Returns the ordinal position of the current record in a sorted context. *)
RANKINGFunction = "RANKING" "(" RANKINGArgs ")" ;
(* RANKINGArgs: Contains a required 'by' argument for ordering
   and optional 'per', 'allow_ties', and 'dense' arguments. *)
RANKINGArgs = ByArg 
              [ "," PerArg ]
              [ "," AllowTiesArg ]
              [ "," DenseArg ] ;

(* PERCENTILEFunction: Returns the bucket index of the current record when records are split into buckets. *)
PERCENTILEFunction = "PERCENTILE" "(" PERCENTILEArgs ")" ;
(* PERCENTILEArgs: Contains a required 'by' argument,
   and optional 'per' and 'n_buckets' arguments. *)
PERCENTILEArgs   = ByArg 
                   [ "," PerArg ] 
                   [ "," NBucketsArg ] ;

(* PREVFunction: Returns the value of an expression from a preceding record in the collection. *)
PREVFunction = "PREV" "(" PREVArgs ")" ;
(* PREVArgs: Requires an expression; optionally 'n' for the number of records to look back,
   'default' for a fallback value, and optional 'by' and 'per' for ordering and partitioning. *)
PREVArgs = Expression 
           [ "," NArg ]
           [ "," DefaultArg ]
           [ "," ByArg ]
           [ "," PerArg ] ;

(* NEXTFunction: Returns the value of an expression from a following record.
   (Conceptually equivalent to PREV with a negative 'n'.) *)
NEXTFunction = "NEXT" "(" NEXTArgs ")" ;
(* NEXTArgs: Similar to PREVArgs; accepts 'n', 'default', 'by', and 'per' for forward lookup. *)
NEXTArgs     = Expression 
               [ "," NArg ]
               [ "," DefaultArg ]
               [ "," ByArg ]
               [ "," PerArg ] ;

(* RELSUMFunction: Returns the sum of values from multiple records within the current context. *)
RELSUMFunction = "RELSUM" "(" RELSUMArgs ")" ;
(* RELSUMArgs: Contains a required expression plus optional named arguments for partitioning ('per'),
   ordering ('by'), cumulative sum ('cumulative'), or framing ('frame'). *)
RELSUMArgs     = Expression { "," RELSUMNamedArg } ;
RELSUMNamedArg = PerArg 
                | ByArg 
                | CumulativeArg 
                | FrameArg ;

(* RELAVGFunction: Returns the average of values from multiple records in the current context. *)
RELAVGFunction = "RELAVG" "(" RELAVGArgs ")" ;
(* RELAVGArgs: Contains a required expression plus optional named arguments analogous to RELSUMArgs. *)
RELAVGArgs = Expression { "," RELAVGNamedArg } ;
RELAVGNamedArg = PerArg 
                | ByArg 
                | CumulativeArg 
                | FrameArg ;

(* RELCOUNTFunction: Returns the count of non-null values from multiple records. *)
RELCOUNTFunction = "RELCOUNT" "(" RELCOUNTArgs ")" ;
(* RELCOUNTArgs: Contains a required expression plus optional named arguments for partitioning, ordering,
   cumulative count, or framing. *)
RELCOUNTArgs = Expression { "," RELCOUNTNamedArg } ;
RELCOUNTNamedArg = PerArg 
                  | ByArg 
                  | CumulativeArg 
                  | FrameArg ;

(* RELSIZEFunction: Returns the total number of records in the current context. *)
RELSIZEFunction = "RELSIZE" "(" RELSIZEArgs ")" ;
(* RELSIZEArgs: Optionally includes named arguments for partitioning, ordering, cumulative count, or framing. *)
RELSIZEArgs = [ RELSIZENamedArg { "," RELSIZENamedArg } ] ;
RELSIZENamedArg = PerArg 
                  | ByArg 
                  | CumulativeArg 
                  | FrameArg ;

WindowFunction = RANKINGFunction
               | PERCENTILEFunction
               | PREVFunction
               | NEXTFunction
               | RELSUMFunction
               | RELAVGFunction
               | RELCOUNTFunction
               | RELSIZEFunction ;


#################################
###    Numerical Functions    ###
#################################

(* ABSFunction: Returns the absolute value of the given expression. *)
ABSFunction      = "ABS" "(" Expression ")" ;

(* ROUNDFunction: Rounds the first argument to the precision specified by the second argument.
   Note: Precision must be explicitly provided. *)
ROUNDFunction    = "ROUND" "(" Expression "," Expression ")" ;

(* POWERFunction: Raises the first expression to the power of the second expression. *)
POWERFunction    = "POWER" "(" Expression "," Expression ")" ;

(* SQRTFunction: Returns the square root of the given expression (equivalent to POWER(x, 0.5)). *)
SQRTFunction     = "SQRT" "(" Expression ")" ;

(* SIGNFunction: Returns the sign of the given expression:
   1 for positive, -1 for negative, 0 for zero. *)
SIGNFunction     = "SIGN" "(" Expression ")" ;

(* SMALLESTFunction: Returns the smallest value among the given values.
   Requires at least two arguments; returns NULL if any argument is NULL. *)
SMALLESTFunction = "SMALLEST" "(" Expression "," Expression { "," Expression } ")" ;

(* LARGESTFunction: Returns the largest value among the given values.
   Requires at least two arguments; returns NULL if any argument is NULL. *)
LARGESTFunction  = "LARGEST" "(" Expression "," Expression { "," Expression } ")" ;

NumericalFunction = ABSFunction | ROUNDFunction | POWERFunction | SQRTFunction |
                   SIGNFunction | SMALLESTFunction | LARGESTFunction ;

### **Datetime Functions**
(* DATETIMEFunction: Converts the input expression into a datetime value. *)
DATETIMEFunction   = "DATETIME" "(" DateExpression | DateString ")" ;
DateExpression    = Expression ; (* Must be a valid date-related expression *)
DateString        = string ; (* Must be a valid datetime string or "now" *)

(* DATEDIFFFunction: Returns the difference between two datetime values based on the specified units.
   The first parameter is a string literal indicating the units (e.g., "years", "months", "days", "hours", etc.),
   followed by the start date and the end date expressions. *)
DATEDIFFFunction   = "DATEDIFF" "(" Interval "," DateExpression "," DateExpression ")" ;
Interval          = "days" | "months" | "years" | "hours" | "minutes" | "seconds" | "quarters" | "weeks" ;

(* YEARFunction: Returns the year component from a datetime value. *)
YEARFunction       = "YEAR" "(" DateExpression ")" ;
(* MONTHFunction: Returns the month component from a datetime value. *)
MONTHFunction      = "MONTH" "(" DateExpression ")" ;
(* DAYFunction: Returns the day component from a datetime value. *)
DAYFunction        = "DAY" "(" DateExpression ")" ;
(* QUARTERFunction: Returns the quarter (1-4) from a datetime value. *)
QUARTERFunction    = "QUARTER" "(" DateExpression ")" ;
(* HOURFunction: Returns the hour component from a datetime values. *)
HOURFunction       = "HOUR" "(" DateExpression ")" ;
(* MINUTEFunction: Returns the minute component from a datetime value. *)
MINUTEFunction     = "MINUTE" "(" DateExpression ")" ;
(* SECONDFunction: Returns the second component from a datetime value. *)
SECONDFunction     = "SECOND" "(" DateExpression ")" ;
(* DAYOFWEEKFunction: Returns the day of the week as an integer for a datetime value. *)
DAYOFWEEKFunction  = "DAYOFWEEK" "(" DateExpression ")" ;
(* DAYNAMEFunction: Returns the name of the day (e.g., "Monday") for a datetime value. *)
DAYNAMEFunction    = "DAYNAME" "(" DateExpression ")" ;

DatetimeFunction = DATETIMEFunction | DATEDIFFFunction | YEARFunction | MONTHFunction |
                  DAYFunction | QUARTERFunction | HOURFunction | MINUTEFunction |
                  SECONDFunction | DAYOFWEEKFunction | DAYNAMEFunction ;

### **String Functions**
(* LOWERFunction: Converts the input string to lowercase. *)
LOWERFunction        = "LOWER" "(" StringExpression ")" ;
(* UPPERFunction: Converts the input string to uppercase. *)
UPPERFunction        = "UPPER" "(" StringExpression ")" ;
(* LENGTHFunction: Returns the number of characters in the input string. *)
LENGTHFunction       = "LENGTH" "(" StringExpression ")" ;
(* STARTSWITHFunction: Returns True if the input string starts with the specified prefix.
   Requires two arguments: the input string and the prefix. *)
STARTSWITHFunction   = "STARTSWITH" "(" StringExpression "," StringExpression ")" ;
(* ENDSWITHFunction: Returns True if the input string ends with the specified suffix.
   Requires two arguments: the input string and the suffix. *)
ENDSWITHFunction     = "ENDSWITH" "(" StringExpression "," StringExpression ")" ;
(* CONTAINSFunction: Returns True if the input string contains the specified substring.
   Requires two arguments: the input string and the substring. *)
CONTAINSFunction     = "CONTAINS" "(" StringExpression "," StringExpression ")" ;
(* LIKEFunction: Checks if the input string matches a SQL-like pattern.
   Requires two arguments: the input string and the pattern. *)
LIKEFunction         = "LIKE" "(" StringExpression "," LikePattern ")" ;
(* JOIN_STRINGSFunction: Concatenates multiple string expressions into a single string.
   Typically, the first argument is used as a delimiter. *)
JOIN_STRINGSFunction = "JOIN_STRINGS" "(" StringExpression { "," StringExpression } ")" ;

StringFunction = LOWERFunction | UPPERFunction | LENGTHFunction | STARTSWITHFunction |
                ENDSWITHFunction | CONTAINSFunction | LIKEFunction | JOIN_STRINGSFunction ;

### **Conditional Functions**
(* IFFFunction: Returns the second argument if the first (condition) is true; otherwise, returns the third argument. *)
IFFFunction        = "IFF" "(" BooleanExpression "," Expression "," Expression ")" ;
(* ISINFunction: Returns True if the first argument is found within the set specified by the second argument; otherwise, returns False. *)
ISINFunction       = "ISIN" "(" Expression "," "(" Expression { "," Expression } ")" ")" ;
(* DEFAULT_TOFunction: Returns the first argument when it is present (non-null); otherwise, returns the default value supplied as the second argument. *)
DEFAULT_TOFunction = "DEFAULT_TO" "(" Expression "," Expression ")" ;
(* PRESENTFunction: Returns True if the given expression is present (non-null); otherwise, returns False. *)
PRESENTFunction    = "PRESENT" "(" Expression ")" ;
(* ABSENTFunction: Returns True if the given expression is absent (null); otherwise, returns False. *)
ABSENTFunction     = "ABSENT" "(" Expression ")" ;
(* KEEP_IFFunction: Filters the collection provided as the first argument, returning only those records for which the predicate (second argument) evaluates to True. *)
KEEP_IFFunction    = "KEEP_IF" "(" BooleanExpression ")" ;
(* MONOTONICFunction: Returns True if the sequence of expressions (provided as one or more arguments) is monotonic 
   (i.e. consistently non-decreasing or non-increasing); otherwise, returns False. *)
MONOTONICFunction  = "MONOTONIC" "(" Expression "," Expression { "," Expression }")" ;

ConditionalFunction = IFFFunction | ISINFunction | DEFAULT_TOFunction | PRESENTFunction |
                     ABSENTFunction | KEEP_IFFunction | MONOTONICFunction ;

### **Function Grouping**
Function = AggregationFunction | WindowFunction | NumericalFunction | DatetimeFunction |
          StringFunction | ConditionalFunction ;

### **Order Handling**
OrderExpression = OrderElement | "(" OrderElement { "," OrderElement } ")" ;

OrderElement = OrderableExpression [ "." order ] ;

OrderableExpression = identifier | SubCollection | FunctionCall ;

order = "ASC" | "DESC" ;

### **Collection Operators**
CALCULATEOperator = "CALCULATE" "(" Assignment { "," Assignment } ")" ;
WHEREOperator     = "WHERE" "(" BooleanExpression ")" ;
ORDER_BYOperator  = "ORDER_BY" "(" OrderElement { "," OrderElement } ")" ;
TOP_KOperator     = "TOP_K" "(" integer ")" ;
PARTITIONOperator = "PARTITION" "(" "name" "=" string "," "by" "=" OrderExpression ")" ;
SINGULAROperator  = "SINGULAR" "(" ")" ;
NEXTOperator      = "NEXT" ;
PREVOperator      = "PREV" ;
BESTOperator      = "BEST" "(" BESTParams ")" ;
BESTParams        = "by" "=" OrderExpression 
                    { "," "per" "=" Collection }
                    [ "," ( "allow_ties" "=" BooleanLiteral | "n_best" "=" integer ) ] ;

### **Collection Operator Grouping**
CollectionOperator = CALCULATEOperator | WHEREOperator | ORDER_BYOperator |
                     TOP_KOperator | PARTITIONOperator | SINGULAROperator |
                     NEXTOperator | PREVOperator | BESTOperator ;

### **Statements (Allowing Nested Collection Operators)**
PydoughCode = Statement { Statement } ;

Statement = Collection "." CollectionOperator { "." CollectionOperator } ;


### **Additional Semantic Notes**
(* 
  Semantic Constraints (to be enforced by semantic analyzer):
  1. Function argument types must match expected parameter types
  2. Collection names must be valid and accessible in current scope
  3. Date strings must be valid datetime formats or "now"
  4. LIKE patterns must use valid SQL LIKE syntax with % and _
  5. Slice indices must be valid for the target string/collection
  6. Boolean expressions in WHERE, IFF, KEEP_IF must evaluate to boolean
  7. Numeric expressions in arithmetic operations must be numeric
  8. String operations must operate on string-compatible expressions
*)