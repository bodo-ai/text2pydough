import streamlit as st
from llm import LLMClient

# Set page config
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

# ---------------------- LAYOUT: TWO-PANE VIEW ----------------------
col1, col2 = st.columns([0.5, 0.5])  # Left = Conversation, Right = Display Pane

with col1:
    st.header("Conversation")

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history in left pane
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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
                    "content": "Your answer is ready! Select the result info in the right panel.",
                    "query_result": result  
                })

                # Store result in session state for the display pane
                st.session_state.last_result = result

                # Refresh to update display pane
                st.rerun()

        except Exception as e:
            st.error(f"❌ Error running query: {e}")

    # Reset button
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()

# ---------------------- RIGHT PANE: DISPLAY OUTPUT ----------------------
with col2:
    st.header("Query Results")

    if "last_result" in st.session_state and st.session_state.last_result:
        result = st.session_state.last_result

        # Dropdown for selecting output type
        selected_output = st.selectbox(
            "Select what to view:",
            ["Code", "Full Explanation", "DataFrame", "SQL", "Exception", 
             "Original Question", "Base Prompt", "Cheat Sheet", "Knowledge Graph"],
            key="output_dropdown",
        )

        st.markdown("---")

        # Display selected output
        response_content = ""
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

