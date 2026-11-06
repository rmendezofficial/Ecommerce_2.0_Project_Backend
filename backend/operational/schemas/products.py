from pydantic import BaseModel
from typing import Annotated, List
from decimal import Decimal

class ProductImagesSchema(BaseModel):
    image_url:str
    is_main:bool|None=False

class ProductCreationSchema(BaseModel):
    name: str
    description: str
    price: Decimal
    stock: int
    category_name: str
    tax_code: str
    product_images: List[ProductImagesSchema]
