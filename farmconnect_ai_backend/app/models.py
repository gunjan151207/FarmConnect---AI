from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

def utc_now_str():
    return datetime.now(timezone.utc).isoformat()

class Farmer(Base):
    __tablename__ = "farmers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    farm_name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    sales = Column(Float, default=0.0)
    created_at = Column(String, default=utc_now_str)

    products = relationship("Product", back_populates="farmer", cascade="all, delete-orphan")

    @property
    def farm(self):
        return self.farm_name

class Buyer(Base):
    __tablename__ = "buyers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    city = Column(String, default="")
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    created_at = Column(String, default=utc_now_str)

    orders = relationship("Order", back_populates="buyer")

    @property
    def location(self):
        return self.city

    @property
    def company(self):
        return self.city

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, default="vegetable")
    quantity = Column(Float, nullable=False)
    unit = Column(String, default="kg")
    price_per_unit = Column(Float, nullable=False)
    image_path = Column(Text, default="")
    location = Column(String, default="")
    freshness_status = Column(String, default="Grade A")
    description = Column(Text, default="")
    created_at = Column(String, default=utc_now_str)

    farmer = relationship("Farmer", back_populates="products")
    orders = relationship("Order", back_populates="product", cascade="all, delete-orphan")

    # Bridge properties for dual compatibility
    @property
    def crop_name(self):
        return self.name

    @property
    def price_per_kg(self):
        return self.price_per_unit

    @property
    def price(self):
        return self.price_per_unit

    @property
    def quantity_kg(self):
        return self.quantity

    @property
    def image_url(self):
        return self.image_path

    @property
    def image(self):
        return self.image_path

    @property
    def grade(self):
        return self.freshness_status

    @property
    def quality_score(self):
        return 90.0

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="Placed")
    created_at = Column(String, default=utc_now_str)

    product = relationship("Product", back_populates="orders")
    buyer = relationship("Buyer", back_populates="orders")
    logistics = relationship("Logistics", back_populates="order", uselist=False)

    @property
    def quantity_kg(self):
        return self.quantity

    @property
    def amount(self):
        return self.total_amount

class Logistics(Base):
    __tablename__ = "logistics"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    pickup_location = Column(String, nullable=False)
    delivery_location = Column(String, nullable=False)
    distance_km = Column(Float, default=0.0)
    estimated_fee = Column(Float, default=0.0)
    optimized_sequence = Column(Text, default="")
    status = Column(String, default="Pending")
    created_at = Column(String, default=utc_now_str)
    quantity = Column(Float, default=100.0)
    transport_type = Column(String, default="medium")

    order = relationship("Order", back_populates="logistics")

class MarketPrice(Base):
    __tablename__ = "market_prices"
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False, index=True)
    market = Column(String, default="")
    state = Column(String, default="")
    price = Column(Float, nullable=False)
    price_date = Column(String, default=utc_now_str)

class Scheme(Base):
    __tablename__ = "schemes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    eligibility = Column(Text, default="")
    benefits = Column(Text, default="")
    official_url = Column(String, default="")

class PricePrediction(Base):
    __tablename__ = "price_predictions"
    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String, nullable=False)
    base_cost = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    grade = Column(String, nullable=False)
    predicted_price = Column(Float, nullable=False)
    recommended_price = Column(Float, nullable=False)
    created_at = Column(String, default=utc_now_str)


