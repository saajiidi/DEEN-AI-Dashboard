import pandas as pd
import streamlit as st
from FrontEnd.components import ui
from .data_helpers import sum_order_level_revenue, build_order_level_dataset

def render_executive_summary(df_sales: pd.DataFrame, df_customers: pd.DataFrame, summary: dict, df_prev_sales: pd.DataFrame = None):
    st.subheader("Executive Summary")
    df = df_sales[df_sales["order_date"].notna()].copy()
    order_df = build_order_level_dataset(df)
    total_revenue = sum_order_level_revenue(df)
    total_orders = order_df["order_id"].replace("", pd.NA).dropna().nunique() if not order_df.empty else 0
    active_customers = df["customer_key"].replace("", pd.NA).dropna().nunique()
    total_items = float(df["qty"].sum())
    pending_count = len(df[df["order_status"].str.lower().isin(["pending", "processing", "on-hold"])])

    d_rev_label, d_rev_val = None, None
    d_ord_label, d_ord_val = None, None
    d_aov_label, d_aov_val = None, None
    d_cust_label, d_cust_val = None, None
    d_items_label, d_items_val = None, None

    if df_prev_sales is not None and not df_prev_sales.empty:
        prev_df = df_prev_sales[df_prev_sales["order_date"].notna()].copy()
        prev_order_df = build_order_level_dataset(prev_df)
        prev_revenue = sum_order_level_revenue(prev_df)
        prev_orders = prev_order_df["order_id"].replace("", pd.NA).dropna().nunique() if not prev_order_df.empty else 0
        prev_customers = prev_df["customer_key"].replace("", pd.NA).dropna().nunique()
        prev_items = float(prev_df["qty"].sum())
        prev_aov = prev_revenue / prev_orders if prev_orders else 0
        
        def get_delta(curr, prev):
            if prev <= 0: return None, None
            diff = curr - prev
            pct = (diff / prev) * 100
            sign = "+" if diff > 0 else ""
            return f"{sign}{pct:.1f}% vs prev", diff

        d_rev_label, d_rev_val = get_delta(total_revenue, prev_revenue)
        d_ord_label, d_ord_val = get_delta(total_orders, prev_orders)
        d_aov_label, d_aov_val = get_delta(total_revenue / total_orders if total_orders else 0, prev_aov)
        d_cust_label, d_cust_val = get_delta(active_customers, prev_customers)
        d_items_label, d_items_val = get_delta(total_items, prev_items)

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: ui.icon_metric("Revenue", f"TK {total_revenue:,.0f}", icon="💰", delta=d_rev_label, delta_val=d_rev_val); ui.badge("Order-level totals")
    with k2: ui.icon_metric("Orders", f"{total_orders:,}", icon="🛒", delta=d_ord_label, delta_val=d_ord_val); ui.badge("Normalized count")
    with k3: ui.icon_metric("AOV", f"TK { (total_revenue/total_orders) if total_orders else 0:,.0f}", icon="💳", delta=d_aov_label, delta_val=d_aov_val); ui.badge("Direct calc")
    with k4: ui.icon_metric("Customers", f"{active_customers:,}", icon="👥", delta=d_cust_label, delta_val=d_cust_val); ui.badge("Distinct keys")
    with k5: ui.icon_metric("Pending", f"{pending_count:,}", icon="⏳", delta="Action required" if pending_count > 5 else "Healthy", delta_color="inverse" if pending_count > 5 else "normal")

    s1, s2, s3 = st.columns(3)
    with s1: ui.icon_metric("Items Sold", f"{total_items:,.0f}", icon="📦", delta=d_items_label, delta_val=d_items_val); st.caption(f"WooCommerce: {summary.get('woocommerce_live',0):,} rows")
    with s2: ui.icon_metric("Repeat Rate", f"{float((df_customers['total_orders'] > 1).mean() * 100) if not df_customers.empty else 0:.1f}%", icon="🔄"); ui.badge("Retention base")
    with s3: ui.icon_metric("Latest Order", df["order_date"].max().strftime("%Y-%m-%d %H:%M") if not df.empty and pd.notna(df["order_date"].max()) else "N/A", icon="🗓️")

    insights = []
    if pending_count > 10: insights.append("Fulfillment pressure is rising. The pending order queue justifies immediate review.")
    mean_qty = df.groupby("order_id")["qty"].sum().mean() if total_orders else 0
    if mean_qty and mean_qty < 1.5: insights.append("Basket depth is light. Consider cross-sell programs.")
    if not df_customers.empty and "segment" in df_customers.columns:
        vip_count = int((df_customers["segment"] == "VIP").sum())
        if vip_count: insights.append(f"{vip_count} VIP customers are active. Prioritize their experience.")
    if not insights: insights.append("Business pulse is stable. Focus on retention programs.")
    ui.commentary("Intelligence Commentary", insights)

    st.markdown("---")
    if st.button("✨ Generate AI Executive Brief", use_container_width=True):
        with st.spinner("Analyzing business performance via AI..."):
            try:
                from BackEnd.services.nlp_engine import LLMAgent
                import os
                agent_type = "Standard"
                if "OPENROUTER_API_KEY" in st.secrets or os.environ.get("OPENROUTER_API_KEY"):
                    agent_type = "OpenRouter"
                elif "HUGGINGFACE_API_KEY" in st.secrets or os.environ.get("HUGGINGFACE_API_KEY"):
                    agent_type = "HuggingFace"
                elif "GROQ_API_KEY" in st.secrets or os.environ.get("GROQ_API_KEY"):
                    agent_type = "Groq"
                elif "GEMINI_API_KEY" in st.secrets or os.environ.get("GEMINI_API_KEY"):
                    agent_type = "Google Gemini"
                    
                agent = LLMAgent(agent_type=agent_type)
                context_dfs = {"sales": df_sales}
                avg_ltv = df_customers["clv"].mean() if not df_customers.empty and "clv" in df_customers.columns else 0
                repeat_rate = (df_customers["total_orders"] > 1).mean() * 100 if not df_customers.empty and "total_orders" in df_customers.columns else 0
                prompt = f"You are a CEO-level Executive Data Analyst. Provide a concise, 4-bullet-point executive brief on the current sales performance. Identify the biggest win, the biggest risk, and summarize Customer Lifetime Value (LTV) improvements or retention health (Current Avg LTV: ৳{avg_ltv:,.0f}, Repeat Rate: {repeat_rate:.1f}%). Keep it strictly under 120 words. Format cleanly using markdown."
                
                ai_brief = agent.query(prompt, context_dfs)
                st.session_state["ai_executive_brief"] = ai_brief
            except Exception as e:
                st.error(f"Could not generate AI brief: {e}")
                
    if "ai_executive_brief" in st.session_state:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%); 
                        padding: 20px; border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2); 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-top: 10px;">
                <div style="color: var(--primary); font-weight: 800; font-size: 0.75rem; letter-spacing: 1px; margin-bottom: 8px;">✨ AI EXECUTIVE BRIEF</div>
                <div style="font-size: 0.95rem; line-height: 1.5;">{st.session_state['ai_executive_brief']}</div>
            </div>
            """, unsafe_allow_html=True
        )
