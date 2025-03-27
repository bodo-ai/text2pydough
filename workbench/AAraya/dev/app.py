import streamlit as st
import traceback
from llm_v2 import LLMClient

# --- Simple Password gate ---
CORRECT_PASSWORD = "pydoughdemo"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Pydough LLM Demo Login")

    with st.form("login_form", clear_on_submit=False):
        password = st.text_input("Enter password to access the demo:", type="password")
        submitted = st.form_submit_button("Enter")

    if submitted:
        if password == CORRECT_PASSWORD:
            st.session_state.authenticated = True
            st.rerun() 
        else:
            st.error("❌ Incorrect password. Please try again.")

    st.stop()
    
# Set page config for wide layout
st.set_page_config(page_title="PyDough LLM Demo v2", layout="wide", page_icon="bodo_icon.png")

# Add custom CSS to style the dropdown
st.markdown("""
<style>
    /* Make the dropdown more compact */
    div.stSelectbox {
        max-width: 300px;  
        margin-left: 40px; 
    }
    
    /* Hide the label completely */
    div.stSelectbox > label {
        display: none !important;
    }
    .stChatMessage {
        padding-bottom: 5px 
    }
</style>
""", unsafe_allow_html=True)

# ---------------------- PAGE HEADER ----------------------
st.image("logo.png", width=150, use_container_width=False)
st.title("PyDough LLM Demo v2")

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
    - Type a query in the Input panel and press enter.    
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
    st.write("You can **copy** any of the examples by hovering on top of the query and clicking the copy button on the right side. Then paste it into the query box!")

    query_pairs = [
        (
            "Total customers & suppliers per nation, ordered by nation name.",
            "Which nation has the most customers?"
        ),
        (
            "Top 5 nations with most customer orders in 1995.",
            "What was the total revenue from each of these nations in 1995?"
        ),
        (
            "Region with highest total order value in 1996.\n\nRevenue is defined as the sum of extended_price * (1 - discount).",
            "What was the average order value in that region?"
        ),
        (
            "Top 3 regions with most distinct customers.",
            "What’s the total order count per region?"
        ),
        (
            "Customers & order count in 1995 (Europe) with balance > $700.",
            "How many of them placed follow-up orders in 1996?"
        ),
        (
            "Top 10 customers who bought 'green' products in 1998 (with quantity & address).",
            "What was their total spend on green products?"
        ),
        (
            "Customers with more orders in 1995 than 1994.",
            "What was the percentage increase in orders per customer?"
        ),
        (
            "Avg. order value per nation.\n\nRevenue is defined as the sum of extended_price * quantity.",
            "Order nations by average order value, lowest first."
        ),
        (
            "Customers with >30 orders, showing name & total order count.",
            "Also include their account balance."
        ),
        (
            "Orders from 1998 with total price > $100, sorted by price.",
            "Which customers placed these high-value orders?"
        ),
    ]

    for original, follow_up in query_pairs:
        st.markdown("**Query:**")
        st.code(original, language="")
        st.markdown("➡️ **Follow-up option:**")
        st.code(f"{follow_up}", language="")
        st.markdown("---")

def update_dropdown_selection(query_id):
    dropdown_key = f"dropdown_{query_id}"
    st.session_state.active_query = query_id
    st.session_state.selected_output[dropdown_key] = st.session_state[dropdown_key]
    st.session_state.should_rerun = True

    

