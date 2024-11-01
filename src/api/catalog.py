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

    sql_to_execute = """
                        SELECT potion_sku, potion_name, potion_price, catalog.potion_type, SUM(potion_entries.potion_change) AS potion_quantity
                        FROM catalog
                        JOIN potion_entries ON catalog.potion_type = potion_entries.potion_type
                        GROUP BY potion_sku, potion_name, potion_price, catalog.potion_type
                        HAVING SUM(potion_entries.potion_change) > 0
                        ORDER BY SUM(potion_entries.potion_change) DESC
                        LIMIT 6
                    """
    with db.engine.begin() as connection:
        catalog_inventory = connection.execute(sqlalchemy.text(sql_to_execute)).mappings().fetchall()

        print("catalog_inventory = ", catalog_inventory)

    catalog = []

    for catalog_item in catalog_inventory:
        catalog.append({
            "sku": catalog_item["potion_sku"],
            "name": catalog_item["potion_name"],
            "quantity": catalog_item["potion_quantity"],
            "price": catalog_item["potion_price"],
            "potion_type": catalog_item["potion_type"],
        })

    return catalog
