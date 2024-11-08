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
            "transaction_id" : order_id,
            "transaction_type" : "POTION_BOTTLE",
            "potion_type" : potion.potion_type,
            "potion_change" : potion.quantity
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
            "transaction_id" : order_id,
            "transaction_type" : "POTION_BOTTLE",
            "potion_type" : [1, 0, 0, 0],
            "liquid_change" : -red_used if red_used > 0 else 0
        },
        {
            "transaction_id" : order_id,
            "transaction_type" : "POTION_BOTTLE",
            "potion_type" : [0, 1, 0, 0],
            "liquid_change" : -green_used if green_used > 0 else 0
        },
        {
            "transaction_id" : order_id,
            "transaction_type" : "POTION_BOTTLE",
            "potion_type" : [0, 0, 1, 0],
            "liquid_change" : -blue_used if blue_used > 0 else 0
        },
        {
            "transaction_id" : order_id,
            "transaction_type" : "POTION_BOTTLE",
            "potion_type" : [0, 0, 0, 1],
            "liquid_change" : -dark_used if dark_used > 0 else 0
        }
    ]

    with db.engine.begin() as connection:
        sql_to_execute = """
                            INSERT INTO potion_entries (transaction_id, transaction_type, potion_type, potion_change) VALUES
                            (:transaction_id, :transaction_type, :potion_type, :potion_change)
                         """
        connection.execute(sqlalchemy.text(sql_to_execute), potion_update_parameters)

        sql_to_execute = """
                            INSERT INTO barrel_entries (transaction_id, transaction_type, potion_type, liquid_change) VALUES 
                            (:transaction_id, :transaction_type, :potion_type, :liquid_change)
                         """
        connection.execute(sqlalchemy.text(sql_to_execute), liquid_update_parameters)

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
        sql_to_execute = """
                            SELECT potion_type, COALESCE(SUM(potion_entries.potion_change), 0) AS quantity
                            FROM potion_entries
                            GROUP BY potion_type
                         """
        potion_inventory = connection.execute(sqlalchemy.text(sql_to_execute)).mappings().fetchall()
        print("potion_inventory = ", potion_inventory)

        sql_to_execute = """
                            SELECT barrels.potion_type, barrels.color, COALESCE(SUM(barrel_entries.liquid_change), 0) AS num_ml
                            FROM barrel_entries
                            LEFT JOIN barrels ON barrel_entries.potion_type = barrels.potion_type
                            GROUP BY barrels.potion_type, barrels.color
                         """
        liquid_inventory = connection.execute(sqlalchemy.text(sql_to_execute)).mappings().fetchall()
        print("liquid_inventory = ", liquid_inventory)

        sql_to_execute = """
                            SELECT COALESCE(SUM(potion_capacity), 1) AS potion_capacity, COALESCE(SUM(ml_capacity), 1) AS ml_capacity
                            FROM capacity_entries
                         """
        cur_capacity = connection.execute(sqlalchemy.text(sql_to_execute)).mappings().fetchone()

    minH = []
    cur_potion_inventory = 0
    for potion in potion_inventory:
        minH.append((potion["quantity"], potion["potion_type"]))
        cur_potion_inventory += potion["quantity"]

    print("cur_potion_inventory = ", cur_potion_inventory)
    heapq.heapify(minH)
    print("minH = ", minH)

    red_available = green_available = blue_available = dark_available = 0
    for liquid in liquid_inventory:
        if liquid["color"] == "RED":
            red_available += liquid["num_ml"]
        if liquid["color"] == "GREEN":
            green_available += liquid["num_ml"]
        if liquid["color"] == "BLUE":
            blue_available += liquid["num_ml"]
        if liquid["color"] == "DARK":
            dark_available += liquid["num_ml"]

    bottle_plan = []

    max_potion_capacity = 50 * cur_capacity["potion_capacity"]
    print("max_potion_capacity = ", max_potion_capacity)

    available_potion_capacity = max_potion_capacity - cur_potion_inventory

    while minH:
        potion_quantity, potion_type = heapq.heappop(minH)

        print("available_potion_capacity = ", available_potion_capacity)
        quantity_to_bottle = 0

        red_needed, green_needed, blue_needed, dark_needed = potion_type

        print("red_needed = ", red_needed)
        print("green_needed = ", green_needed)
        print("blue_needed = ", blue_needed)
        print("dark_needed = ", dark_needed)

        # quantity_to_bottle <= ((50 * (potion_capacity)) - quantity)
        while (
            red_available >= red_needed and 
            green_available >= green_needed and 
            blue_available >= blue_needed and 
            dark_available >= dark_needed and 
            quantity_to_bottle < available_potion_capacity
            ):
            quantity_to_bottle += 1
            red_available -= red_needed
            green_available -= green_needed
            blue_available -= blue_needed
            dark_available -= dark_needed

            if quantity_to_bottle == available_potion_capacity // 2:
                break
        
        print("quantity_to_bottle = ", quantity_to_bottle)

        if quantity_to_bottle > 0 and quantity_to_bottle <= available_potion_capacity:
            bottle_plan.append({
                "potion_type" : potion_type,
                "quantity" : quantity_to_bottle
            })

            available_potion_capacity -= quantity_to_bottle
    
    print("bottle_plan = ", bottle_plan)

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())