st.markdown('<p style="margin-top:10px;">Don\'t know what to write? Check out some examples</p>', unsafe_allow_html=True)
if st.button("📋 Examples"):
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
    if "show_chat" not in st.session_state:
        st.session_state.show_chat = False
    if "query_placeholder" not in st.session_state:
        st.session_state.query_placeholder = "Ask a query about the TPCH database..."
    if "dropdown_options" not in st.session_state:
        st.session_state.dropdown_options = ["Full Explanation", "Code", "DataFrame", "SQL", "Exception", 
                                         "Original Question", "Base Prompt", "Cheat Sheet", "Knowledge Graph"]
        

    # Display chat history in left panel after first query.
    if st.session_state.show_chat:
        with st.container(height=350, border=False):
            for idx, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

                # Assistant response include the dropdown
                if message["role"] == "assistant" and "query_id" in message:
                    query_id = message["query_id"]
                    result = st.session_state.query_results[query_id]
                    dropdown_key = f"dropdown_{query_id}"

                    # Define dropdown options
                    full_dropdown_options = ["Full Explanation", "Code", "DataFrame", "SQL", "Exception", 
                                            "Original Question", "Base Prompt", "Cheat Sheet", "Knowledge Graph"]
                    safe_dropdown_options = ["Full Explanation", "Code", "Exception", 
                                             "Original Question", "Base Prompt","Cheat Sheet", "Knowledge Graph"]

                    # Determine which options to show based on result content
                    has_error = result.exception or not (result.code or result.df or result.sql)
                    dropdown_options = safe_dropdown_options if has_error else full_dropdown_options

                    # Set default value if it doesn't exist
                    if dropdown_key not in st.session_state:
                        st.session_state[dropdown_key] = "Full Explanation"

                    
                    if st.session_state[dropdown_key] not in dropdown_options:
                        st.session_state[dropdown_key] = "Full Explanation"

                    st.selectbox(
                        label=" ",
                        options=dropdown_options,
                        key=dropdown_key,
                        on_change=update_dropdown_selection,
                        args=(query_id,)
                    )


    # ---------------------- USER INPUT ----------------------
    if query := st.chat_input(st.session_state.query_placeholder):
        st.session_state.messages.append({"role": "user", "content": query})

        query_id = len(st.session_state.messages)  # Unique ID per query
        client = LLMClient()

        try:
            # Determine if this is a follow-up query
            if st.session_state.last_query_id is not None and len(st.session_state.messages) > 2:
                last_result = st.session_state.query_results[st.session_state.last_query_id]
                result = client.discourse(last_result, query)
            else:
                # This is a new query, use ask
                result = client.ask(query)

            # Check if result is empty
            if not result or (not result.code and not result.full_explanation and not result.df):
                st.code(str(result.exception))
                st.error("⚠️ No valid response received. Please try again.")
            else:
                st.session_state.show_chat = True
                st.session_state.query_placeholder = "Refine your query for more details..."

                # Store response and result
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "Your answer is ready! Select the result format below:",
                    "query_id": query_id
                })

                st.session_state.query_results[query_id] = result
                st.session_state.selected_output[f"dropdown_{query_id}"] = "Full Explanation"
                st.session_state.active_query = query_id
                st.session_state.last_query_id = query_id 

                # Refresh to update display pane
                st.rerun()

        except Exception as e:
            full_traceback = traceback.format_exc()  
            st.error("❌ Error running query. See full traceback below:")
            st.code(full_traceback, language="python")  

    # Reset button
    if st.button("🔄 Restart"):
        st.session_state.messages = []
        st.session_state.selected_output = {}
        st.session_state.query_results = {}
        st.session_state.active_query = None
        st.session_state.last_query_id = None
        st.session_state.show_chat = False 
        st.session_state.query_placeholder = "Ask a query about the TPCH database..."  
        st.rerun()

# ---------------------- RIGHT PANE: DISPLAY OUTPUT ----------------------
with col2:
    st.header("Output")

    # Use active_query instead of last_selected_query
    if "active_query" in st.session_state and st.session_state.active_query is not None:
        query_id = st.session_state.active_query
        result = st.session_state.query_results[query_id]
        dropdown_key = f"dropdown_{query_id}"
        selected_output = st.session_state.get(dropdown_key, "Full Explanation")


        st.markdown("---")

        # Display selected output
        if selected_output == "Full Explanation":
            st.write(result.full_explanation)
            if result.exception:
                st.warning("⚠️ Unable to execute this query at this point, try rephrasing the question.")
                with st.expander("See error details"):
                    st.code(result.exception, language="python")
        elif selected_output == "Code":
            if hasattr(result, "code") and result.code is not None:
                st.code(result.code, language="python")
            else:
                st.warning("⚠️ No code available.")
        elif selected_output == "DataFrame":
            if hasattr(result, "df") and result.df is not None:
                st.dataframe(result.df)  
            else:
                st.warning("⚠️ No DataFrame available.")
        elif selected_output == "SQL":
            if hasattr(result, "sql") and result.sql is not None:
                st.code(result.sql, language="sql") 
            else:
                st.warning("⚠️ No SQL available.")
        elif selected_output == "Exception":
            st.code(result.exception, language="python")
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