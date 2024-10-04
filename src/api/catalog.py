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

    sql_to_execute = "SELECT num_green_potions FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        # print(result)

    quantity = result.fetchone().num_green_potions

    if quantity > 0:
        return [
                {
                    "sku": "GREEN_POTION",
                    "name": "green potion",
                    "quantity": quantity,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                }
            ]
    
    return []
