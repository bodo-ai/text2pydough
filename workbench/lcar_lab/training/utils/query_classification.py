import pandas as pd
import argparse
import re
import sqlglot

# sqlglot expressions to check for query complexity 
from sqlglot.expressions import (
    Subquery,
    Join,
    Window,
    Union,
    Except,
    Intersect,
    With,
    Select,
)

# Hardness classification via raw SQL heuristics

def count_component1(sql):
    c = 0
    if re.search(r"\bwhere\b", sql, re.IGNORECASE): c += 1
    if re.search(r"\bgroup\s+by\b", sql, re.IGNORECASE): c += 1
    if re.search(r"\border\s+by\b", sql, re.IGNORECASE): c += 1
    if re.search(r"\blimit\b", sql, re.IGNORECASE): c += 1
    joins = len(re.findall(r"\bjoin\b", sql, re.IGNORECASE))
    c += max(0, joins)
    # ORs and LIKEs
    c += len(re.findall(r"\bor\b", sql, re.IGNORECASE))
    c += len(re.findall(r"\blike\b", sql, re.IGNORECASE))
    return c

def count_component2(sql):
    # nested SELECTs
    return len(re.findall(r"\(\s*select\b", sql, re.IGNORECASE))

def count_others(sql):
    c = 0
    # aggregation functions
    agg_count = len(re.findall(r"\b(count|sum|avg|min|max)\s*\(", sql, re.IGNORECASE))
    if agg_count > 1: c += 1
    # multi-select
    sel = re.search(r"\bselect\b(.*?)\bfrom\b", sql, re.IGNORECASE | re.DOTALL)
    if sel and sel.group(1).count(',') > 0: c += 1
    # multiple where conditions
    where = re.search(r"\bwhere\b(.*?)(?:\bgroup\b|\border\b|\blimit\b|$)", sql, re.IGNORECASE | re.DOTALL)
    if where and len(re.findall(r"\b(and|or)\b", where.group(1), re.IGNORECASE)) > 1:
        c += 1
    # multiple group by columns
    gb = re.search(r"\bgroup\s+by\b(.*?)(?:\border\b|\blimit\b|$)", sql, re.IGNORECASE | re.DOTALL)
    if gb and gb.group(1).count(',') > 1:
        c += 1
    return c

def eval_hardness(sql):
    c1 = count_component1(sql)
    c2 = count_component2(sql)
    co = count_others(sql)
    if c1 <= 1 and co == 0 and c2 == 0:
        return 'easy'
    elif (co <= 2 and c1 <= 1 and c2 == 0) or (c1 <= 2 and co < 2 and c2 == 0):
        return 'medium'
    elif (co > 2 and c1 <= 2 and c2 == 0) or (2 < c1 <= 3 and co <= 2 and c2 == 0) or (c1 <= 1 and co == 0 and c2 <= 1):
        return 'hard'
    else:
        return 'extra'
    
def eval_complexity(sql: str, dialect="sqlite"):
    """
    Roughly replicates Gretel's buckets.
    Returns one of:
      basic SQL | aggregation | single join | multiple_joins |
      subqueries | window functions | set operations | CTEs | unknown
    """
    try:
        tree = sqlglot.parse_one(sql, read=dialect)
    except sqlglot.errors.ParseError:
        return "unknown"

    # 1. CTEs (WITH ...)
    if tree.find(With):
        return "CTEs"

    # 2. Set operations (UNION / INTERSECT / EXCEPT)
    if tree.find(Union) or tree.find(Except) or tree.find(Intersect):
        return "set operations"

    # 3. Window functions
    if tree.find(Window):
        return "window functions"

    # 4. Joins
    joins = list(tree.find_all(Join))
    if joins:
        return "multiple_joins" if len(joins) > 1 else "single join"

    # 5. Subqueries (SELECT inside another SELECT / WHERE / FROM …)
    if tree.find(Subquery):
        return "subqueries"

    # 6. Aggregations (COUNT, SUM … or GROUP BY / HAVING)
    agg_funcs = {"COUNT", "SUM", "AVG", "MIN", "MAX"}
    # Anonymous covers functions like COUNT(...)
    if any(f.name.upper() in agg_funcs for f in tree.find_all(sqlglot.expressions.Anonymous)):
        return "aggregation"
    if tree.args.get("group") or tree.args.get("having"):
        return "aggregation"

    # 7. Basic SQL (simple SELECT with none of the above)
    if isinstance(tree, Select):
        return "basic SQL"

    # 8. Fallback
    return "unknown"



def annotate_difficulty(input_csv: str, output_csv: str):
    df = pd.read_csv(input_csv)
    df['difficulty'] = df['ground_truth_sql'].apply(lambda s: eval_hardness(s))
    df['complexity'] = df['ground_truth_sql'].apply(lambda s: eval_complexity(s))
    df.to_csv(output_csv, index=False)
    print(f"Annotated CSV saved to {output_csv}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv')
    parser.add_argument('output_csv')
    args = parser.parse_args()
    annotate_difficulty(args.input_csv, args.output_csv)



