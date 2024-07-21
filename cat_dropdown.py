import streamlit as st

def instantiate_selectbox(session_state, default_values):
    """Instantiate a selectbox with the provided list of default values."""
    if not hasattr(session_state, "current_values"):
        session_state.current_values = default_values[:]
    # Adding None as the first option to act as a placeholder
    options = [None] + session_state.current_values
    selected_value = st.selectbox("Choose a livestock category:", options)
    return selected_value

def remove_selected_item(session_state, selected_value):
    """Remove the selected value from the current values in session state."""
    if selected_value and selected_value in session_state.current_values:
        session_state.current_values.remove(selected_value)

def save_selected_item(session_state, selected_value):
    """Save the selected item in the session state."""
    session_state['category'] = selected_value
