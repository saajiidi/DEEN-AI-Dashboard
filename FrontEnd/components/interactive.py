
from __future__ import annotations

import streamlit as st





































def floating_action_bar(
    primary_label: str,
    primary_key: str,
    secondary_label: str | None = None,
    secondary_key: str | None = None,
):
    with st.container():
        # This marker allows the CSS :has() selector to style this entire container
        st.markdown('<div class="hub-action-wrap"></div>', unsafe_allow_html=True)
        if secondary_label and secondary_key:
            c1, c2 = st.columns([2, 1])
            primary_clicked = c1.button(
                primary_label, type="primary", width="stretch", key=primary_key
            )
            secondary_clicked = c2.button(
                secondary_label, width="stretch", key=secondary_key
            )
        else:
            primary_clicked = st.button(
                primary_label, type="primary", width="stretch", key=primary_key
            )
            secondary_clicked = False
    return primary_clicked, secondary_clicked


def dialog_confirm(label: str, state_key: str, reset_fn):
    """
    Registers a tool's reset function for the unified sidebar.
    Doesn't render anything in the sidebar immediately to avoid duplicates.
    """
    if "registered_resets" not in st.session_state:
        st.session_state.registered_resets = {}

    st.session_state.registered_resets[label] = {"fn": reset_fn, "key": state_key}
