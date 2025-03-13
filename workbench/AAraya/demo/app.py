import streamlit as st
from llm import LLMClient

# ---------------------- CONVERSATIONAL INTERFACE ----------------------
st.header("Query Interface")

# Initialize session state for messages and dropdown selection
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_output" not in st.session_state:
    st.session_state.selected_output = {}

# Display chat history
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

    # If this is an assistant message with query results, show a dropdown
    if message["role"] == "assistant" and "query_result" in message:
        dropdown_key = f"dropdown_{idx}"
        
        # Restore previous selection or default to "Code"
        selected_output = st.session_state.selected_output.get(dropdown_key, "Code")

        # Create dropdown and store selection
        selected_output = st.selectbox(
            "Select what to view:",
            ["Code", "Full Explanation", "DataFrame", "SQL", "Exception", 
             "Original Question", "Base Prompt", "Cheat Sheet", "Knowledge Graph"],
            key=dropdown_key,
            index=["Code", "Full Explanation", "DataFrame", "SQL", "Exception",
                   "Original Question", "Base Prompt", "Cheat Sheet", "Knowledge Graph"].index(selected_output)
        )

        st.session_state.selected_output[dropdown_key] = selected_output

        # Display selected output
        result = message["query_result"]
        response_content = ""
        if selected_output == "Code":
            response_content = f"```python\n{result.code}\n```"
        elif selected_output == "Full Explanation":
            response_content = result.full_explanation
        elif selected_output == "DataFrame":
            response_content = result.df
        elif selected_output == "SQL":
            response_content = f"```sql\n{result.sql}\n```"
        elif selected_output == "Exception":
            response_content = result.exception
        elif selected_output == "Original Question":
            response_content = result.original_question
        elif selected_output == "Base Prompt":
            response_content = result.base_prompt
        elif selected_output == "Cheat Sheet":
            response_content = result.cheat_sheet
        elif selected_output == "Knowledge Graph":
            response_content = result.knowledge_graph
        
        st.markdown(response_content)

# ---------------------- USER INPUT ----------------------
if query := st.chat_input("Ask a query about the TPCH database..."):

    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    try:
        client = LLMClient()
        result = client.ask(query)

        # Store result in chat history with a placeholder for dropdown
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "**Select an output type below:**",  
            "query_result": result  
        })

        # Refresh to show new dropdown immediately
        st.rerun()

    except Exception as e:
        st.error(f"Error running query: {e}")

# ---------------------- RESET BUTTON ----------------------
if st.button("Reset Conversation"):
    st.session_state.messages = []
    st.session_state.selected_output = {}
    st.rerun()

