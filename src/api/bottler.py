from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    """ 
    - loop through the potions_delivered
    - Updates:
        - total potion
            - get current potions in database
            - add potions from potions delivered
            - update database with new number of potions
    - check API Spec to ensure you're returning the right thing
    """
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")

    sql_to_execute = f"SELECT num_green_potions FROM global_inventory"
    with db.engine.begin() as connection:
        total_potions = connection.execute(sqlalchemy.text(sql_to_execute))
        total_ml = connection.execute(sqlalchemy.text(f"SELECT num_green_ml FROM global_inventory"))

    potion_inventory = total_potions.fetchone().num_green_potions
    ml = total_ml.fetchone().num_green_ml
    for potion in potions_delivered:
        potion_inventory += potion.quantity
        ml -= (100 * potion.quantity)

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {potion_inventory}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {ml}"))

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into green potions.

    """
    - get your current inventory of potions available for sale
    - if you go below a certain number of potions and if you have enough ml, make more potions
    - check API Spec to ensure you're returning the right thing
    """

    sql_to_execute = "SELECT num_green_ml FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        # print(result)

    current_inventory = result.fetchone().num_green_ml
    quantity = current_inventory // 100

    if quantity > 0:
        return [
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": quantity,
                }
            ]
    
    return []

if __name__ == "__main__":
    print(get_bottle_plan())