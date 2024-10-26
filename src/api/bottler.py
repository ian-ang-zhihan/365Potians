from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import heapq

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

    potion_update_parameters = []

    red_used = green_used = blue_used = dark_used = 0
    for potion in potions_delivered:
        potion_update_parameters.append({
            "potion_quantity" : potion.quantity,
            "potion_type" : potion.potion_type
        })

        red_used += (potion.potion_type[0] * potion.quantity)
        green_used += (potion.potion_type[1] * potion.quantity)
        blue_used += (potion.potion_type[2] * potion.quantity)
        dark_used += (potion.potion_type[3] * potion.quantity)

    print("potion_update_parameters = ", potion_update_parameters)
    print("red_used = ", red_used)
    print("green_used = ", green_used)
    print("blue_used = ", blue_used)
    print("dark_used = ", dark_used)

    liquid_update_parameters = [
        {
            "color" : "RED",
            "ml_used" : red_used
        },
        {
            "color" : "GREEN",
            "ml_used" : green_used
        },
        {
            "color" : "BLUE",
            "ml_used" : blue_used
        },
        {
            "color" : "DARK",
            "ml_used" : dark_used
        }
    ]


    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE catalog SET quantity = catalog.quantity + :potion_quantity WHERE potion_type = :potion_type"), potion_update_parameters)
        connection.execute(sqlalchemy.text("UPDATE liquid_inventory SET num_ml = num_ml - :ml_used WHERE color = :color"), liquid_update_parameters)

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
        potion_inventory = connection.execute(sqlalchemy.text("SELECT potion_type, quantity FROM catalog WHERE quantity < 10")).mappings().fetchall()
        print("potion_inventory = ", potion_inventory)

        liquid_inventory = connection.execute(sqlalchemy.text("SELECT potion_type, color, num_ml FROM liquid_inventory")).mappings().fetchall()
        print("liquid_inventory = ", liquid_inventory)

        cur_capacity = connection.execute(sqlalchemy.text("SELECT potion_capacity, ml_capacity FROM storage_capacity")).mappings().fetchone()

    minH = []
    cur_potion_inventory = 0
    for potion in potion_inventory:
        minH.append((potion["quantity"], potion["potion_type"]))
        cur_potion_inventory += potion["quantity"]

    heapq.heapify(minH)
    print("minH = ", minH)

    for liquid in liquid_inventory:
        if liquid["color"] == "RED":
            red_available = liquid["num_ml"]
        if liquid["color"] == "GREEN":
            green_available = liquid["num_ml"]
        if liquid["color"] == "BLUE":
            blue_available = liquid["num_ml"]
        if liquid["color"] == "DARK":
            dark_available = liquid["num_ml"]

    bottle_plan = []

    while minH:
        node = heapq.heappop(minH)

        quantity_to_bottle = 0

        red_needed = node[1][0]
        green_needed = node[1][1]
        blue_needed = node[1][2]
        dark_needed = node[1][3]

        # quantity_to_bottle <= ((50 * (potion_capacity)) - quantity)
        while (red_available >= red_needed and green_available >= green_needed and blue_available >= blue_needed and dark_available >= dark_needed and quantity_to_bottle <= ((50 * (cur_capacity["potion_capacity"])) - cur_potion_inventory)):
            quantity_to_bottle += 1
            red_available -= red_needed
            green_available -= green_needed
            blue_available -= blue_needed
            dark_available -= dark_needed

        if quantity_to_bottle > 0:
            bottle_plan.append({
                "potion_type" : node[1],
                "quantity" : quantity_to_bottle
            })
    
    print("bottle_plan = ", bottle_plan)

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())