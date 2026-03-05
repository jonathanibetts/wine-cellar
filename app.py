
import streamlit as st
import pandas as pd
import json
import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="🍷 Jonathan's Wine Cellar", page_icon="🍷", layout="wide")

DATA_FILE = "wine_cellar.json"

def load_cellar():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_cellar(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fetch_drinking_window(producer, wine, vintage):
    """Scrape Wine-Searcher and Vivino for drinking window info."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    query = f"{producer} {wine} {vintage}"
    results = {"source": "", "drink_from": "", "drink_to": "", "score": "", "notes": "", "last_refreshed": datetime.now().strftime("%Y-%m-%d")}

    # Try Wine-Searcher
    try:
        url = f"https://www.wine-searcher.com/find/{requests.utils.quote(query)}/1/gbp"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Look for drinking window data
            drink_tags = soup.find_all(string=lambda t: t and ("drink" in t.lower() or "peak" in t.lower()))
            for tag in drink_tags[:5]:
                parent = tag.parent
                text = parent.get_text(separator=" ", strip=True)
                if any(year in text for year in [str(y) for y in range(2020, 2045)]):
                    results["notes"] = text[:200]
                    results["source"] = "Wine-Searcher"
                    break

            # Look for critic score
            score_el = soup.find("span", class_=lambda c: c and "score" in c.lower())
            if score_el:
                results["score"] = score_el.get_text(strip=True)
    except Exception:
        pass

    # Try Vivino as fallback
    if not results["notes"]:
        try:
            url2 = f"https://www.vivino.com/search/wines?q={requests.utils.quote(query)}"
            r2 = requests.get(url2, headers=headers, timeout=8)
            if r2.status_code == 200:
                soup2 = BeautifulSoup(r2.text, "html.parser")
                drink_tags2 = soup2.find_all(string=lambda t: t and "drink" in t.lower())
                for tag in drink_tags2[:3]:
                    text = tag.parent.get_text(separator=" ", strip=True)
                    if len(text) > 20:
                        results["notes"] = text[:200]
                        results["source"] = "Vivino"
                        break
        except Exception:
            pass

    # Heuristic fallback based on wine type and vintage
    if not results["notes"] and vintage:
        try:
            v = int(vintage)
            current_year = datetime.now().year
            age = current_year - v
            # General heuristics by region/type keywords
            wine_lower = (wine + " " + producer).lower()
            if any(k in wine_lower for k in ["barolo", "barbaresco", "brunello", "riserva", "grand cru", "premier cru"]):
                peak_start = v + 10
                peak_end = v + 25
            elif any(k in wine_lower for k in ["bordeaux", "cab", "cabernet", "syrah", "hermitage"]):
                peak_start = v + 8
                peak_end = v + 20
            elif any(k in wine_lower for k in ["burgundy", "pinot", "chambolle", "gevrey", "vosne"]):
                peak_start = v + 5
                peak_end = v + 15
            elif any(k in wine_lower for k in ["champagne", "blanc de blancs", "vintage champ"]):
                peak_start = v + 5
                peak_end = v + 20
            elif any(k in wine_lower for k in ["sauternes", "barsac", "trockenbeerenauslese", "tba"]):
                peak_start = v + 10
                peak_end = v + 40
            elif any(k in wine_lower for k in ["rioja", "tempranillo"]):
                peak_start = v + 5
                peak_end = v + 15
            else:
                peak_start = v + 3
                peak_end = v + 10
            results["drink_from"] = str(peak_start)
            results["drink_to"] = str(peak_end)
            results["source"] = "Heuristic estimate"
            results["notes"] = f"Est. peak: {peak_start}–{peak_end}"
        except Exception:
            pass

    return results

# ─── Session state ───────────────────────────────────────────────
if "cellar" not in st.session_state:
    st.session_state.cellar = load_cellar()

# ─── Header ──────────────────────────────────────────────────────
st.title("🍷 Wine Cellar Manager")
st.caption("Track your cellar · Get optimal drinking windows · Refresh anytime")

# ─── Add Wine Form ────────────────────────────────────────────────
with st.expander("➕ Add a New Bottle", expanded=len(st.session_state.cellar) == 0):
    with st.form("add_wine_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            producer = st.text_input("Producer *", placeholder="e.g. Château Pétrus")
            wine = st.text_input("Wine Name *", placeholder="e.g. Pomerol")
            vintage = st.text_input("Vintage *", placeholder="e.g. 2015")
        with col2:
            region = st.text_input("Region / Appellation", placeholder="e.g. Bordeaux, Pomerol")
            format_size = st.selectbox("Format", ["75cl", "150cl (Magnum)", "300cl (Double Magnum)", "37.5cl (Half)", "500cl (Jeroboam)", "Other"])
            quantity = st.number_input("Quantity", min_value=1, max_value=500, value=1)
        with col3:
            purchase_price = st.text_input("Purchase Price (£)", placeholder="e.g. 250")
            location = st.text_input("Cellar Location", placeholder="e.g. Rack A, Shelf 2")
            notes = st.text_area("Personal Notes", placeholder="Gift from...", height=80)

        submitted = st.form_submit_button("Add to Cellar", use_container_width=True, type="primary")

        if submitted:
            if not producer or not wine or not vintage:
                st.error("Producer, Wine Name and Vintage are required.")
            else:
                entry = {
                    "id": int(time.time() * 1000),
                    "producer": producer.strip(),
                    "wine": wine.strip(),
                    "vintage": vintage.strip(),
                    "region": region.strip(),
                    "format": format_size,
                    "quantity": quantity,
                    "purchase_price": purchase_price.strip(),
                    "location": location.strip(),
                    "personal_notes": notes.strip(),
                    "drink_from": "",
                    "drink_to": "",
                    "score": "",
                    "source": "",
                    "window_notes": "",
                    "last_refreshed": ""
                }
                st.session_state.cellar.append(entry)
                save_cellar(st.session_state.cellar)
                st.success(f"✅ Added: {producer} {wine} {vintage}")
                st.rerun()

# ─── Cellar Table ─────────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📦 My Cellar — {sum(w.get('quantity', 1) for w in st.session_state.cellar)} bottles across {len(st.session_state.cellar)} entries")

if not st.session_state.cellar:
    st.info("Your cellar is empty. Add your first wine above!")
else:
    # Controls row
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 2, 2, 2])
    with ctrl1:
        sort_by = st.selectbox("Sort by", ["Producer", "Vintage", "Wine", "Region", "Score", "Drink From"])
    with ctrl2:
        sort_order = st.radio("Order", ["A → Z / Old → New", "Z → A / New → Old"], horizontal=True)
    with ctrl3:
        search_filter = st.text_input("🔍 Filter", placeholder="Search producer, wine, region...")
    with ctrl4:
        st.write("")
        st.write("")
        refresh_all = st.button("🔄 Refresh Drinking Windows", use_container_width=True, type="primary",
                                help="Re-query Wine-Searcher & other sources for updated drinking window data")

    # Refresh logic
    if refresh_all:
        progress = st.progress(0, text="Fetching drinking window data...")
        total = len(st.session_state.cellar)
        for i, entry in enumerate(st.session_state.cellar):
            progress.progress((i + 1) / total, text=f"Refreshing {entry['producer']} {entry['wine']} {entry['vintage']}...")
            window_data = fetch_drinking_window(entry["producer"], entry["wine"], entry["vintage"])
            entry["drink_from"] = window_data.get("drink_from", "")
            entry["drink_to"] = window_data.get("drink_to", "")
            entry["score"] = window_data.get("score", "")
            entry["source"] = window_data.get("source", "")
            entry["window_notes"] = window_data.get("notes", "")
            entry["last_refreshed"] = window_data.get("last_refreshed", "")
            time.sleep(0.5)
        save_cellar(st.session_state.cellar)
        progress.empty()
        st.success("✅ Drinking windows refreshed!")
        st.rerun()

    # Build dataframe
    df = pd.DataFrame(st.session_state.cellar)
    display_cols = ["producer", "wine", "vintage", "region", "format", "quantity",
                    "purchase_price", "drink_from", "drink_to", "score", "source",
                    "window_notes", "location", "last_refreshed"]
    for col in display_cols:
        if col not in df.columns:
            df[col] = ""
    df = df[display_cols]

    # Filter
    if search_filter:
        mask = df.apply(lambda row: search_filter.lower() in " ".join(row.astype(str)).lower(), axis=1)
        df = df[mask]

    # Sort
    sort_map = {
        "Producer": "producer", "Vintage": "vintage", "Wine": "wine",
        "Region": "region", "Score": "score", "Drink From": "drink_from"
    }
    sort_col = sort_map.get(sort_by, "producer")
    ascending = sort_order.startswith("A")
    if sort_col == "vintage":
        df["_sort_vintage"] = pd.to_numeric(df["vintage"], errors="coerce")
        df = df.sort_values("_sort_vintage", ascending=ascending).drop(columns=["_sort_vintage"])
    else:
        df = df.sort_values(sort_col, ascending=ascending)

    # Pretty column names
    df.columns = ["Producer", "Wine", "Vintage", "Region", "Format", "Qty",
                  "Price (£)", "Drink From", "Drink To", "Score", "Source",
                  "Window Notes", "Location", "Last Refreshed"]

    # Colour-code drinking status
    def highlight_status(row):
        try:
            current = datetime.now().year
            drink_from = int(row["Drink From"]) if row["Drink From"] else None
            drink_to = int(row["Drink To"]) if row["Drink To"] else None
            if drink_from and drink_to:
                if current < drink_from:
                    return ["background-color: #d4edda"] * len(row)  # green = not ready
                elif current > drink_to:
                    return ["background-color: #f8d7da"] * len(row)  # red = past peak
                else:
                    return ["background-color: #fff3cd"] * len(row)  # amber = drink now
        except:
            pass
        return [""] * len(row)

    styled = df.style.apply(highlight_status, axis=1)

    st.dataframe(styled, use_container_width=True, height=500)

    # Legend
    col_l1, col_l2, col_l3 = st.columns(3)
    col_l1.markdown("🟢 **Not yet ready** — hold")
    col_l2.markdown("🟡 **In drinking window** — open now")
    col_l3.markdown("🔴 **Past peak** — drink urgently")

    # Delete / Edit section
    st.markdown("---")
    with st.expander("🗑️ Remove a Bottle"):
        if st.session_state.cellar:
            options = {f"{w['producer']} | {w['wine']} | {w['vintage']} (x{w.get('quantity',1)})": w["id"]
                       for w in st.session_state.cellar}
            to_delete = st.selectbox("Select wine to remove", list(options.keys()))
            if st.button("Remove Selected", type="primary"):
                del_id = options[to_delete]
                st.session_state.cellar = [w for w in st.session_state.cellar if w["id"] != del_id]
                save_cellar(st.session_state.cellar)
                st.success("Removed!")
                st.rerun()

    # Export
    st.markdown("---")
    csv = df.to_csv(index=False)
    st.download_button("📥 Export Cellar as CSV", data=csv, file_name="wine_cellar.csv", mime="text/csv")

    # Stats
    st.markdown("---")
    st.subheader("📊 Cellar Snapshot")
    m1, m2, m3, m4 = st.columns(4)
    total_bottles = sum(w.get("quantity", 1) for w in st.session_state.cellar)
    in_window = sum(1 for w in st.session_state.cellar
                    if w.get("drink_from") and w.get("drink_to")
                    and int(w.get("drink_from", 0) or 0) <= datetime.now().year <= int(w.get("drink_to", 9999) or 9999))
    m1.metric("Total Entries", len(st.session_state.cellar))
    m2.metric("Total Bottles", total_bottles)
    m3.metric("In Drinking Window", in_window)
    m4.metric("Last Refreshed", st.session_state.cellar[-1].get("last_refreshed", "Never") if st.session_state.cellar else "—")
