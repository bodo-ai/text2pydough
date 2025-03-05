import streamlit as st

# Title
st.title("Pydough LLM Demo")

# Description
st.markdown(
    """
    This notebook showcases how an LLM can generate PyDough queries from natural language instructions. 
    The goal is to demonstrate how AI can automate complex data analysis, making querying faster, 
    more intuitive, and accessible without needing deep technical expertise.

    Each example highlights different capabilities, including aggregations, filtering, ranking, 
    and calculations across multiple collections.
    """
)

# Section: Setup
st.header("Setup")
st.markdown("First, we import the created client.")
st.code("from llm import LLMClient", language="python")

# Ensure the client is initialized only once
if "client" not in st.session_state:
    try:
        from llm import LLMClient
        st.session_state.client = LLMClient()  # Load the client
        st.success("LLMClient initialized successfully! ✅")
    except Exception as e:
        st.error(f"Error initializing LLMClient: {e}")

st.markdown("Then we initialize the client.")
st.code("client = LLMClient()", language="python")

# Section: Example
st.header("Example")
st.markdown("First, we give the client the query we need PyDough code for.")

# User input for the query
query = st.text_input("Enter your natural language query:", "Give me all the suppliers' names from United States")

# Button to execute the query
if st.button("Run Query"):
    if "client" in st.session_state:
        try:
            # Call the LLM client to generate the PyDough query
            result = st.session_state.client.ask(query)
            
            # Store the result in session state
            st.session_state.result = result

            st.success("Query executed successfully! ✅")
        except Exception as e:
            st.error(f"Error running query: {e}")

# If a result exists, automatically display attributes like in Jupyter
if "result" in st.session_state:
    result = st.session_state.result

    # Section: Accessing the Result Attributes
    st.markdown("### After that, we can consult all the necessary attributes from the result.")

    # Show the PyDough code with explanation
    st.markdown("### At first, I want the PyDough code with a full explanation.")
    st.code("print(result.full_explanation)", language="python")
    st.markdown("#### Output:")
    st.write(result.full_explanation)

    # Display the generated PyDough code
    st.markdown("### PyDough Code")
    st.code(result.code, language="python")

    # Display the raw query result dataframe
    if hasattr(result, "df"):
        st.markdown("### Query Results")
        st.dataframe(result.df.head())
