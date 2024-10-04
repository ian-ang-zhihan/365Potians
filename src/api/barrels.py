from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

"""
[Barrel(sku='MEDIUM_RED_BARREL', ml_per_barrel=2500, potion_type=[1, 0, 0, 0], price=250, quantity=10), Barrel(sku='SMALL_RED_BARREL', ml_per_barrel=500, potion_type=[1, 0, 0, 0], price=100, quantity=10), Barrel(sku='MEDIUM_GREEN_BARREL', ml_per_barrel=2500, potion_type=[0, 1, 0, 0], price=250, quantity=10), Barrel(sku='SMALL_GREEN_BARREL', ml_per_barrel=500, potion_type=[0, 1, 0, 0], price=100, quantity=10), Barrel(sku='MEDIUM_BLUE_BARREL', ml_per_barrel=2500, potion_type=[0, 0, 1, 0], price=300, quantity=10), Barrel(sku='SMALL_BLUE_BARREL', ml_per_barrel=500, potion_type=[0, 0, 1, 0], price=120, quantity=10), Barrel(sku='MINI_RED_BARREL', ml_per_barrel=200, potion_type=[1, 0, 0, 0], price=60, quantity=1), Barrel(sku='MINI_GREEN_BARREL', ml_per_barrel=200, potion_type=[0, 1, 0, 0], price=60, quantity=1), Barrel(sku='MINI_BLUE_BARREL', ml_per_barrel=200, potion_type=[0, 0, 1, 0], price=60, quantity=1), Barrel(sku='LARGE_DARK_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 0, 1], price=750, quantity=10), Barrel(sku='LARGE_BLUE_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 1, 0], price=600, quantity=30), Barrel(sku='LARGE_GREEN_BARREL', ml_per_barrel=10000, potion_type=[0, 1, 0, 0], price=400, quantity=30), Barrel(sku='LARGE_RED_BARREL', ml_per_barrel=10000, potion_type=[1, 0, 0, 0], price=500, quantity=30)]
"""
# { item_sku: string : [ml_per_barrel: int, potion_type: list, price: int, quantity: int]}
# barrels = {
#     "MINI_RED_BARREL" : [200, [1, 0, 0, 0], 60, 10],
#     "SMALL_RED_BARREL" : [500, [1, 0, 0, 0], 100, 10],
#     "MEDIUM_RED_BARREL" : [2500, [1, 0, 0, 0], 250, 10],
#     "LARGE_RED_BARREL" : [10000, [1, 0, 0, 0], 500, 30],
#     "MINI_GREEN_BARREL" : [200, [0, 1, 0, 0], 60, 10],
#     "SMALL_GREEN_BARREL" : [500, [0, 1, 0, 0], 100, 10],
#     "MEDIUM_GREEN_BARREL" : [2500, [0, 1, 0, 0], 250, 10],
#     "LARGE_GREEN_BARREL" : [10000, [0, 1, 0, 0], 400, 30]
# }

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    """ 
    - loop through the barrels_delivered
    - Updates:
        - total ml
            - get current ml in database
            - add ml from barrels delivered
            - update database with new ml
        - gold
            - get current gold in database
            - minus gold based on barrels delivered
            - update database with new gold
    - check API Spec to ensure you're returning the right thing
    """

    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    sql_to_execute = f"SELECT num_green_ml FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        cost = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory"))


    total_ml = result.fetchone().num_green_ml
    total_cost = cost.fetchone().gold
    for barrel in barrels_delivered:
        total_ml += barrel.ml_per_barrel
        total_cost -= barrel.price

    sql_to_execute = f"UPDATE global_inventory SET num_green_ml = {total_ml}"
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {total_cost}"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    """ 
    Steps for v2
    - Parse through wholesale_catalog and add it to a dictionary temporarily? (or can possibly do this later)
    - Get the results you need from the appropriate tables in your database
    - Logic
        - For your RGBD ml:
            - Find the lowest (minimum) color supply -> choose to buy that color
            - Check if that color is being sold
            - Check if you have enough money to buy barrel
    - Parse through wholesale_catalog and see if that color is being sold
    - Based on the results you get, let Roxanne know what barrels you want to buy
    - Check API Spec to ensure you're returning the right thing
    """

    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        gold_result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        # print("Result: ", type(result.fetchone()))
        # print("Result: ", type(result.fetchone().num_green_potions))
    
    green_potion_inventory = result.fetchone().num_green_potions
    gold_inventory = gold_result.fetchone().gold
    if (green_potion_inventory < 10) and (gold_inventory >= 100):
        return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            }
        ]
    
    return []

