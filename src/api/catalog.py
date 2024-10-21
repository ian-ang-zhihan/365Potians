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

    """
    SELECT potion_sku, potion_name, quantity, potion_price, potion_type 
    FROM catalog
    WHERE quantity > 0

    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT potion_sku, potion_name, quantity, potion_price, potion_type FROM catalog WHERE quantity > 0")).mappings()
        # result = connection.execute(sqlalchemy.text(f"SELECT num_green_potions, num_red_potions, num_blue_potions FROM global_inventory")).mappings()
        # print("Get Catalog Query Result = ", result)

    catalog_inventory = result.fetchall()
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

    """
    num_green_potions = catalog_inventory["num_green_potions"]
    num_red_potions = catalog_inventory["num_red_potions"]
    num_blue_potions = catalog_inventory["num_blue_potions"]

    if num_green_potions > 0:
        catalog.append(
                {
                    "sku": "GREEN_POTION",
                    "name": "green potion",
                    "quantity": num_green_potions,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                }
            )
        
    if num_red_potions > 0:
        catalog.append(
                {
                    "sku": "RED_POTION",
                    "name": "red potion",
                    "quantity": num_red_potions,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            )

    if num_blue_potions > 0:
        catalog.append(
                {
                    "sku": "BLUE_POTION",
                    "name": "blue potion",
                    "quantity": num_blue_potions,
                    "price": 60,
                    "potion_type": [0, 0, 100, 0],
                }
        )
    """
    return catalog
