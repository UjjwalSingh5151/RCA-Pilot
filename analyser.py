import pandas as pd
import anthropic
import os

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# --- Standard hypothesis library ---
# You can add to this list anytime
HYPOTHESIS_LIBRARY = [
    "Seasonality assumption didn't hold — actual user behaviour didn't match expected uplift",
    "KR initiative underdelivered — the planned intervention had lower impact than modelled",
    "Creator churn spiked unexpectedly — lost creators weren't replaced fast enough",
    "New creator ramp is slower — new creators posting less than historical average",
    "Click quality dropped — users clicking but not converting, suggesting feed relevance issue",
    "Retained creator fatigue — high-tenure creators reducing post frequency",
    "External event impact — competitor sale, news event, or platform outage affected behaviour",
]

# --- Part 1: Variance scanner ---
def scan_variance(filepath, threshold_pct=5.0):
    """
    Reads actuals vs forecast from Excel.
    Returns a list of metrics that are off by more than threshold_pct.
    threshold_pct: how much variance to flag (default 5%)
    """
    actuals = pd.read_excel(filepath, sheet_name="actuals")
    forecast = pd.read_excel(filepath, sheet_name="forecast")
    seasonality = pd.read_excel(filepath, sheet_name="seasonality")

    # Only look at this week (last 7 days in the file)
    actuals_week = actuals.tail(7).reset_index(drop=True)
    forecast_week = forecast.tail(7).reset_index(drop=True)

    # Metrics to scan — excludes date column
    metrics = [col for col in actuals.columns if col != "date"]

    results = []

    for metric in metrics:
        actual_avg = actuals_week[metric].mean()
        forecast_avg = forecast_week[metric].mean()

        if forecast_avg == 0:
            continue

        variance_pct = ((actual_avg - forecast_avg) / forecast_avg) * 100
        wow_actual = actuals_week[metric].iloc[-1] - actuals.iloc[-8][metric]
        wow_pct = (wow_actual / actuals.iloc[-8][metric]) * 100

        results.append({
            "metric": metric,
            "actual_avg": round(actual_avg, 3),
            "forecast_avg": round(forecast_avg, 3),
            "variance_pct": round(variance_pct, 2),
            "wow_pct": round(wow_pct, 2),
            "flagged": abs(variance_pct) >= threshold_pct,
        })

    flagged = [r for r in results if r["flagged"]]
    return results, flagged, seasonality

# --- Part 2: Hypothesis checker ---
def check_hypotheses(filepath, metric, hypotheses):
    """
    Takes a flagged metric + list of hypotheses.
    Returns LLM verdict for each hypothesis: supported / contradicted / inconclusive.
    """
    actuals = pd.read_excel(filepath, sheet_name="actuals")
    forecast = pd.read_excel(filepath, sheet_name="forecast")
    seasonality = pd.read_excel(filepath, sheet_name="seasonality")

    # Get last 7 days for context
    actuals_week = actuals.tail(7)[["date", metric]].to_string(index=False)
    forecast_week = forecast.tail(7)[["date", metric]].to_string(index=False)

    # Get seasonality rows for this metric if they exist
    season_data = seasonality[seasonality["metric"] == metric]
    season_str = season_data.to_string(index=False) if len(season_data) > 0 else "No seasonality data for this metric"

    hypotheses_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(hypotheses)])

    prompt = f"""You are a senior business analyst at an Indian e-commerce company.

METRIC UNDER REVIEW: {metric}

ACTUALS (last 7 days):
{actuals_week}

FORECAST (last 7 days):
{forecast_week}

SEASONALITY ASSUMPTIONS:
{season_str}

HYPOTHESES TO TEST:
{hypotheses_text}

For each hypothesis, return:
- Verdict: SUPPORTED / CONTRADICTED / INCONCLUSIVE
- Evidence: specific numbers from the data that support your verdict
- Confidence: HIGH / MEDIUM / LOW
- Next step: one specific action to confirm or rule out

Be precise. Reference actual numbers. Do not speculate beyond what the data shows."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


# --- Quick test when run directly ---
if __name__ == "__main__":
    print("Running variance scan on sample_data.xlsx...\n")

    all_results, flagged, _ = scan_variance("sample_data.xlsx")

    print("=== ALL METRICS ===")
    for r in all_results:
        flag = "FLAGGED" if r["flagged"] else "ok"
        print(f"{r['metric']:30} variance: {r['variance_pct']:+.1f}%  WoW: {r['wow_pct']:+.1f}%  [{flag}]")

    if flagged:
        print(f"\n=== FLAGGED METRICS ({len(flagged)}) ===")
        for r in flagged:
            print(f"  - {r['metric']}: {r['variance_pct']:+.1f}% vs forecast")

        print("\nRunning hypothesis check on first flagged metric...")
        metric = flagged[0]["metric"]

        test_hypotheses = [
            HYPOTHESIS_LIBRARY[0],
            HYPOTHESIS_LIBRARY[2],
        ]

        verdict = check_hypotheses("sample_data.xlsx", metric, test_hypotheses)
        print(f"\n=== HYPOTHESIS VERDICTS FOR: {metric} ===")
        print(verdict)
    else:
        print("\nNo metrics flagged at 5% threshold")