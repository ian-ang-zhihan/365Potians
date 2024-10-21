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

    """
    SELECT SUM(quantity)
    FROM catalog
    JOIN???

    SELECT SUM(num_ml)
    FROM liquid_inventory

    SELECT gold
    FROM cha_ching
    

    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM catalog")).mappings()
        # print("SUM(quantity) result = ", result)
        potion_inventory = result.fetchone()
        # print("potion_inventory = ", potion_inventory)
        # print("potion_inventory[\"sum\"] = ", potion_inventory["sum"])

        result = connection.execute(sqlalchemy.text("SELECT SUM(num_ml) FROM liquid_inventory")).mappings()
        # print("SUM(num_ml) result = ", result)
        liquid_inventory = result.fetchone()
        # print("liquid_inventory = ", liquid_inventory)

        result = connection.execute(sqlalchemy.text("SELECT gold FROM cha_ching")).mappings()
        # print("gold result = ", result)
        gold_inventory = result.fetchone()
        # print("gold_inventory = ", gold_inventory)

    return {"number_of_potions": potion_inventory["sum"], "ml_in_barrels": liquid_inventory["sum"], "gold": gold_inventory["gold"]}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
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

    return "OK"
