import streamlit as st


st.title("Pydough LLM Demo")

st.markdown(
    """
    This notebook showcases how an LLM can generate PyDough queries from natural language instructions. 
    The goal is to demonstrate how AI can automate complex data analysis, making querying faster, 
    more intuitive, and accessible without needing deep technical expertise.

    Each example highlights different capabilities, including aggregations, filtering, ranking, 
    and calculations across multiple collections.
    """
)

st.header("Setup")
st.markdown("First, we import the created client.")
st.code("from llm import LLMClient", language="python")


if "client" not in st.session_state:
    try:
        from llm import LLMClient
        st.session_state.client = LLMClient()  # Load the client
        st.success("LLMClient initialized successfully! ✅")
    except Exception as e:
        st.error(f"Error initializing LLMClient: {e}")

st.markdown("Then we initialize the client.")
st.code("client = LLMClient()", language="python")


st.header("Example")
st.markdown("First, we give the client the query we need PyDough code for.")


query = st.text_input("Enter your natural language query:", "Give me all the suppliers' names from United States")


if st.button("Run Query"):
    if "client" in st.session_state:
        try:
            
            result = st.session_state.client.ask(query)
            
            
            st.session_state.result = result

            st.success("Query executed successfully! ✅")
        except Exception as e:
            st.error(f"Error running query: {e}")


if "result" in st.session_state:
    result = st.session_state.result

    
    st.markdown("### After that, we can consult all the necessary attributes from the result.")

    
    st.markdown("#### At first, I want the PyDough code with a full explanation.")
    st.code("print(result.full_explanation)", language="python")
    st.markdown("##### Output:")
    st.write(result.full_explanation)

    
    st.markdown("#### We can also ask for the pydough code without the explanation.")
    st.code("print(result.code)", language="python")
    st.markdown("##### Output:")
    st.code(result.code, language="python")

    
    if hasattr(result, "df"):
        st.markdown("#### And if we want to visually check, analyze or edit the resulting dataframe we also can.")
        st.code("result.df.head()", language="python")
        st.markdown("##### Output:")
        st.dataframe(result.df.head())
        
        
        st.markdown("#### Exceptions")
        
        
        st.markdown(
        """
        If one calls the dataframe and gets an error, no response, or an empty dataframe, 
        it is possible that there is a PyDough exception.  
        We can check this by running:
        """
        )


    st.code("print(result.exception)", language="python")


    st.markdown(
        """
        You can try to fix the error using the `correct` method.  
        We are going to declare a new variable to obtain the corrected result.
        """
    )


    st.code("corrected_result = client.correct(result)", language="python")


    st.markdown(
        """
        To see how the model tries to solve the issue, you can print the full explanation of the `corrected_result`.
        """
    )


    st.code("print(corrected_result.full_explanation)", language="python")
    
    st.markdown("You can try this as many times as you like if an exception keeps ocurring. ")
    

# Section: Test Cases
st.header("Test Cases")

# Subsection: Customer Segmentation
st.subheader("Customer Segmentation.")

# Test Case Title
st.markdown("### 1. Find the names of all customers and the number of orders placed in 1995 in Europe.")

# Description
st.markdown(
    """
    Demonstrates simple filtering, counting, and sorting while being business-relevant for regional market analysis. 
    Adds a second filtering layer by including account balance and order activity, making it more dynamic.
    """
)

# Show the query variable
st.code(
    '''query1 = "Find the names of all customers and the number of orders placed in 1995 in Europe."''',
    language="python"
)

# User input query field (pre-filled)
query1 = st.text_area(
    "Query to execute:", 
    "Find the names of all customers and the number of orders placed in 1995 in Europe."
)

# Button to execute the query
if st.button("Run Query 1"):
    if "client" in st.session_state:
        try:
            # Call the LLM client to generate the PyDough query
            result1 = st.session_state.client.ask(query1)
            
            # Store the result in session state
            st.session_state.result1 = result1

            st.success("Query executed successfully! ✅")
        except Exception as e:
            st.error(f"Error running query: {e}")

# If a result exists, automatically display attributes like in Jupyter
if "result1" in st.session_state:
    result1 = st.session_state.result1

    # Show the full explanation
    st.code("print(result1.full_explanation)", language="python")
    st.write(result1.full_explanation)

    # Display the first rows of the dataframe
    st.code("result1.df.head()", language="python")
    if hasattr(result1, "df"):
        st.dataframe(result1.df.head())

# Follow-up Question
st.markdown(
    """
    **Follow up:** Now, give me the ones who have an account balance greater than $700 and placed 
    at least one order in that same year. Sorted in descending order by the number of orders.
    """
)

        
        
