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

        potion_inventory = connection.execute(sqlalchemy.text("SELECT SUM(potion_change) FROM potion_entries")).mappings().fetchone()
        # print("potion_inventory = ", potion_inventory)
        # print("potion_inventory[\"sum\"] = ", potion_inventory["sum"])

        liquid_inventory = connection.execute(sqlalchemy.text("SELECT SUM(liquid_change) FROM barrel_entries")).mappings().fetchone()
        # print("liquid_inventory = ", liquid_inventory)

        gold_inventory = connection.execute(sqlalchemy.text("SELECT SUM(cha_change) FROM cha_ching_entries")).mappings().fetchone()
        # print("gold_inventory = ", gold_inventory)

    return {"number_of_potions": potion_inventory["sum"], "ml_in_barrels": liquid_inventory["sum"], "gold": gold_inventory["sum"]}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    with db.engine.begin() as connection:

        potion_inventory = connection.execute(sqlalchemy.text("SELECT SUM(potion_change) FROM potion_entries")).mappings().fetchone()

        liquid_inventory = connection.execute(sqlalchemy.text("SELECT SUM(liquid_change) FROM barrel_entries")).mappings().fetchone()

        gold_inventory = connection.execute(sqlalchemy.text("SELECT SUM(cha_change) AS gold FROM cha_ching_entries")).mappings().fetchone()

        cur_capacity = connection.execute(sqlalchemy.text("SELECT SUM(potion_capacity) AS potion_capacity, SUM(ml_capacity) AS ml_capacity FROM capacity_entries")).mappings().fetchone()

    potion_capacity_to_add = 0
    ml_capacity_to_add = 0
    if potion_inventory["sum"] >= (20 * cur_capacity["potion_capacity"]) and gold_inventory["gold"] >= 1000:
        potion_capacity_to_add += 1
        gold_inventory["gold"] -= 1000

    if liquid_inventory["sum"] >= (5000 * cur_capacity["ml_capacity"]) and gold_inventory["gold"] >= 1000:
        ml_capacity_to_add += 1
        gold_inventory["gold"] -= 1000

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
    print("capacity_purchase = ", capacity_purchase, " order_id = ", order_id)
    
    capacity_upgrade_parameters = [
        {
            "transaction_id" : order_id,
            "transaction_type" : "CAPACITY_UPGRADE",
            "potion_capacity_upgrade" : capacity_purchase.potion_capacity,
            "ml_capacity_upgrade" : capacity_purchase.ml_capacity
        }
    ]

    cost = {
        "transaction_id" : order_id,
        "transaction_type" : "CAPACITY_UPGRADE",
        "cost" : -(capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000
    }

    with db.engine.begin() as connection:
        sql_to_execute = """
                            INSERT INTO capacity_entries (transaction_id, transaction_type, potion_capacity, ml_capacity) VALUES
                            (:transaction_id, :transaction_type, :potion_capacity_upgrade, :ml_capacity_upgrade)
                         """
        connection.execute(sqlalchemy.text(sql_to_execute), capacity_upgrade_parameters)

        sql_to_execute = """
                            INSERT INTO cha_ching_entries (transaction_id, transaction_type, cha_change) VALUES 
                            (:transaction_id, :transaction_type, :cost)
                         """
        connection.execute(sqlalchemy.text(sql_to_execute), cost)

    return "OK"
