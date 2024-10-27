from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    """
    - Grab info from database
    - If you have stock in your database, return what you have
    - check API Spec to ensure you're returning the right thing
    """

    with db.engine.begin() as connection:
        catalog_inventory = connection.execute(sqlalchemy.text("SELECT potion_sku, potion_name, quantity, potion_price, potion_type FROM catalog WHERE quantity > 0")).mappings().fetchall()

        print("catalog_inventory = ", catalog_inventory)

    catalog = []

    for catalog_item in catalog_inventory:
        catalog.append({
            "sku": catalog_item["potion_sku"],
            "name": catalog_item["potion_name"],
            "quantity": catalog_item["quantity"],
            "price": catalog_item["potion_price"],
            "potion_type": catalog_item["potion_type"],
        })

    return catalog
