from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, AliasChoices, ConfigDict

class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class FarmerRegister(BaseSchema):
    name: str
    email: str
    phone: str
    farm_name: str = Field(validation_alias=AliasChoices("farm_name", "farm", "farmName"))
    location: str
    username: str
    password: str

class LoginRequest(BaseSchema):
    username: str
    password: str

class BuyerRegister(BaseSchema):
    name: str
    email: str
    phone: str
    company: Optional[str] = ""
    city: str = Field(default="", validation_alias=AliasChoices("city", "location"))
    username: str
    password: str

class ProductCreate(BaseSchema):
    farmer_id: int = Field(validation_alias=AliasChoices("farmer_id", "farmerId"))
    name: str = Field(validation_alias=AliasChoices("name", "crop_name", "produceName"))
    quantity: float = Field(gt=0, validation_alias=AliasChoices("quantity", "quantity_kg", "produceQuantity"))
    price: float = Field(gt=0, validation_alias=AliasChoices("price", "price_per_unit", "price_per_kg", "producePrice"))
    description: Optional[str] = ""
    category: Optional[str] = "vegetable"
    unit: Optional[str] = "kg"
    image: Optional[str] = Field(default="", validation_alias=AliasChoices("image", "image_path", "image_url", "produceImage"))
    location: Optional[str] = ""
    grade: Optional[str] = Field(default="Grade A", validation_alias=AliasChoices("grade", "freshness_status"))
    quality_score: Optional[float] = Field(default=90.0, ge=0, le=100)

class OrderCreate(BaseSchema):
    buyer_id: int = Field(validation_alias=AliasChoices("buyer_id", "buyerId"))
    product_id: int = Field(validation_alias=AliasChoices("product_id", "productId"))
    quantity: float = Field(gt=0, validation_alias=AliasChoices("quantity", "quantity_kg"))

class LogisticsRequest(BaseSchema):
    pickup_location: str = Field(validation_alias=AliasChoices("pickup_location", "pickup", "pickupLocation", "source"))
    delivery_location: str = Field(validation_alias=AliasChoices("delivery_location", "delivery", "deliveryLocation", "destination"))
    quantity: float = Field(default=100.0, gt=0, validation_alias=AliasChoices("quantity", "quantity_kg", "routeQuantity"))
    transport_type: str = Field(default="medium", validation_alias=AliasChoices("transport_type", "transportType", "vehicle_type", "vehicle"))

class PricePredictionRequest(BaseSchema):
    crop_name: str = Field(validation_alias=AliasChoices("crop_name", "crop", "name"))
    base_cost: Optional[float] = Field(default=14.0, gt=0)
    quantity: Optional[float] = Field(default=100.0, gt=0, validation_alias=AliasChoices("quantity", "quantity_kg"))
    grade: Optional[str] = "Grade A"
    target_mandi: Optional[str] = "Azadpur Mandi, Delhi"
    quality_score: Optional[float] = Field(default=90.0, ge=0, le=100)
    target_price: Optional[float] = None

class BuyerPriceBenchmarkRequest(BaseSchema):
    crop_name: str = Field(validation_alias=AliasChoices("crop_name", "crop", "name"))
    quantity: Optional[float] = Field(default=100.0, gt=0)
    grade: Optional[str] = "Grade A"
    target_mandi: Optional[str] = "Azadpur Mandi, Delhi"
    test_price: Optional[float] = None

class DemandForecastRequest(BaseSchema):
    crop: str = Field(validation_alias=AliasChoices("crop", "crop_name", "name"))
    mandi: Optional[str] = Field(default="Azadpur Mandi, Delhi", validation_alias=AliasChoices("mandi", "location"))
    horizon_days: Optional[int] = Field(default=7, validation_alias=AliasChoices("horizon_days", "days", "forecast_days"))
    grade: Optional[str] = "Grade A"
    quality_score: Optional[float] = Field(default=90.0, ge=0, le=100)

class MarketDescriptionRequest(BaseSchema):
    crop: str = Field(validation_alias=AliasChoices("crop", "crop_name", "name"))
    mandi: Optional[str] = Field(default="Azadpur Mandi, Delhi", validation_alias=AliasChoices("mandi", "location"))
    grade: Optional[str] = "Grade A"
    quality_score: Optional[float] = Field(default=90.0, ge=0, le=100)


