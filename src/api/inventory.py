from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """

    with db.engine.begin() as connection:
        potion_inventory = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM catalog")).mappings().fetchone()
        # print("potion_inventory = ", potion_inventory)
        # print("potion_inventory[\"sum\"] = ", potion_inventory["sum"])

        liquid_inventory = connection.execute(sqlalchemy.text("SELECT SUM(num_ml) FROM liquid_inventory")).mappings().fetchone()
        # print("liquid_inventory = ", liquid_inventory)

        gold_inventory = connection.execute(sqlalchemy.text("SELECT gold FROM cha_ching")).mappings().fetchone()
        # print("gold_inventory = ", gold_inventory)

    return {"number_of_potions": potion_inventory["sum"], "ml_in_barrels": liquid_inventory["sum"], "gold": gold_inventory["gold"]}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    with db.engine.begin() as connection:
        cur_capacity = connection.execute(sqlalchemy.text("SELECT potion_capacity, ml_capacity FROM storage_capacity")).mappings().fetchone()
        potion_inventory = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM catalog")).mappings().fetchone()
        liquid_inventory = connection.execute(sqlalchemy.text("SELECT SUM(num_ml) FROM liquid_inventory")).mappings().fetchone()
        gold_inventory = connection.execute(sqlalchemy.text("SELECT gold FROM cha_ching")).mappings().fetchone()

    potion_capacity_to_add = 0
    ml_capacity_to_add = 0
    if potion_inventory["sum"] >= (40 * cur_capacity["potion_capacity"]) and gold_inventory["gold"] >= 1000:
        potion_capacity_to_add += 1

    if liquid_inventory["sum"] >= (9000 * cur_capacity["ml_capacity"]) and gold_inventory["gold"] >= 1000:
        ml_capacity_to_add += 1

    return {
        "potion_capacity": potion_capacity_to_add,
        "ml_capacity": ml_capacity_to_add
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    capacity_upgrade_parameters = [
        {
            "potion_capacity_upgrade" : capacity_purchase.potion_capacity,
            "ml_capacity_upgrade" : capacity_purchase.ml_capacity
        }
    ]

    cost = {"cost" : (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000}

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE storage_capacity SET potion_capacity = potion_capacity + :potion_capacity_upgrade, ml_capacity = ml_capacity + :ml_capacity_upgrade"), capacity_upgrade_parameters)
        connection.execute(sqlalchemy.text("UPDATE cha_ching SET gold = gold - :cost"), cost)

    return "OK"
