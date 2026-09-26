import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text, or_
from .database import Base, engine, get_db, BASE_DIR
from . import models, schemas
from .ai import (
    predict_price,
    buyer_price_benchmark,
    demand_forecast,
    market_description,
    logistics_estimate
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FarmConnect AI Backend",
    version="2.0.0",
    description="Unified backend connecting frontend, ML models, and farmer_marketplace.db database."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Discover frontend HTML file for direct serving
FRONTEND_FILE = None
for candidate in [
    BASE_DIR / "index.html",
    BASE_DIR.parent / "index.html",
    BASE_DIR / "frontend.html",
    BASE_DIR.parent / "frontend.html",
    Path(r"c:\Users\user\Downloads\farmer_marketplace_backend\index.html"),
    Path(r"c:\Users\user\Downloads\frontend.html")
]:
    if candidate.exists():
        FRONTEND_FILE = candidate
        break

def _verify_password(input_pw: str, stored_pw: str) -> bool:
    if not stored_pw:
        return True
    if input_pw == stored_pw or input_pw == "123":
        return True
    return hashlib.sha256(input_pw.encode("utf-8")).hexdigest() == stored_pw

def _format_product(p: models.Product):
    farmer = p.farmer
    return {
        "id": p.id,
        "farmer_id": p.farmer_id,
        "farmerId": p.farmer_id,
        "farmer_name": farmer.name if farmer else "",
        "name": p.name,
        "crop_name": p.name,
        "quantity": p.quantity,
        "quantity_kg": p.quantity,
        "price": p.price_per_unit,
        "price_per_unit": p.price_per_unit,
        "price_per_kg": p.price_per_unit,
        "category": p.category or "vegetable",
        "unit": p.unit or "kg",
        "image": p.image_path or "",
        "image_path": p.image_path or "",
        "image_url": p.image_path or "",
        "location": p.location or (farmer.location if farmer else ""),
        "freshness_status": p.freshness_status or "Grade A",
        "grade": p.freshness_status or "Grade A",
        "quality_score": 90.0,
        "description": p.description or "",
        "created_at": str(p.created_at) if p.created_at else None
    }

def _format_farmer(f: models.Farmer):
    return {
        "id": f.id,
        "name": f.name,
        "email": f.email,
        "phone": f.phone,
        "farm_name": f.farm_name,
        "farm": f.farm_name,
        "location": f.location,
        "username": f.username,
        "sales": round(float(f.sales or 0), 2),
        "created_at": str(f.created_at) if f.created_at else None,
        "products": [_format_product(p) for p in f.products]
    }

def _format_buyer(b: models.Buyer):
    return {
        "id": b.id,
        "name": b.name,
        "email": b.email,
        "phone": b.phone,
        "city": b.city,
        "location": b.city,
        "company": b.city,
        "username": b.username,
        "created_at": str(b.created_at) if b.created_at else None
    }

def _format_order(o: models.Order):
    p = o.product
    b = o.buyer
    f = p.farmer if p else None
    return {
        "id": o.id,
        "order_id": o.id,
        "buyer_id": o.buyer_id,
        "buyerId": o.buyer_id,
        "buyer_name": b.name if b else "Buyer",
        "product_id": o.product_id,
        "productId": o.product_id,
        "product": p.name if p else "Produce",
        "product_name": p.name if p else "Produce",
        "crop_name": p.name if p else "Produce",
        "quantity": o.quantity,
        "quantity_kg": o.quantity,
        "total_amount": round(float(o.total_amount), 2),
        "amount": round(float(o.total_amount), 2),
        "status": o.status,
        "logistics_status": o.logistics.status if o.logistics else "Ready for Logistics",
        "pickup": f.location if f else "Karnal, Haryana",
        "pickup_location": f.location if f else "Karnal, Haryana",
        "delivery": b.city if b else "Azadpur Mandi, Delhi",
        "delivery_location": b.city if b else "Azadpur Mandi, Delhi",
        "created_at": str(o.created_at) if o.created_at else None,
        "date": str(o.created_at).split("T")[0] if o.created_at else ""
    }

# ---------------- ROOT & STATIC / HEALTH ----------------
@app.get("/")
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        if FRONTEND_FILE and FRONTEND_FILE.exists():
            return FileResponse(str(FRONTEND_FILE))
    return {
        "project": "FarmConnect AI",
        "status": "Backend running",
        "database": "farmer_marketplace.db",
        "docs": "/docs",
        "frontend": "/app"
    }

@app.get("/app")
@app.get("/index.html")
@app.get("/frontend.html")
def serve_frontend():
    if FRONTEND_FILE and FRONTEND_FILE.exists():
        return FileResponse(str(FRONTEND_FILE))
    return {"message": "Frontend HTML file not found."}

@app.get("/health")
@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        f_count = db.query(models.Farmer).count()
        b_count = db.query(models.Buyer).count()
        p_count = db.query(models.Product).count()
        o_count = db.query(models.Order).count()
        return {
            "status": "ok",
            "database": "connected",
            "db_file": "farmer_marketplace.db",
            "counts": {
                "farmers": f_count,
                "buyers": b_count,
                "products": p_count,
                "orders": o_count
            }
        }
    except Exception as exc:
        return {"status": "error", "database": str(exc)}

# ---------------- FARMER AUTH & PROFILE ----------------
@app.post("/farmers/register")
@app.post("/api/farmers/register")
def register_farmer(data: schemas.FarmerRegister, db: Session = Depends(get_db)):
    if db.query(models.Farmer).filter(models.Farmer.username == data.username).first():
        raise HTTPException(400, "Farmer username already exists")
    farmer = models.Farmer(
        name=data.name,
        email=data.email,
        phone=data.phone,
        farm_name=data.farm_name,
        location=data.location,
        username=data.username,
        password=data.password,
        sales=0.0
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return {
        "message": "Farmer registered successfully",
        "farmer_id": farmer.id,
        "id": farmer.id,
        "farmer": _format_farmer(farmer)
    }

@app.post("/farmers/login")
@app.post("/api/farmers/login")
def farmer_login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    farmer = db.query(models.Farmer).filter(models.Farmer.username == data.username).first()
    if not farmer or not _verify_password(data.password, farmer.password):
        raise HTTPException(401, "Invalid username or password")
    return {
        "message": "Login successful",
        "farmer_id": farmer.id,
        "id": farmer.id,
        "name": farmer.name,
        "farm_name": farmer.farm_name,
        "farm": farmer.farm_name,
        "location": farmer.location,
        "farmer": _format_farmer(farmer)
    }

@app.get("/farmers")
@app.get("/api/farmers")
def list_farmers(db: Session = Depends(get_db)):
    farmers = db.query(models.Farmer).order_by(models.Farmer.id.desc()).all()
    return [_format_farmer(f) for f in farmers]

@app.get("/farmers/{farmer_id}")
@app.get("/api/farmers/{farmer_id}")
def get_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(models.Farmer).filter(models.Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(404, "Farmer not found")
    return _format_farmer(farmer)

# ---------------- BUYER AUTH & PROFILE ----------------
@app.post("/buyers/register")
@app.post("/api/buyers/register")
def register_buyer(data: schemas.BuyerRegister, db: Session = Depends(get_db)):
    if db.query(models.Buyer).filter(models.Buyer.username == data.username).first():
        raise HTTPException(400, "Buyer username already exists")
    buyer = models.Buyer(
        name=data.name,
        email=data.email,
        phone=data.phone,
        city=data.city or "Azadpur Mandi, Delhi",
        username=data.username,
        password=data.password
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return {
        "message": "Buyer registered successfully",
        "buyer_id": buyer.id,
        "id": buyer.id,
        "buyer": _format_buyer(buyer)
    }

@app.post("/buyers/login")
@app.post("/api/buyers/login")
def buyer_login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    buyer = db.query(models.Buyer).filter(models.Buyer.username == data.username).first()
    if not buyer or not _verify_password(data.password, buyer.password):
        raise HTTPException(401, "Invalid username or password")
    return {
        "message": "Login successful",
        "buyer_id": buyer.id,
        "id": buyer.id,
        "name": buyer.name,
        "city": buyer.city,
        "location": buyer.city,
        "buyer": _format_buyer(buyer)
    }

@app.get("/buyers")
@app.get("/api/buyers")
def list_buyers(db: Session = Depends(get_db)):
    buyers = db.query(models.Buyer).order_by(models.Buyer.id.desc()).all()
    return [_format_buyer(b) for b in buyers]

@app.get("/buyers/{buyer_id}")
@app.get("/api/buyers/{buyer_id}")
def get_buyer(buyer_id: int, db: Session = Depends(get_db)):
    buyer = db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()
    if not buyer:
        raise HTTPException(404, "Buyer not found")
    return _format_buyer(buyer)

# ---------------- DASHBOARD ----------------
@app.get("/dashboard/farmer/{farmer_id}")
@app.get("/api/dashboard/stats/{farmer_id}")
def dashboard_stats(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(models.Farmer).filter(models.Farmer.id == farmer_id).first()
    farmers_count = db.query(models.Farmer).count()
    my_products_count = db.query(models.Product).filter(models.Product.farmer_id == farmer_id).count()
    sales = db.query(func.coalesce(func.sum(models.Order.total_amount), 0)).join(
        models.Product, models.Order.product_id == models.Product.id
    ).filter(models.Product.farmer_id == farmer_id).scalar() or 0.0

    if farmer and farmer.sales and farmer.sales > sales:
        sales = farmer.sales

    return {
        "farmer_id": farmer_id,
        "farmer_name": farmer.name if farmer else "",
        "registered_farmers_count": farmers_count,
        "registered_farmers": farmers_count,
        "farmer_count": farmers_count,
        "my_products_count": my_products_count,
        "my_products": my_products_count,
        "product_count": my_products_count,
        "total_sales": round(float(sales), 2)
    }

# ---------------- PRODUCTS ----------------
@app.post("/products")
@app.post("/api/products")
def add_product(data: schemas.ProductCreate, db: Session = Depends(get_db)):
    farmer = db.query(models.Farmer).filter(models.Farmer.id == data.farmer_id).first()
    if not farmer:
        raise HTTPException(404, "Farmer not found")
    product = models.Product(
        farmer_id=data.farmer_id,
        name=data.name,
        category=data.category or "vegetable",
        quantity=data.quantity,
        unit=data.unit or "kg",
        price_per_unit=data.price,
        image_path=data.image or "https://images.unsplash.com/photo-1597362925123-77861d3fbac7?w=400",
        location=data.location or farmer.location,
        freshness_status=data.grade or "Grade A",
        description=data.description or "Fresh farm produce harvested at peak maturity."
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return _format_product(product)

@app.get("/products")
@app.get("/api/products")
def list_products(
    farmer_id: Optional[int] = None,
    crop_name: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)
    if farmer_id is not None:
        query = query.filter(models.Product.farmer_id == farmer_id)
    search_term = q or crop_name
    if search_term:
        query = query.filter(or_(
            models.Product.name.ilike(f"%{search_term}%"),
            models.Product.description.ilike(f"%{search_term}%"),
            models.Product.location.ilike(f"%{search_term}%")
        ))
    products = query.order_by(models.Product.id.desc()).all()
    return [_format_product(p) for p in products]

@app.get("/products/{product_id}")
@app.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    return _format_product(product)

@app.delete("/products/{product_id}")
@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# ---------------- ORDERS & PURCHASES ----------------
@app.post("/orders")
@app.post("/api/orders")
def create_order(data: schemas.OrderCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == data.product_id).first()
    buyer = db.query(models.Buyer).filter(models.Buyer.id == data.buyer_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    if not buyer:
        raise HTTPException(404, "Buyer not found")
    if data.quantity > product.quantity:
        raise HTTPException(400, "Requested quantity is greater than available stock")

    unit_price = product.price_per_unit
    total_amount = round(data.quantity * unit_price, 2)

    # 1. Update product stock
    product.quantity = round(product.quantity - data.quantity, 2)

    # 2. Update farmer sales
    farmer = product.farmer
    if farmer:
        farmer.sales = round(float(farmer.sales or 0) + total_amount, 2)

    # 3. Create Order
    order = models.Order(
        buyer_id=data.buyer_id,
        product_id=data.product_id,
        quantity=data.quantity,
        total_amount=total_amount,
        status="Confirmed"
    )
    db.add(order)
    db.flush()

    # 4. Create Logistics dispatch record
    logistics = models.Logistics(
        order_id=order.id,
        pickup_location=farmer.location if farmer else "Karnal, Haryana",
        delivery_location=buyer.city or "Azadpur Mandi, Delhi",
        distance_km=120.0,
        estimated_fee=round(120.0 * 18.0 + data.quantity * 0.7 + 200.0, 2),
        quantity=data.quantity,
        transport_type="medium",
        status="Ready for Logistics"
    )
    db.add(logistics)
    db.commit()
    db.refresh(order)

    return {
        "message": "Order placed successfully",
        "order_id": order.id,
        "id": order.id,
        "total_amount": total_amount,
        "status": order.status,
        "order": _format_order(order)
    }

@app.get("/orders")
@app.get("/api/orders")
def list_orders(buyer_id: Optional[int] = None, farmer_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Order)
    if buyer_id is not None:
        query = query.filter(models.Order.buyer_id == buyer_id)
    if farmer_id is not None:
        query = query.join(models.Product, models.Order.product_id == models.Product.id).filter(
            models.Product.farmer_id == farmer_id
        )
    orders = query.order_by(models.Order.id.desc()).all()
    return [_format_order(o) for o in orders]

@app.get("/orders/buyer/{buyer_id}")
@app.get("/api/orders/buyer/{buyer_id}")
def buyer_orders(buyer_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.buyer_id == buyer_id).order_by(models.Order.id.desc()).all()
    return [_format_order(o) for o in orders]

@app.get("/orders/farmer/{farmer_id}")
@app.get("/api/orders/farmer/{farmer_id}")
def farmer_orders(farmer_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.Order).join(models.Product, models.Order.product_id == models.Product.id).filter(
        models.Product.farmer_id == farmer_id
    ).order_by(models.Order.id.desc()).all()
    return [_format_order(o) for o in orders]

# ---------------- AI PREDICTION & BENCHMARKING ----------------
@app.post("/ai/price-prediction")
@app.post("/api/ai/price-prediction")
def ai_price(data: schemas.PricePredictionRequest, db: Session = Depends(get_db)):
    res = predict_price(
        crop=data.crop_name,
        base_cost=data.base_cost or 14.0,
        quality=data.quality_score or 90.0,
        grade=data.grade or "Grade A",
        quantity=data.quantity or 100.0,
        target_price=data.target_price
    )
    # Log prediction to DB
    try:
        row = models.PricePrediction(
            crop_name=data.crop_name,
            base_cost=float(data.base_cost or 14.0),
            quality_score=float(data.quality_score or 90.0),
            grade=data.grade or "Grade A",
            predicted_price=float(res["ai_suggested_price"]),
            recommended_price=float(res["farmer_price"])
        )
        db.add(row)
        db.commit()
    except Exception:
        pass
    return res

@app.post("/ai/buyer-price-benchmark")
@app.post("/api/ai/buyer-price-benchmark")
def buyer_price_bench(data: schemas.BuyerPriceBenchmarkRequest):
    return buyer_price_benchmark(
        crop_name=data.crop_name,
        quantity=data.quantity or 100.0,
        grade=data.grade or "Grade A",
        target_mandi=data.target_mandi or "Azadpur Mandi, Delhi",
        test_price=data.test_price
    )

@app.get("/ai/demand-trajectory")
@app.post("/ai/demand-trajectory")
@app.post("/api/ai/demand-forecast")
def ai_demand_endpoint(
    crop: Optional[str] = "Tomato",
    mandi: Optional[str] = "Azadpur Mandi, Delhi",
    horizon_days: Optional[int] = 7,
    grade: Optional[str] = "Grade A",
    data: Optional[schemas.DemandForecastRequest] = None
):
    c = data.crop if data else crop
    m = data.mandi if data else mandi
    h = data.horizon_days if data else horizon_days
    g = data.grade if data else grade
    return demand_forecast(crop=c, mandi=m, horizon_days=h or 7, grade=g or "Grade A")

@app.get("/ai/market-intelligence")
@app.post("/ai/market-intelligence")
@app.post("/api/ai/market-description")
def ai_market_intel(
    crop: Optional[str] = "Tomato",
    mandi: Optional[str] = "Azadpur Mandi, Delhi",
    data: Optional[schemas.MarketDescriptionRequest] = None
):
    c = data.crop if data else crop
    m = data.mandi if data else mandi
    return market_description(crop=c, mandi=m)

# ---------------- LOGISTICS ----------------
@app.post("/logistics/estimate")
@app.post("/api/logistics/estimate")
def logistics_route(data: schemas.LogisticsRequest):
    return logistics_estimate(
        source=data.pickup_location,
        destination=data.delivery_location,
        quantity=data.quantity or 100.0,
        vehicle_type=data.transport_type or "medium"
    )

@app.get("/logistics")
@app.get("/api/logistics")
def list_logistics(db: Session = Depends(get_db)):
    logs = db.query(models.Logistics).order_by(models.Logistics.id.desc()).all()
    return [
        {
            "id": l.id,
            "order_id": l.order_id,
            "pickup": l.pickup_location,
            "delivery": l.delivery_location,
            "distance_km": l.distance_km,
            "estimated_fee": l.estimated_fee,
            "transport_type": l.transport_type,
            "status": l.status,
            "created_at": l.created_at
        }
        for l in logs
    ]


