
import pydough
from pydough import init_pydough_context

# Load metadata and connect to database
pydough.active_session.load_metadata_graph("data/Broker_graph.json", "Broker")
pydough.active_session.connect_database("sqlite", database="data/Broker.db")

@init_pydough_context(pydough.active_session.metadata)
def func():
    # Generated PyDough code
    result = Broker.Customers.CALCULATE(name=name, email=email)
    return result

result = func()
print("\nSQL Query:")
print(pydough.to_sql(result))
print("\nResult:")
print(pydough.to_df(result).head(10))  # Show only first 10 rows
