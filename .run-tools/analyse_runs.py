#!/usr/bin/env python3
"""Pull last 90 days of runs from Strava and produce the marathon-run-analysis report.

Credentials (in priority order):
  1. Env vars: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN
  2. ~/.strava/token.json (local dev / after strava_oauth.py)
"""

import json
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

TOKEN_PATH = Path.home() / ".strava" / "token.json"
# Allow override via env vars (used in GitHub Actions)
CLIENT_ID     = os.environ.get("STRAVA_CLIENT_ID",     "229846")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "9b99e83f0c7545621c433575a2ba2e7f85516040")

# ── helpers ──────────────────────────────────────────────────────────────────

def load_token():
    env_refresh = os.environ.get("STRAVA_REFRESH_TOKEN")
    if env_refresh:
        # GitHub Actions path: exchange refresh token for access token directly
        data = {"refresh_token": env_refresh, "expires_at": 0}
    else:
        data = json.loads(TOKEN_PATH.read_text())

    # refresh if expired (or always, when coming from env)
    if data["expires_at"] < time.time() + 60:
        payload = urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": data["refresh_token"],
            "grant_type": "refresh_token",
        }).encode()
        req = urllib.request.Request("https://www.strava.com/oauth/token", data=payload, method="POST")
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        if not env_refresh:
            TOKEN_PATH.write_text(json.dumps(data, indent=2))
    return data["access_token"]

