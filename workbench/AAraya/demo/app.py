import streamlit as st
from llm import LLMClient

# Set page config for wide layout
st.set_page_config(page_title="PyDough LLM Demo", layout="wide", page_icon="bodo_icon.png")

# Add custom CSS to style the dropdown
st.markdown("""
<style>
    /* Make the dropdown more compact */
    div.stSelectbox {
        max-width: 300px;  /* Adjust width as needed */
        margin-left: 40px; /* Indent to align with chat message */
    }
    
    /* Hide the label completely */
    div.stSelectbox > label {
        display: none !important;
    }
    
    /* Optional: Style the chat container */
    .stChatMessage {
        padding-bottom: 5px !important;  /* Reduce spacing */
    }
</style>
""", unsafe_allow_html=True)

# ---------------------- PAGE HEADER ----------------------
st.image("logo.png", width=150, use_container_width=False)
st.title("PyDough LLM Demo")

st.markdown(
    """
    This interactive demo allows you to generate **PyDough queries** from natural language instructions.  
    Simply enter a query for the **TPCH database**, run it, and explore the results.
    """,
    unsafe_allow_html=True,
)

#View TPCH diagram
@st.dialog("📊 TPCH Database Diagram", width="large")
def show_db_diagram():
    st.image("db_diag.png", use_container_width=True)

if st.button("View TPCH Diagram 📊"):
    show_db_diagram()


st.markdown(
    """
    ### How It Works:
    - Type a query in the chat panel.    
    - Select an option from the result dropdown to view specific details on the Output panel.  
    - Refine the query by adding more details on the Input panel to get a more specific response.  
    - **Each conversation is based on a single query and its refinements.** 
        To start a completely new query, click **"Restart"**.  
    """,
    unsafe_allow_html=True,
)
# ---------------------- EXAMPLES MODAL ----------------------
@st.dialog("💡 Example Queries for TPCH", width="large") 
def show_examples():
    st.write("You can **copy** any of the examples by clicking the copy button. Then paste it into the query box!")

    examples = [
        "Total customers & suppliers per nation, ordered by nation name.",
        "Top 5 nations with most customer orders in 1995.",
        "Region with highest total order value in 1996.\n\nSUM(extended_price * (1 - discount))",
        "Top 3 regions with most distinct customers.",
        "Customers & order count in 1995 (Europe) with balance > $700.",
        "Top 10 customers who bought 'green' products in 1998 (with quantity & address).",
        "Customers with more orders in 1995 than 1994.",
        "Avg. order value per nation.\n\nSUM(extended_price * quantity)",
        "Total revenue per customer in 1994.\n\nSUM(extended_price * (1 - discount))",
        "Customer key, name & revenue in 1994.\n\nSUM(extended_price * (1 - discount))",
        "Customers ending in zero with 30-lowest balances.",
        "Customers with >10 orders, showing name & total order count.",
        "Orders from 1998 with total price > $100, sorted by price.",
        "Customers who ordered in 1996 but not in 1997, with email & total spent (> $200)."
    ]

    for example in examples:
        st.code(example, language="")

col1, col2 = st.columns([0.85, 2.80])  
with col1:
    st.markdown('<p style="margin-top:10px;">Don\'t know what to write? Check out our</p>', unsafe_allow_html=True)
with col2: 
    if st.button("Examples"):
        show_examples()

# ---------------------- LAYOUT: TWO-PANE VIEW ----------------------
col1, col2 = st.columns([0.5, 0.5])  # Left = Query Panel, Right = Output Panel

