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
[
Barrel(sku='MINI_RED_BARREL', ml_per_barrel=200, potion_type=[1, 0, 0, 0], price=60, quantity=1), 
Barrel(sku='SMALL_RED_BARREL', ml_per_barrel=500, potion_type=[1, 0, 0, 0], price=100, quantity=1),
Barrel(sku='MEDIUM_RED_BARREL', ml_per_barrel=2500, potion_type=[1, 0, 0, 0], price=250, quantity=10),  
Barrel(sku='LARGE_RED_BARREL', ml_per_barrel=10000, potion_type=[1, 0, 0, 0], price=500, quantity=30)]

Barrel(sku='MINI_GREEN_BARREL', ml_per_barrel=200, potion_type=[0, 1, 0, 0], price=60, quantity=1), 
Barrel(sku='SMALL_GREEN_BARREL', ml_per_barrel=500, potion_type=[0, 1, 0, 0], price=100, quantity=1), 
Barrel(sku='MEDIUM_GREEN_BARREL', ml_per_barrel=2500, potion_type=[0, 1, 0, 0], price=250, quantity=10), 
Barrel(sku='LARGE_GREEN_BARREL', ml_per_barrel=10000, potion_type=[0, 1, 0, 0], price=400, quantity=30), 

Barrel(sku='MINI_BLUE_BARREL', ml_per_barrel=200, potion_type=[0, 0, 1, 0], price=60, quantity=1), 
Barrel(sku='SMALL_BLUE_BARREL', ml_per_barrel=500, potion_type=[0, 0, 1, 0], price=120, quantity=1), 
Barrel(sku='MEDIUM_BLUE_BARREL', ml_per_barrel=2500, potion_type=[0, 0, 1, 0], price=300, quantity=10), 
Barrel(sku='LARGE_BLUE_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 1, 0], price=600, quantity=30), 

Barrel(sku='LARGE_DARK_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 0, 1], price=750, quantity=10), 
"""
"""
[
  {
    "sku": "SMALL_GREEN_BARREL",
    "ml_per_barrel": 500,
    "potion_type": [
      0, 1, 0, 0
    ],
    "price": 100,
    "quantity": 1
  },
  {
    "sku": "SMALL_RED_BARREL",
    "ml_per_barrel": 500,
    "potion_type": [
      1, 0, 0, 0
    ],
    "price": 100,
    "quantity": 1
  },
  {
    "sku": "SMALL_BLUE_BARREL",
    "ml_per_barrel": 500,
    "potion_type": [
      0, 0, 1, 0
    ],
    "price": 600,
    "quantity": 30
  },
  {
    "sku": "LARGE_BLUE_BARREL",
    "ml_per_barrel": 10000,
    "potion_type": [
      0, 0, 1, 0
    ],
    "price": 120,
    "quantity": 30
  }
]
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
            - add ml from barrels delivered (need to multiply num of barrels with ml_per_barrel)
            - update database with new ml
        - gold
            - get current gold in database
            - minus gold based on barrels delivered
            - update database with new gold
    - check API Spec to ensure you're returning the right thing
    """

    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num_green_ml, num_red_ml, num_blue_ml, gold FROM global_inventory")).mappings()

    inventory = result.fetchone()
    
    cur_green_ml = inventory["num_green_ml"]
    cur_red_ml = inventory["num_red_ml"]
    cur_blue_ml = inventory["num_blue_ml"]
    cur_gold = inventory["gold"]


    for barrel in barrels_delivered:
        # Green
        if barrel.potion_type == [0, 1, 0, 0]:
            cur_green_ml += (barrel.ml_per_barrel * barrel.quantity)
            cur_gold -= barrel.price

        # Red
        if barrel.potion_type == [1, 0, 0, 0]:
            cur_red_ml += (barrel.ml_per_barrel * barrel.quantity)
            cur_gold -= barrel.price

        # Blue
        if barrel.potion_type == [0, 0, 1, 0]:
            cur_blue_ml += (barrel.ml_per_barrel * barrel.quantity)
            cur_gold -= barrel.price
        

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {cur_green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {cur_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {cur_blue_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {cur_gold}"))

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
                - What if the value is the same? Which color to buy then?
                
            - Check if that color is being sold
            - Check if you have enough money to buy barrel
    - Parse through wholesale_catalog and see if that color is being sold
    - Based on the results you get, let Roxanne know what barrels you want to buy
    - Check API Spec to ensure you're returning the right thing
    """

    print(wholesale_catalog)

    insert_parameters = []
    for barrel in wholesale_catalog:
        insert_parameters.append({
            "sku" : barrel.sku,
            "ml_per_barrel" : barrel.ml_per_barrel,
            "potion_type": barrel.potion_type,
            "price" : barrel.price
        })

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO barrels_available_for_purchase (sku, ml_per_barrel, potion_type, price) SELECT :sku, :ml_per_barrel, :potion_type, :price WHERE NOT EXISTS (SELECT 1 FROM barrels_available_for_purchase WHERE sku = :sku)"), insert_parameters)

    """
    INSERT INTO barrels_available_for_purchase (sku, ml_per_barrel, potion_type, price)
    SELECT :sku, :ml_per_barrel, :potion_type, :price
    WHERE NOT EXISTS (
        SELECT 1 FROM barrels_available_for_purchase WHERE sku = :sku
    )

    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num_green_potions, num_red_potions, num_blue_potions, gold FROM global_inventory")).mappings()
    
    inventory = result.fetchone()
    green_potion_inventory = (inventory["num_green_potions"], "GREEN")
    red_potion_inventory = (inventory["num_red_potions"], "RED")
    blue_potion_inventory = (inventory["num_blue_potions"], "BLUE")

    gold_inventory = inventory["gold"]

    """
    min_available_potion = min(green_potion_inventory[0], red_potion_inventory[0], blue_potion_inventory[0])
    for p, c in [red_potion_inventory, blue_potion_inventory, green_potion_inventory]:
        if min_available_potion == p:
            min_available_color = c
    """

    min_available_potion = green_potion_inventory[0]
    min_available_color = green_potion_inventory[1]
    for p, c in [red_potion_inventory, blue_potion_inventory]:
        if p < min_available_potion:
            min_available_potion = p
            min_available_color = c

    barrel_to_purchase = f"SMALL_{min_available_color}_BARREL"
    is_for_sale = False
    for barrel in wholesale_catalog:
        if barrel_to_purchase == barrel.sku:
            is_for_sale = True

    if is_for_sale:
        purchase_plan = []

        if min_available_color == "GREEN":
            if (green_potion_inventory[0] < 10) and (gold_inventory >= 100):
                purchase_plan.append(
                    {
                        "sku": "SMALL_GREEN_BARREL",
                        "quantity": 1,
                    }
                )
                gold_inventory -= 100
        # TODO: need to update gold_inventory once you append to the purchase plan since technically your gold would "go down"
        # i.e. you need to ensure that you have enough gold to buy whatever it is you're looking to buy
    
        if min_available_color == "RED":
            if (red_potion_inventory[0] < 10) and (gold_inventory >= 100):
                purchase_plan.append(
                    {
                        "sku": "SMALL_RED_BARREL",
                        "quantity": 1,
                    }
                )
                gold_inventory -= 100

        if min_available_color == "BLUE":
            if (blue_potion_inventory[0] < 10) and (gold_inventory >= 120):
                purchase_plan.append(
                    {
                        "sku": "SMALL_BLUE_BARREL",
                        "quantity": 1,
                    }
                )
                gold_inventory -= 120
    
    return purchase_plan

