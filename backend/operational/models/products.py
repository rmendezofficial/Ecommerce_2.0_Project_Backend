from enum import Enum as PyEnum
from operational.database import Base
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Float, ForeignKey, Numeric, Enum
from sqlalchemy.sql import func

class ProductStatusModel(str, PyEnum):
    active = "active"
    inactive = "inactive"

class ProductsModel(Base):

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10,2), nullable=False)
    stock = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(Enum(ProductStatusModel), default=ProductStatusModel.active, nullable=False)
    taxcode = Column(String(200),nullable=False)
    reserve_stock = Column(Integer, nullable=False)
    available_stock = Column(Integer, nullable=False)