with col1:
    st.header("Input")

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_output" not in st.session_state:
        st.session_state.selected_output = {}
    if "query_results" not in st.session_state:
        st.session_state.query_results = {}
    if "active_query" not in st.session_state:
        st.session_state.active_query = None
    if "last_query_id" not in st.session_state:
        st.session_state.last_query_id = None

    # Function to handle dropdown changes
    def on_dropdown_change(query_id):
        st.session_state.active_query = query_id

    # Display chat history in left panel
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

        # If it's an assistant response, include the dropdown
        if message["role"] == "assistant" and "query_id" in message:
            query_id = message["query_id"]
            result = st.session_state.query_results[query_id]

            dropdown_key = f"dropdown_{query_id}"
            selected_output = st.session_state.selected_output.get(dropdown_key, "Code")

            # Dropdown without label
            selected_output = st.selectbox(
                " ", 
                ["Code", "Full Explanation", "DataFrame", "SQL", "Exception", 
                "Original Question", "Base Prompt", "Cheat Sheet", "Knowledge Graph"],
                key=dropdown_key,
                index=["Code", "Full Explanation", "DataFrame", "SQL", "Exception",
                    "Original Question", "Base Prompt", "Cheat Sheet", "Knowledge Graph"].index(selected_output),
                on_change=on_dropdown_change,
                args=(query_id,)
            )

            # Store selection in session state
            st.session_state.selected_output[dropdown_key] = selected_output
            
            # Update active query when dropdown changes
            if st.session_state.get('widget_triggered') == dropdown_key:
                st.session_state.active_query = query_id

    # ---------------------- USER INPUT ----------------------
    if query := st.chat_input("Ask a query about the TPCH database..."):
        st.session_state.messages.append({"role": "user", "content": query})

        query_id = len(st.session_state.messages)  # Unique ID per query
        client = LLMClient()

        try:
            # Determine if this is a follow-up query
            if st.session_state.last_query_id is not None and len(st.session_state.messages) > 2:
                # Get the last result for discourse
                last_result = st.session_state.query_results[st.session_state.last_query_id]
                # This is a follow-up query, use discourse
                result = client.discourse(last_result, query)
            else:
                # This is a new query, use ask
                result = client.ask(query)

            # Check if result is empty
            if not result or (not result.code and not result.full_explanation and not result.df):
                st.error("⚠️ No valid response received. Please try again.")
            else:
                # Store response and result
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "Your answer is ready! Select the result format below:",
                    "query_id": query_id
                })

                st.session_state.query_results[query_id] = result
                st.session_state.selected_output[f"dropdown_{query_id}"] = "Code"
                st.session_state.active_query = query_id
                st.session_state.last_query_id = query_id  # Update the last query ID

                # Refresh to update display pane
                st.rerun()

        except Exception as e:
            st.error(f"❌ Error running query: {e}")

    # Reset button
    if st.button("Restart"):
        st.session_state.messages = []
        st.session_state.selected_output = {}
        st.session_state.query_results = {}
        st.session_state.active_query = None
        st.session_state.last_query_id = None  # Reset last query ID
        st.rerun()

# ---------------------- RIGHT PANE: DISPLAY OUTPUT ----------------------
with col2:
    st.header("Output")

    # Use active_query instead of last_selected_query
    if "active_query" in st.session_state and st.session_state.active_query is not None:
        query_id = st.session_state.active_query
        result = st.session_state.query_results[query_id]
        selected_output = st.session_state.selected_output.get(f"dropdown_{query_id}", "Code")

        st.markdown("---")

        # Display selected output
        if selected_output == "Code":
            st.code(result.code, language="python")
        elif selected_output == "Full Explanation":
            st.write(result.full_explanation)
        elif selected_output == "DataFrame":
            if hasattr(result, "df") and result.df is not None:
                st.dataframe(result.df)  
            else:
                st.warning("⚠️ No DataFrame available.")
        elif selected_output == "SQL":
            st.code(result.sql, language="sql") if hasattr(result, "sql") else st.write("No SQL available.")
        elif selected_output == "Exception":
            st.write(result.exception or "No exception found.")
        elif selected_output == "Original Question":
            st.write(result.original_question or "No original question found.")
        elif selected_output == "Base Prompt":
            st.write(result.base_prompt or "No base prompt found.")
        elif selected_output == "Cheat Sheet":
            st.write(result.cheat_sheet or "No cheat sheet found.")
        elif selected_output == "Knowledge Graph":
            st.write(result.knowledge_graph or "No knowledge graph found.")
    else:
        st.info("Run a query to see results here.")