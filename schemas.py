"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Police analytics specific schemas

class Incident(BaseModel):
    """
    Incidents collection schema
    Collection name: "incident"
    """
    incident_id: Optional[str] = Field(None, description="External or human-readable ID")
    type: Literal[
        "theft",
        "assault",
        "burglary",
        "fraud",
        "vandalism",
        "traffic",
        "narcotics",
        "homicide",
        "disturbance",
        "other",
    ] = Field("other", description="Incident category")
    description: Optional[str] = Field(None, description="Short description")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        "medium", description="Severity level"
    )
    status: Literal["reported", "dispatched", "on_scene", "resolved", "closed"] = Field(
        "reported", description="Current status"
    )
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    occurred_at: Optional[str] = Field(
        None, description="ISO datetime string when incident occurred"
    )
    reported_at: Optional[str] = Field(
        None, description="ISO datetime string when incident was reported"
    )
    response_minutes: Optional[float] = Field(
        None, ge=0, description="Minutes from report to on-scene"
    )
    precinct: Optional[str] = Field(None, description="Precinct or station name/code")
    officer_id: Optional[str] = Field(None, description="Primary officer ID")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
