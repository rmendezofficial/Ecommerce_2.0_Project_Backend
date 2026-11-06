from fastapi import APIRouter, status, Depends
from operational.config import MyTags
from fastapi.responses import JSONResponse
from operational.business_layer.users import is_employee
from typing import Annotated

from operational.database import SessionDB
from operational.models.products import ProductsModel
from operational.models.categories import CategoriesModel

router = APIRouter(prefix="/products")

@router.get("/", tags=[MyTags.admin_products])
async def get_products(session: SessionDB, is_employee: Annotated[bool, Depends(is_employee)]):

    products = session.query(ProductsModel).all()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"products": products})

#create product creation employee protected route