import streamlit as st
from llm import LLMClient

# Set page config for wide layout
st.set_page_config(page_title="PyDough LLM Demo", layout="wide")

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

# ---------------------- TPCH DATABASE DIAGRAM ----------------------
@st.dialog("📊 TPCH Database Diagram", width="large")
def show_db_diagram():
    st.image("db_diag.png", use_container_width=True)

if st.button("View TPCH Diagram 📊"):
    show_db_diagram()

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

col1, col2 = st.columns([0.85, 0.25])  
with col1:
    st.markdown('<p style="margin-top:10px;">Don\'t know what to write? Check out our</p>', unsafe_allow_html=True)
with col2: 
    if st.button("Examples"):
        show_examples()

# ---------------------- LAYOUT: TWO-PANE VIEW ----------------------
col1, col2 = st.columns([0.5, 0.5])  # Left = Query Panel, Right = Output Panel

with col1:
    st.header("Query")

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_output" not in st.session_state:
        st.session_state.selected_output = {}

    # Display chat history in left panel
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

        # If it's an assistant response, include the dropdown
        if message["role"] == "assistant" and "query_result" in message:
            result = message["query_result"]
            dropdown_key = f"dropdown_{idx}"

            # Restore previous selection or default to "Code"
            selected_output = st.session_state.selected_output.get(dropdown_key, "Code")

            # Dropdown for selecting output type
            selected_output = st.selectbox(
                "Select result format:",
                ["Code", "Full Explanation", "DataFrame", "SQL", "Exception", 
                "Original Question", "Base Prompt", "Cheat Sheet", "Knowledge Graph"],
                key=dropdown_key,
                index=["Code", "Full Explanation", "DataFrame", "SQL", "Exception",
                    "Original Question", "Base Prompt", "Cheat Sheet", "Knowledge Graph"].index(selected_output)
            )

            # Store selection in session state
            st.session_state.selected_output[dropdown_key] = selected_output

            # Store the result reference so the right panel can access it
            st.session_state.last_result = {"query_result": result, "output_type": selected_output}

    # ---------------------- USER INPUT ----------------------
    if query := st.chat_input("Ask a query about the TPCH database..."):

        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("user"):
            st.markdown(query)

        try:
            client = LLMClient()
            result = client.ask(query)

            # Check if result is empty
            if not result or (not result.code and not result.full_explanation and not result.df):
                st.error("⚠️ No valid response received. Please try again.")
            else:
                # Store response in chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "Your answer is ready! Select the result format below:",
                    "query_result": result  
                })

                # Default to last result
                st.session_state.last_result = {"query_result": result, "output_type": "Code"}

                # Refresh to update display pane
                st.rerun()

        except Exception as e:
            st.error(f"❌ Error running query: {e}")

    # Reset button
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.selected_output = {}
        st.rerun()

# ---------------------- RIGHT PANE: DISPLAY OUTPUT ----------------------
with col2:
    st.header("Output")

    if "last_result" in st.session_state and st.session_state.last_result:
        result = st.session_state.last_result["query_result"]
        selected_output = st.session_state.last_result["output_type"]

        st.markdown("---")

        # Display selected output
        if selected_output == "Code":
            st.code(result.code, language="python")
        elif selected_output == "Full Explanation":
            st.write(result.full_explanation)
        elif selected_output == "DataFrame":
            if hasattr(result, "df") and result.df is not None:
                st.dataframe(result.df)  # ✅ Correct DataFrame display
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

