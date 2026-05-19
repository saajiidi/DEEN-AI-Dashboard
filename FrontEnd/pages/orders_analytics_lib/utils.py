from datetime import datetime, timedelta

def classify_trend(units_sold):
    """Classify product trend based on units sold."""
    if units_sold >= 20:
        return "Fast Moving"
    elif units_sold > 0:
        return "Slow Moving"
    else:
        return "Non-Moving"

def format_currency(value):
    """Format numeric value to BDT currency string."""
    return f"৳{value:,.2f}"

def get_date_range(option, custom_start=None, custom_end=None):
    """Return ISO format strings for after/before filtering."""
    now = datetime.now()
    if option == "Last 7 Days":
        after = now - timedelta(days=7)
    elif option == "Last 15 Days":
        after = now - timedelta(days=15)
    elif option == "Last 30 Days":
        after = now - timedelta(days=30)
    elif option == "Last 3 Months":
        after = now - timedelta(days=90)
    elif option == "Last 6 Months":
        after = now - timedelta(days=180)
    elif option == "Last 1 Year":
        after = now - timedelta(days=365)
    elif option == "Custom Frame":
        if custom_start and custom_end:
            return custom_start.isoformat(), custom_end.isoformat()
        return None, None
    else:
        return None, None

    return after.isoformat(), None
