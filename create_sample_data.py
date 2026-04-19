import pandas as pd
from datetime import date

# --- 14 days of data: last week + this week ---
dates = [
    date(2025, 4, 7),  date(2025, 4, 8),  date(2025, 4, 9),
    date(2025, 4, 10), date(2025, 4, 11), date(2025, 4, 12), date(2025, 4, 13),
    date(2025, 4, 14), date(2025, 4, 15), date(2025, 4, 16),
    date(2025, 4, 17), date(2025, 4, 18), date(2025, 4, 19), date(2025, 4, 20),
]

# --- Sheet 1: Actuals (what really happened) ---
actuals = pd.DataFrame({
    "date": dates,
    "creators_new":         [120,118,122,119,121,130,125, 123,120,118,117,119,121,120],
    "creators_retained":    [800,798,802,799,801,810,805, 808,805,800,798,796,794,792],
    "creators_resurrected": [50,48,52,49,51,55,53,   54,52,50,48,46,44,42],
    "creators_churned":     [30,32,28,31,29,25,27,   35,38,40,42,44,46,48],
    "post_per_creator":     [3.2,3.1,3.3,3.2,3.1,3.4,3.3, 3.0,2.9,2.8,2.7,2.8,2.9,2.8],
    "click_per_post":       [45,44,46,45,43,47,46,   42,40,39,38,39,40,39],
    "order_per_click":      [0.032,0.031,0.033,0.032,0.031,0.034,0.033, 0.030,0.029,0.028,0.027,0.028,0.029,0.028],
})

# --- Sheet 2: Forecast (what you expected) ---
forecast = pd.DataFrame({
    "date": dates,
    "creators_new":         [120,119,121,120,122,131,126, 125,124,123,122,123,124,125],
    "creators_retained":    [800,799,801,800,802,811,806, 812,814,816,818,820,822,824],
    "creators_resurrected": [50,49,51,50,52,56,54,   56,57,58,59,60,61,62],
    "creators_churned":     [30,31,29,30,28,24,26,   30,30,30,30,30,30,30],
    "post_per_creator":     [3.2,3.1,3.3,3.2,3.1,3.4,3.3, 3.3,3.4,3.5,3.6,3.6,3.7,3.7],
    "click_per_post":       [45,44,46,45,43,47,46,   46,47,48,49,49,50,50],
    "order_per_click":      [0.032,0.031,0.033,0.032,0.031,0.034,0.033, 0.033,0.034,0.035,0.036,0.036,0.037,0.037],
})

# --- Sheet 3: Seasonality assumptions ---
seasonality = pd.DataFrame({
    "date": dates[7:],  # only this week
    "metric":           ["post_per_creator","post_per_creator","click_per_post",
                         "click_per_post","order_per_click","order_per_click","order_per_click"],
    "expected_uplift_pct": [3.0, 6.0, 2.0, 4.0, 3.0, 5.0, 6.0],
    "driver":           ["Payday weekend","Festival week","Payday weekend",
                         "Festival week","Payday weekend","Festival week","Festival week"],
    "notes":            ["Expected 3% uplift Mon","Ramp up Thu onwards",
                         "Higher intent users","Peak shopping intent",
                         "Better product match","Festival purchases","Continued festival"],
})

# --- Write all 3 sheets into one Excel file ---
with pd.ExcelWriter("sample_data.xlsx", engine="openpyxl") as writer:
    actuals.to_excel(writer, sheet_name="actuals", index=False)
    forecast.to_excel(writer, sheet_name="forecast", index=False)
    seasonality.to_excel(writer, sheet_name="seasonality", index=False)

print("sample_data.xlsx created with 3 sheets")
print(f"Actuals: {len(actuals)} rows")
print(f"Forecast: {len(forecast)} rows")
print(f"Seasonality: {len(seasonality)} rows")