def strava_get(token, path):
    req = urllib.request.Request(
        f"https://www.strava.com/api/v3{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def sec_to_hms(s):
    h, rem = divmod(int(s), 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{sec:02d}s"
    return f"{m}m{sec:02d}s"

def pace_str(speed_ms):
    """m/s → min/km string"""
    if not speed_ms:
        return "—"
    sec_per_km = 1000 / speed_ms
    return f"{int(sec_per_km // 60)}:{int(sec_per_km % 60):02d}/km"

def pace_sec(speed_ms):
    if not speed_ms:
        return None
    return 1000 / speed_ms

def guess_workout_type(act, splits):
    dist_km = act["distance"] / 1000
    avg_speed = act.get("average_speed", 0)
    avg_pace_s = pace_sec(avg_speed)

    # Look at split variance for interval detection
    split_paces = [pace_sec(s.get("average_speed", 0)) for s in splits if s.get("average_speed")]
    if len(split_paces) > 2:
        variance = max(split_paces) - min(split_paces)
    else:
        variance = 0

    if dist_km >= 28:
        return "long"
    if dist_km < 8:
        return "recovery"
    if variance > 60:  # >1min/km spread between fastest and slowest split
        return "intervals"
    if avg_pace_s and avg_pace_s < 330:  # faster than 5:30/km
        return "tempo"
    if dist_km >= 16:
        return "long"
    return "easy"

def iso_date(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

def week_label(dt):
    """Return Monday of the week containing dt."""
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%b %d")

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    token = load_token()

    # 90 days ago
    since = int((datetime.now(timezone.utc) - timedelta(days=90)).timestamp())

    print("Fetching activities from last 90 days (paginated)...", flush=True)
    raw = []
    page = 1
    while True:
        batch = strava_get(token, f"/athlete/activities?after={since}&per_page=100&page={page}")
        if not batch:
            break
        raw.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    runs = [a for a in raw if a.get("type") == "Run" or a.get("sport_type") == "Run"]
    print(f"Found {len(runs)} runs. Fetching detailed splits...", flush=True)

    detailed = []
    for i, r in enumerate(runs):
        print(f"  {i+1}/{len(runs)} — {r['name']} ({r['start_date_local'][:10]})", flush=True)
        det = strava_get(token, f"/activities/{r['id']}")
        splits = det.get("splits_metric", [])
        detailed.append((det, splits))
        time.sleep(0.3)  # be polite to the API

    # ── per-run table ─────────────────────────────────────────────────────────

    runs_data = []
    for det, splits in detailed:
        dist_km = det["distance"] / 1000
        avg_hr = det.get("average_heartrate") or det.get("average_hr")
        max_hr = det.get("max_heartrate")
        elev = det.get("total_elevation_gain", 0)
        wtype = guess_workout_type(det, splits)
        dt = datetime.fromisoformat(det["start_date_local"].replace("Z", "+00:00"))

        runs_data.append({
            "id": det["id"],
            "date": det["start_date_local"][:10],
            "dt": dt,
            "dow": dt.strftime("%a"),
            "name": det["name"],
            "dist_km": dist_km,
            "dist_mi": dist_km * 0.621371,
            "duration": det["elapsed_time"],
            "moving_time": det["moving_time"],
            "avg_speed": det.get("average_speed", 0),
            "avg_pace_s": pace_sec(det.get("average_speed", 0)),
            "avg_hr": avg_hr,
            "max_hr": max_hr,
            "elev_m": elev,
            "type": wtype,
            "splits": splits,
            "week": week_label(dt),
        })

    runs_data.sort(key=lambda x: x["date"])

    # ── weekly rollups ────────────────────────────────────────────────────────

    weeks = {}
    for r in runs_data:
        w = r["week"]
        if w not in weeks:
            weeks[w] = {"runs": [], "label": w}
        weeks[w]["runs"].append(r)

    week_summaries = []
    for wlabel, wdata in sorted(weeks.items(), key=lambda x: min(r["date"] for r in x[1]["runs"])):
        wr = wdata["runs"]
        total_km = sum(r["dist_km"] for r in wr)
        total_time = sum(r["moving_time"] for r in wr)
        longest = max(r["dist_km"] for r in wr)
        easy_paces = [r["avg_pace_s"] for r in wr if r["type"] in ("easy", "recovery") and r["avg_pace_s"]]
        med_easy = sorted(easy_paces)[len(easy_paces)//2] if easy_paces else None
        week_summaries.append({
            "label": wlabel,
            "n_runs": len(wr),
            "total_km": total_km,
            "total_time": total_time,
            "longest_km": longest,
            "med_easy_pace_s": med_easy,
        })

    # ── fitness estimates ─────────────────────────────────────────────────────

    # "Long run" = longest run in the set, no hard cutoff
    long_runs = sorted([r for r in runs_data if r["dist_km"] >= 5], key=lambda x: x["dist_km"], reverse=True)
    tempo_runs = [r for r in runs_data if r["type"] == "tempo"]
    peak_week_km = max(w["total_km"] for w in week_summaries) if week_summaries else 0
    current_week_km = week_summaries[-1]["total_km"] if week_summaries else 0

    # Fitness: use best 5–10 km effort via Riegel formula → marathon projection
    # Riegel: T2 = T1 * (D2/D1)^1.06
    predicted_range = None
    # Use fastest effort ≥ 3 km regardless of absolute pace
    best_efforts = sorted(
        [r for r in runs_data if r["dist_km"] >= 3 and r["avg_pace_s"]],
        key=lambda x: x["avg_pace_s"]
    )
    if best_efforts:
        best = best_efforts[0]
        d1 = best["dist_km"] * 1000  # metres
        t1 = best["moving_time"]     # seconds
        d2 = 42195.0
        # Riegel projection
        t2_riegel = t1 * (d2 / d1) ** 1.06
        # Add a modest fatigue buffer (training runs, not races)
        t2_lo = t2_riegel * 1.04
        t2_hi = t2_riegel * 1.12
        mp_s = 1000 / (d2 / t2_lo / 1000)  # sec per km at predicted pace
        predicted_range = (sec_to_hms(t2_lo), sec_to_hms(t2_hi), t2_lo / 42.195, best)

    tempo_mp_estimate = None
    if tempo_runs:
        tempo_pace_s = sorted([r["avg_pace_s"] for r in tempo_runs if r["avg_pace_s"]])[len(tempo_runs)//2]
        mp_from_tempo = tempo_pace_s + 15
        tempo_mp_estimate = mp_from_tempo

    # ── taper check ──────────────────────────────────────────────────────────

    ws = week_summaries
    taper_note = ""
    if len(ws) >= 2:
        prev_km = ws[-2]["total_km"]
        curr_km = ws[-1]["total_km"]
        taper_pct = (curr_km / prev_km * 100) if prev_km else 0
        if taper_pct < 50:
            taper_note = f"YES — current week is {taper_pct:.0f}% of previous ({curr_km:.0f} vs {prev_km:.0f} km)"
        elif taper_pct < 75:
            taper_note = f"PARTIAL — current week is {taper_pct:.0f}% of previous ({curr_km:.0f} vs {prev_km:.0f} km)"
        else:
            taper_note = f"NOT YET — current week is {taper_pct:.0f}% of previous ({curr_km:.0f} vs {prev_km:.0f} km) — needs more reduction"

    # ── longest run check ─────────────────────────────────────────────────────

    today = datetime.now(timezone.utc).replace(tzinfo=None)
    if long_runs:
        lr = long_runs[0]
        lr_dt = lr["dt"].replace(tzinfo=None)
        days_ago = (today - lr_dt).days
        lr_flag = ""
        if lr["dist_km"] < 28:
            lr_flag = f" ⚠⚠ ONLY {lr['dist_km']:.1f} km — marathon prep expects ≥28–32 km"
        if days_ago > 21:
            lr_flag += f" ⚠ {days_ago} days ago — may be too far back"
        lr_summary = f"{lr['dist_km']:.1f} km on {lr['date']} ({days_ago} days ago){lr_flag}"
    else:
        lr_summary = "NO LONG RUN FOUND in last 30 days ⚠⚠"

    # ── build report ──────────────────────────────────────────────────────────

    hr_available = any(r["avg_hr"] for r in runs_data)

    lines = []
    a = lines.append

    a("=" * 70)
    a("MARATHON PREP: RUN HISTORY ANALYSIS")
    a(f"Alireza Toghiani | Toronto Marathon, May 3 2026 | 90-day window | Analysed {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    a("=" * 70)

    # TL;DR
    a("\n## TL;DR\n")
    if predicted_range:
        lo, hi, mp_s, lr = predicted_range
        a(f"• Predicted finish: {lo} – {hi}  (MP target: ~{pace_str(1000/mp_s)})")
    else:
        a("• Predicted finish: insufficient data for estimate")

    strengths = []
    risks = []

    if long_runs and long_runs[0]["dist_km"] >= 30:
        strengths.append(f"solid long run ({long_runs[0]['dist_km']:.1f} km)")
    elif long_runs:
        risks.append(f"longest run only {long_runs[0]['dist_km']:.1f} km")
    else:
        risks.append("no long run found")

    if not hr_available:
        risks.append("no HR data — pace-only analysis")

    if tempo_runs:
        strengths.append(f"tempo work in the bank ({len(tempo_runs)} session{'s' if len(tempo_runs)>1 else ''})")

    taper_happening = "NOT YET" not in taper_note
    if taper_happening:
        strengths.append("taper underway")
    else:
        risks.append("taper not yet happening")

    a(f"• Biggest strength: {'; '.join(strengths) if strengths else 'see below'}")
    a(f"• Biggest risk: {'; '.join(risks) if risks else 'looking clean'}")

    # Weekly table
    a("\n## Weekly Rollups\n")
    a(f"{'Week (Mon)':>12} {'Runs':>5} {'km':>7} {'Time':>10} {'Longest':>9} {'Easy Pace':>11}")
    a("-" * 60)
    for w in week_summaries:
        ep = f"{int(w['med_easy_pace_s']//60)}:{int(w['med_easy_pace_s']%60):02d}/km" if w['med_easy_pace_s'] else "—"
        a(f"{w['label']:>12} {w['n_runs']:>5} {w['total_km']:>7.1f} {sec_to_hms(w['total_time']):>10} {w['longest_km']:>8.1f}k {ep:>11}")
    a(f"\nPeak week: {peak_week_km:.1f} km | Current week: {current_week_km:.1f} km")

    # Per-run table
    a("\n## Per-Run Log\n")
    hr_col = "Avg HR" if hr_available else "Avg HR"
    a(f"{'Date':>12} {'Day':>4} {'km':>6} {'Duration':>10} {'Pace':>9} {hr_col:>7} {'MaxHR':>6} {'Elev':>6} {'Type':>10}  Name")
    a("-" * 100)
    for r in runs_data:
        hr_str = f"{r['avg_hr']:.0f}" if r["avg_hr"] else "—"
        mhr_str = f"{r['max_hr']:.0f}" if r["max_hr"] else "—"
        a(f"{r['date']:>12} {r['dow']:>4} {r['dist_km']:>6.2f} {sec_to_hms(r['moving_time']):>10} {pace_str(r['avg_speed']):>9} {hr_str:>7} {mhr_str:>6} {r['elev_m']:>5.0f}m {r['type']:>10}  {r['name']}")

    # Race-readiness verdict
    a("\n## Race-Readiness Verdict\n")

    a(f"**1. Fitness — Predicted marathon time:**")
    if predicted_range:
        lo, hi, mp_s, lr = predicted_range
        a(f"   {lo} – {hi}")
        a(f"   Based on long run of {lr['dist_km']:.1f} km @ {pace_str(lr['avg_speed'])} (MP estimated as 85% of LR pace = {pace_str(1000/mp_s)})")
    if tempo_mp_estimate:
        a(f"   Tempo-based MP check: ~{int(tempo_mp_estimate//60)}:{int(tempo_mp_estimate%60):02d}/km → consistent with above")
    if not hr_available:
        a("   ⚠ No HR data available — estimates are pace-only")

    a(f"\n**2. Taper:**")
    a(f"   {taper_note}")

    a(f"\n**3. Longest Run:**")
    a(f"   {lr_summary}")

    a(f"\n**4. Red Flags:**")
    # HR drift check (last long run)
    if long_runs and long_runs[0]["splits"] and long_runs[0]["splits"][0].get("average_heartrate"):
        lr_splits = long_runs[0]["splits"]
        hr_vals = [s.get("average_heartrate", 0) for s in lr_splits if s.get("average_heartrate")]
        if hr_vals and len(hr_vals) > 4:
            first_half_hr = sum(hr_vals[:len(hr_vals)//2]) / (len(hr_vals)//2)
            second_half_hr = sum(hr_vals[len(hr_vals)//2:]) / len(hr_vals[len(hr_vals)//2:])
            drift = second_half_hr - first_half_hr
            if drift > 8:
                a(f"   ⚠ HR drift on long run: +{drift:.1f} bpm first→second half — indicates heat/fueling stress")
            else:
                a(f"   ✓ HR drift on long run: +{drift:.1f} bpm — within acceptable range")
        else:
            a("   — HR split data insufficient for drift analysis")
    else:
        a("   — No HR split data on long run for drift analysis")

    # Check for gaps > 3 days
    dates = sorted([r["date"] for r in runs_data])
    big_gaps = []
    for i in range(1, len(dates)):
        d1 = datetime.strptime(dates[i-1], "%Y-%m-%d")
        d2 = datetime.strptime(dates[i], "%Y-%m-%d")
        gap = (d2 - d1).days
        if gap > 4:
            big_gaps.append(f"{dates[i-1]} → {dates[i]} ({gap} days)")
    if big_gaps:
        for g in big_gaps:
            a(f"   ⚠ Gap: {g}")
    else:
        a("   ✓ No suspicious gaps (>4 days) in training")

    # Back-to-back hard days
    hard_types = {"tempo", "intervals", "long"}
    back2back = []
    for i in range(1, len(runs_data)):
        if runs_data[i]["type"] in hard_types and runs_data[i-1]["type"] in hard_types:
            d1 = runs_data[i-1]["date"]
            d2 = runs_data[i]["date"]
            gap = (datetime.strptime(d2, "%Y-%m-%d") - datetime.strptime(d1, "%Y-%m-%d")).days
            if gap <= 1:
                back2back.append(f"{d1} ({runs_data[i-1]['type']}) + {d2} ({runs_data[i]['type']})")
    if back2back:
        for b in back2back:
            a(f"   ⚠ Back-to-back hard days: {b}")
    else:
        a("   ✓ No back-to-back hard days found")

    a(f"\n**5. Strengths:**")
    total_runs = len(runs_data)
    total_km = sum(r["dist_km"] for r in runs_data)
    a(f"   • {total_runs} runs totalling {total_km:.1f} km in 90 days — {total_km/90*7:.1f} km/week average")
    if tempo_runs:
        a(f"   • Quality work present: {len(tempo_runs)} tempo run(s), {len([r for r in runs_data if r['type']=='intervals'])} interval session(s)")
    if long_runs:
        a(f"   • Long run base: {long_runs[0]['dist_km']:.1f} km max")
    if not risks:
        a("   • Training looks consistent through the build")

    # Final 9 days plan
    a("\n## Final 9-Day Plan (Apr 25 – May 3)\n")
    a("Based on your training data. Paces derived from your runs.")

    if predicted_range:
        lo, hi, mp_s, lr = predicted_range
        mp_pace = pace_str(1000 / mp_s)
        easy_paces = [r["avg_pace_s"] for r in runs_data if r["type"] in ("easy", "recovery") and r["avg_pace_s"]]
        if easy_paces:
            easy_pace_s = sorted(easy_paces)[len(easy_paces)//2]
            easy_pace = f"{int(easy_pace_s//60)}:{int(easy_pace_s%60):02d}/km"
        else:
            easy_pace_s = mp_s * (1000 / 850)  # estimate
            easy_pace = f"~{int(easy_pace_s//60)}:{int(easy_pace_s%60):02d}/km"

        # 10K race pace estimate (Riegel from MP)
        pace_10k_s = mp_s * 0.88 if mp_s else None
        pace_10k = f"{int(pace_10k_s//60)}:{int(pace_10k_s%60):02d}/km" if pace_10k_s else "—"

        a(f"\nPace zones:")
        a(f"  Easy:  {easy_pace}")
        a(f"  MP:    {mp_pace}  (target race pace)")
        a(f"  10K:   {pace_10k}  (tune-up / strides)")

        a(f"\n{'Date':>12} {'Day':>4} {'km':>5}  Plan")
        a("-" * 80)
        plan = [
            ("Apr 25", "Sat", "10",   f"Easy {easy_pace} — first day of taper, keep it relaxed"),
            ("Apr 26", "Sun", "6",    f"Easy {easy_pace} — short shakeout, legs only"),
            ("Apr 27", "Mon", "REST", "Full rest or 20 min walk. No running."),
            ("Apr 28", "Tue", "10",   f"Tune-up: 2 km easy warm-up + 3×1 km @ {pace_10k} (90s jog recovery) + 2 km easy"),
            ("Apr 29", "Wed", "6",    f"Easy {easy_pace} — keep it honest, no heroics"),
            ("Apr 30", "Thu", "REST", "Full rest. Legs up. Hydrate aggressively."),
            ("May  1", "Fri", "5",    f"Easy {easy_pace} — just to shake out, stop before you feel tired"),
            ("May  2", "Sat", "4",    f"Shake-out: 3 km easy + 4×80 m strides @ 10K effort, full walk recovery"),
            ("May  3", "Sun", "42.2", f"RACE — Toronto Marathon. Start @ {mp_pace}. Do NOT go out faster."),
        ]
        for date, day, km, note in plan:
            a(f"{date:>12} {day:>4} {km:>5}  {note}")
    else:
        a("(insufficient pace data for personalized plan)")

    # Fueling & race morning
    a("\n## Race Morning (Toronto, May 3 — expect 5–12°C, possible rain)\n")
    a("• Dress: singlet + arm warmers or light long-sleeve you can tie off. Throwaway layer at start.")
    a("• Fuel: carb-load Thu–Sat (pasta, rice, bagels). Morning: 2h before gun — bagel + peanut butter + banana + coffee.")
    a("• Hydration: 500 mL water with electrolytes night before. 300–400 mL water morning of. Sip on line.")
    a("• Gels: every 30–35 min from km 8 onward (aim 40–60 g carbs/hr). Wash down with water, not sports drink.")
    a("• Cold rain plan: Vaseline on inner thighs, nipples, armpits. Waterproof shoes cover optional.")
    a("• Pacing: run the first 10 km feeling too slow. Everything after km 30 is what matters.")

    # Caveats
    a("\n## Caveats\n")
    if not hr_available:
        a("• ⚠ HR data missing for most/all runs — all estimates are pace-based only.")
    a("• Workout type classification is heuristic (pace + split variance). May mis-label some efforts.")
    a("• Long-run pace → MP conversion assumes 85% effort, which is a mid-range assumption.")
    a("• Strava GPS pace can be noisy on tight turns or under tree cover — median used where possible.")
    a("• No race or time-trial in the data — prediction confidence is moderate.")

    a("\n" + "=" * 70)

    report = "\n".join(lines)
    print(report)

    out_path = Path("/Users/alirezatoghianikhorasgani/Desktop/Claude/Run Analyser/race_analysis.txt")
    out_path.write_text(report)
    print(f"\n\nFull report saved to {out_path}")

    # Export structured JSON for the HTML dashboard
    json_data = {
        "athlete": "Alireza Toghiani",
        "race_date": "2026-05-03",
        "race_name": "Toronto Marathon",
        "generated": datetime.now().isoformat(),
        "predicted_lo": sec_to_hms(t2_lo) if predicted_range else None,
        "predicted_hi": sec_to_hms(t2_hi) if predicted_range else None,
        "mp_pace": pace_str(1000 / (t2_lo / 42.195)) if predicted_range else None,
        "peak_week_km": round(peak_week_km, 1),
        "total_km_90d": round(sum(r["dist_km"] for r in runs_data), 1),
        "longest_run_km": round(long_runs[0]["dist_km"], 2) if long_runs else 0,
        "longest_run_date": long_runs[0]["date"] if long_runs else None,
        "taper_note": taper_note,
        "lr_summary": lr_summary,
        "weeks": [
            {
                "label": w["label"],
                "n_runs": w["n_runs"],
                "total_km": round(w["total_km"], 1),
                "longest_km": round(w["longest_km"], 1),
                "total_time_s": w["total_time"],
                "med_easy_pace_s": round(w["med_easy_pace_s"]) if w["med_easy_pace_s"] else None,
            }
            for w in week_summaries
        ],
        "runs": [
            {
                "date": r["date"],
                "dow": r["dow"],
                "name": r["name"],
                "dist_km": round(r["dist_km"], 2),
                "duration_s": r["moving_time"],
                "pace": pace_str(r["avg_speed"]),
                "avg_hr": r["avg_hr"],
                "max_hr": r["max_hr"],
                "elev_m": round(r["elev_m"]),
                "type": r["type"],
            }
            for r in runs_data
        ],
        "plan": [
            {"date": "Apr 25", "day": "Sat", "km": "10",   "note": f"Easy {easy_pace if predicted_range else '?'} — first day of taper"},
            {"date": "Apr 26", "day": "Sun", "km": "6",    "note": f"Easy {easy_pace if predicted_range else '?'} — short shakeout"},
            {"date": "Apr 27", "day": "Mon", "km": "REST", "note": "Full rest or 20 min walk. No running."},
            {"date": "Apr 28", "day": "Tue", "km": "10",   "note": f"Tune-up: 2 km easy + 3×1 km @ {pace_10k if predicted_range else '?'} (90s recovery) + 2 km easy"},
            {"date": "Apr 29", "day": "Wed", "km": "6",    "note": f"Easy {easy_pace if predicted_range else '?'} — keep it honest"},
            {"date": "Apr 30", "day": "Thu", "km": "REST", "note": "Full rest. Legs up. Hydrate aggressively."},
            {"date": "May 1",  "day": "Fri", "km": "5",    "note": f"Easy {easy_pace if predicted_range else '?'} — shakeout, stop before you feel tired"},
            {"date": "May 2",  "day": "Sat", "km": "4",    "note": "Shake-out: 3 km easy + 4×80 m strides @ 10K effort"},
            {"date": "May 3",  "day": "Sun", "km": "42.2", "note": f"RACE — Toronto Marathon. Start @ {pace_str(1000/(t2_lo/42.195)) if predicted_range else '?'}. Do NOT go out faster."},
        ] if predicted_range else [],
        "red_flags": [f for f in [
            f"HR drift +{round(second_half_hr - first_half_hr, 1)} bpm on long run" if long_runs and long_runs[0]["splits"] and long_runs[0]["splits"][0].get("average_heartrate") and len([s for s in long_runs[0]["splits"] if s.get("average_heartrate")]) > 4 else None,
            *[f"Gap: {g}" for g in big_gaps],
            *[f"Back-to-back hard: {b}" for b in back2back],
        ] if f],
        "strengths": strengths,
    }
    script_dir = Path(__file__).parent
    json_path = script_dir / "race_data.json"
    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"JSON data saved to {json_path}")

    # ── Embed data into index.html ──
    # Checks script_dir/index.html (CI: .run-tools/) and the local dev copy
    new_data_line = f"const DATA = {json.dumps(json_data)};"
    for html_path in [
        script_dir / "index.html",
        script_dir.parent / "misfit" / "index.html",
        Path.home() / "Desktop" / "Claude" / "Run Analyser" / "index.html",
    ]:
        if not html_path.exists():
            continue
        content = html_path.read_text()
        import re
        updated = re.sub(r"const DATA = \{.*?\};", new_data_line, content, count=1, flags=re.DOTALL)
        if updated != content:
            html_path.write_text(updated)
            print(f"Updated DATA in {html_path}")


if __name__ == "__main__":
    main()
