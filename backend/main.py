from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import threading
import time
from datetime import datetime
from database import engine, SessionLocal
import models
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for hackathon)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)


# ---------------- DB ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- HOME ----------------
@app.get("/")
def home():
    return {"message": "Replenix Ultimate Backend 🚀"}


# ---------------- CREATE ITEM ----------------
@app.post("/items")
def create_item(name: str, stock: int, threshold: int, db: Session = Depends(get_db)):
    item = models.Item(name=name, stock=stock, threshold=threshold)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ---------------- GET ITEMS ----------------
@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    return db.query(models.Item).all()


# ---------------- PRIORITY ----------------
def get_priority(item_name):
    priority_map = {
        "Coffee": "HIGH",
        "Beer": "HIGH",
        "Whiskey": "MEDIUM",
        "Sandwich": "HIGH",
        "Chips": "LOW",
        "Juice": "MEDIUM"
    }
    return priority_map.get(item_name, "LOW")


# ---------------- USAGE RATES ----------------
def get_usage_rate(item_name):
    rates = {
        "Coffee": 3,
        "Beer": 2,
        "Whiskey": 1,
        "Sandwich": 2,
        "Chips": 1,
        "Juice": 2
    }
    return rates.get(item_name, 1)


# ---------------- PEAK HOURS ----------------
def is_peak_hour():
    hour = datetime.now().hour
    return hour in [7, 8, 9, 17, 18, 19]


# ---------------- USAGE HISTORY ----------------
usage_history = {}  # {item_id: [usage values]}


def log_usage(item_id, usage):
    if item_id not in usage_history:
        usage_history[item_id] = []
    usage_history[item_id].append(usage)

    # keep last 10 records
    if len(usage_history[item_id]) > 10:
        usage_history[item_id].pop(0)


def get_avg_usage(item_id):
    history = usage_history.get(item_id, [])
    if not history:
        return 1
    return sum(history) / len(history)


# ---------------- PREDICTION ----------------
@app.get("/predict/{item_id}")
def predict(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()

    avg_usage = get_avg_usage(item.id)
    hours_left = round(item.stock / avg_usage, 2)

    if hours_left < 3:
        status = "CRITICAL 🔴"
    elif hours_left < 6:
        status = "WARNING 🟡"
    else:
        status = "SAFE 🟢"

    return {
        "item": item.name,
        "stock": item.stock,
        "avg_usage": round(avg_usage, 2),
        "predicted_hours_left": hours_left,
        "priority": get_priority(item.name),
        "status": status
    }


# ---------------- ALERTS ----------------
@app.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    items = db.query(models.Item).all()
    alerts = []

    for item in items:
        if item.stock <= item.threshold:
            alerts.append({
                "item": item.name,
                "stock": item.stock,
                "priority": get_priority(item.name),
                "status": "LOW STOCK ⚠️"
            })

    return alerts


# ---------------- AI EXPLANATION ----------------
@app.get("/explain/{item_id}")
def explain(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()

    avg_usage = get_avg_usage(item.id)
    priority = get_priority(item.name)

    reason = f"{item.name} is consuming at {round(avg_usage,2)} units per cycle."

    if priority == "HIGH":
        reason += " It is a high priority item with high demand."
    elif priority == "MEDIUM":
        reason += " It has moderate usage."
    else:
        reason += " It has low demand."

    return {
        "item": item.name,
        "explanation": reason
    }


# ---------------- EMAIL ----------------
def send_reorder_email(item, quantity):
    print("\n📧 EMAIL SENT")
    print(f"Time: {datetime.now()}")
    print(f"Item: {item.name}")
    print(f"Priority: {get_priority(item.name)}")
    print(f"Stock: {item.stock}")
    print(f"Suggested Order: {quantity}")
    print("Action: Reorder triggered\n")


# ---------------- SIMULATION ----------------
def simulate_usage():
    db = SessionLocal()

    while True:
        items = db.query(models.Item).all()
        peak = is_peak_hour()

        for item in items:
            usage = get_usage_rate(item.name)

            if peak:
                usage *= 2

            log_usage(item.id, usage)

            if item.stock > 0:
                item.stock -= usage
                if item.stock < 0:
                    item.stock = 0

                print(f"{item.name} stock: {item.stock} (usage: {usage})")

                if item.stock <= item.threshold:
                    print(f"⚠️ ALERT: {item.name} low stock")

                if item.stock <= 5:
                    reorder_qty = int(get_avg_usage(item.id) * 10)
                    print(f"🚨 REORDER: {item.name} → {reorder_qty}")
                    send_reorder_email(item, reorder_qty)

        db.commit()
        time.sleep(5)


# ---------------- DEMO ----------------
@app.post("/demo/start")
def start_demo(db: Session = Depends(get_db)):
    db.query(models.Item).delete()

    items = [
        models.Item(name="Beer", stock=30, threshold=10),
        models.Item(name="Whiskey", stock=20, threshold=8),
        models.Item(name="Coffee", stock=40, threshold=15),
        models.Item(name="Sandwich", stock=25, threshold=10),
        models.Item(name="Chips", stock=50, threshold=20),
        models.Item(name="Juice", stock=35, threshold=12)
    ]

    db.add_all(items)
    db.commit()

    return {"message": "Ultimate demo ready 🚀"}


# ---------------- START ----------------
@app.on_event("startup")
def start_simulation():
    thread = threading.Thread(target=simulate_usage)
    thread.daemon = True
    thread.start()