import streamlit as st
import requests
import time

# 🔥 CHANGE THIS IF NEEDED
BACKEND_URL = "http://192.168.1.3:8000"

st.set_page_config(page_title="Replenix Dashboard", layout="wide")

st.title("✈️ Replenix Smart Inventory Dashboard")

# ---------------- SAFE REQUEST FUNCTION ----------------
def safe_get(url):
    try:
        return requests.get(url).json()
    except:
        return None

def safe_post(url):
    try:
        return requests.post(url)
    except:
        return None

# ---------------- DEMO BUTTON ----------------
col1, col2 = st.columns([1, 5])

with col1:
    if st.button("🚀 Start Demo"):
        res = safe_post(f"{BACKEND_URL}/demo/start")
        if res:
            st.success("Demo Started!")
        else:
            st.error("❌ Backend not reachable")

# ---------------- FETCH DATA ----------------
items = safe_get(f"{BACKEND_URL}/items")
alerts = safe_get(f"{BACKEND_URL}/alerts")

if items is None:
    st.error("🚨 Backend not running or not reachable")
    st.stop()

# ---------------- INVENTORY ----------------
st.subheader("📦 Inventory Status")

cols = st.columns(len(items))

for i, item in enumerate(items):
    with cols[i]:
        st.metric(
            label=item["name"],
            value=item["stock"]
        )

# ---------------- ALERTS ----------------
st.subheader("⚠️ Alerts")

if alerts:
    for alert in alerts:
        st.error(f"{alert['item']} is LOW ({alert['stock']})")
else:
    st.success("All items are stable ✅")

# ---------------- PREDICTIONS ----------------
st.subheader("🔮 Predictions")

for item in items:
    pred = safe_get(f"{BACKEND_URL}/predict/{item['id']}")
    if pred:
        st.write(
            f"**{pred['item']}** → {pred['predicted_hours_left']} hrs left | {pred['status']}"
        )

# ---------------- EXPLANATION ----------------
st.subheader("🧠 AI Explanation")

for item in items[:2]:
    exp = safe_get(f"{BACKEND_URL}/explain/{item['id']}")
    if exp:
        st.info(f"{exp['item']}: {exp['explanation']}")

# ---------------- AUTO REFRESH ----------------
time.sleep(2)
st.rerun()