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
    potion_type: list[int] # 0 - 100 for each element
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
        - total ml
            - get current ml in database
            - minus ml based on potions delivered
            - update database with new ml of potions
    - check API Spec to ensure you're returning the right thing
    """
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num_green_potions, num_green_ml, num_red_potions, num_red_ml, num_blue_potions, num_blue_ml FROM global_inventory")).mappings()

    inventory = result.fetchone()

    cur_green_potions = inventory["num_green_potions"]
    cur_red_potions = inventory["num_red_potions"]
    cur_blue_potions = inventory["num_blue_potions"]

    cur_green_ml = inventory["num_green_ml"]
    cur_red_ml = inventory["num_red_ml"]
    cur_blue_ml = inventory["num_blue_ml"]

    for potion in potions_delivered:
        # Green
        if potion.potion_type == [0, 100, 0, 0]:
            cur_green_potions += potion.quantity
            cur_green_ml -= (potion.quantity * 100)
        # Red
        if potion.potion_type == [100, 0, 0, 0]:
            cur_red_potions += potion.quantity
            cur_red_ml -= (potion.quantity * 100)
        # Blue
        if potion.potion_type == [0, 0, 100, 0]:
            cur_blue_potions += potion.quantity
            cur_blue_ml -= (potion.quantity * 100)

    with db.engine.begin() as connection:
        # Green
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {cur_green_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {cur_green_ml}"))

        # Red
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {cur_red_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {cur_red_ml}"))

        # Blue
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {cur_blue_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {cur_blue_ml}"))

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

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num_green_ml, num_red_ml, num_blue_ml FROM global_inventory")).mappings()
        # print(result)

    inventory = result.fetchone()
    print("get_bottle_plan_inventory_call = ", inventory)
    cur_green_ml = inventory["num_green_ml"]
    cur_red_ml = inventory["num_red_ml"]
    cur_blue_ml = inventory["num_blue_ml"]

    bottle_plan = []

    # Green
    green_quantity_to_bottle = cur_green_ml // 100
    print("green_quantity_to_bottle = ", green_quantity_to_bottle)
    if green_quantity_to_bottle > 0:
        bottle_plan.append(
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": green_quantity_to_bottle,
                }
        )

    # Red
    red_quantity_to_bottle = cur_red_ml // 100
    print("red_quantity_to_bottle = ", red_quantity_to_bottle)
    if red_quantity_to_bottle > 0:
        bottle_plan.append(
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": red_quantity_to_bottle,
                }
        )

    # Blue
    blue_quantity_to_bottle = cur_blue_ml // 100
    print("blue_quantity_to_bottle = ", blue_quantity_to_bottle)
    if blue_quantity_to_bottle > 0:
        bottle_plan.append(
                {
                    "potion_type": [0, 0, 100, 0],
                    "quantity": blue_quantity_to_bottle,
                }
        )
    
    print("bottle_plan = ", bottle_plan)
    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())