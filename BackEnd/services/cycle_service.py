from datetime import datetime, timedelta, timezone
import pandas as pd

def get_bd_timezone():
    return timezone(timedelta(hours=6))

def get_operational_sync_window(ref_time: datetime):
    """
    Thursday 5:30 PM to Saturday 5:30 PM is the weekend slot (Bangladesh).
    RULE: Active shift starts yesterday 5:30 PM and stays active until MIDNIGHT TONIGHT.
    """
    anchor_5_30pm = ref_time.replace(hour=17, minute=30, second=0, microsecond=0)
    start = anchor_5_30pm - timedelta(days=1)
    
    # Weekend adjustment: Friday is covered by the Thu-Sat slot
    if start.weekday() == 4: # Friday
        start -= timedelta(days=1) # Back to Thu 17:30
    
    end = ref_time.replace(hour=23, minute=59, second=59, microsecond=0)
    return start, end

def classify_operational_slots(df: pd.DataFrame):
    """
    Classifies orders into Today, Yesterday, and Backlog based on operational cutoffs.
    """
    if df.empty or "order_date" not in df.columns:
        return df, pd.DataFrame(), pd.DataFrame()

    tz_bd = get_bd_timezone()
    now_dt = datetime.now(tz_bd)
    
    # Operational Day Rollover: Today stays 'Today' until 6 AM the next calendar day.
    if now_dt.hour < 6:
        op_now = now_dt - timedelta(days=1)
    else:
        op_now = now_dt
        
    cutoff_today = op_now.replace(hour=17, minute=30, second=0, microsecond=0).replace(tzinfo=None)
    cutoff_prev = cutoff_today - timedelta(days=1)
    cutoff_day_before = cutoff_prev - timedelta(days=1)
    
    df["dt_parsed"] = pd.to_datetime(df["order_date"], errors="coerce").dt.tz_localize(None)
    
    is_shipped = df["order_status"].str.lower().isin(["completed", "shipped"])
    is_processing = df["order_status"].str.lower() == "processing"
    is_hold = df["order_status"].str.lower() == "on-hold"
    is_waiting = df["order_status"].str.lower() == "pending"
    
    # TODAY (Active Shift)
    df_live = df[
        (is_waiting | is_processing) |
        ( (df["dt_parsed"] >= cutoff_prev) & is_shipped ) |
        ( (df["dt_parsed"] >= cutoff_today) & is_shipped )
    ].copy()
    
    # YESTERDAY
    df_prev = df[
        (df["dt_parsed"] >= cutoff_day_before) & 
        (df["dt_parsed"] < cutoff_prev) & 
        is_shipped
    ].copy()

    # BACKLOG
    df_backlog = df[is_hold].copy()
    
    return df_live, df_prev, df_backlog
