from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import heapq

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

ml = 10000
cost = 750
cost per ml = 750/10000 = 0.075 gold per ml

sell per ml = 0.15 gold per ml (100% profit margin)

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

    liquid_update_parameters = []
    cost = 0

    for barrel in barrels_delivered:
        liquid_update_parameters.append({
            "new_ml" : barrel.ml_per_barrel * barrel.quantity,
            "potion_type" : barrel.potion_type
        })

        cost += barrel.price

    print("liquid_update_parameters = ", liquid_update_parameters)
    print("cost = ", cost)

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE liquid_inventory SET num_ml = num_ml + :new_ml WHERE potion_type = :potion_type"), liquid_update_parameters)
        connection.execute(sqlalchemy.text("UPDATE cha_ching SET gold = gold - :cost"), {"cost" : cost})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    """ 
    Steps for v3
    - Parse through wholesale_catalog and add it to a dictionary temporarily? (or can possibly do this later)
    - Get the results you need from the appropriate tables in your database
    - Logic
        - For your RGBD ml:
            - Find the quantity of potions that are less than 10 and figure out what colors are needed to brew them
                - What if the value is the same? Which color to buy then?
                
            - Check if that color is being sold
            - Check if you have enough money to buy barrel
    - Parse through wholesale_catalog and see if that color is being sold
    - Based on the results you get, let Roxanne know what barrels you want to buy
    - Check API Spec to ensure you're returning the right thing
    """

    print(wholesale_catalog)

    #--- LOGGING THE TYPES OF BARRELS SOLD ---#
    insert_parameters = []
    available_for_purchase = {} # key = barrel.sku | value = dictionary of other barrel attributes
    for barrel in wholesale_catalog:
        insert_parameters.append({
            "sku" : barrel.sku,
            "ml_per_barrel" : barrel.ml_per_barrel,
            "potion_type": barrel.potion_type,
            "price" : barrel.price
        })

        if barrel.sku not in available_for_purchase:
            available_for_purchase[barrel.sku] = {"ml_per_barrel" : barrel.ml_per_barrel,
                                                  "potion_type": barrel.potion_type,
                                                  "price" : barrel.price,
                                                  "quantity" : barrel.quantity}

    # print("insert_parameters = ", insert_parameters)
    # print("available_for_purchase = ", available_for_purchase)

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO barrels_available_for_purchase (sku, ml_per_barrel, potion_type, price) SELECT :sku, :ml_per_barrel, :potion_type, :price WHERE NOT EXISTS (SELECT 1 FROM barrels_available_for_purchase WHERE sku = :sku)"), insert_parameters)

    #--- ---#

    #--- BARREL BUYING LOGIC ---#
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text(f"SELECT potion_sku, quantity FROM catalog WHERE quantity < 10")).mappings().fetchall()
        print("inventory = ", inventory)

        cur_liquid_inventory = connection.execute(sqlalchemy.text("SELECT SUM(num_ml) FROM liquid_inventory")).mappings().fetchone()
        print("cur_liquid_inventory = ", cur_liquid_inventory)

        cha_ching = connection.execute(sqlalchemy.text(f"SELECT gold FROM cha_ching")).mappings().fetchone()
        print("cha_ching = ", cha_ching)
        cur_gold = cha_ching["gold"]

        cur_capacity = connection.execute(sqlalchemy.text("SELECT potion_capacity, ml_capacity FROM storage_capacity")).mappings().fetchone()

    
    red_needed = green_needed = blue_needed = dark_needed = 0 

    for potion in inventory:
        if int(potion["potion_sku"][:3]) > 0:
            red_needed += (int(potion["potion_sku"][:3]) * (10 - potion["quantity"]))
        
        if int(potion["potion_sku"][4:7]) > 0:
            green_needed += (int(potion["potion_sku"][4:7]) * (10 - potion["quantity"]))

        if int(potion["potion_sku"][8:11]) > 0:
            blue_needed += (int(potion["potion_sku"][8:11]) * (10 - potion["quantity"]))
        
        if int(potion["potion_sku"][12:15]) > 0:
            dark_needed += (int(potion["potion_sku"][12:15]) * (10 - potion["quantity"]))

    print("red_needed = ", red_needed)
    print("green_needed = ", green_needed)
    print("blue_needed = ", blue_needed)
    print("dark_needed = ", dark_needed)

    # Python heapq does min-heap so negate numbers to essentially turn it into a max heap
    maxH = [(-red_needed, "RED"), (-green_needed, "GREEN"), (-blue_needed, "BLUE"), (-dark_needed, "DARK")]
    heapq.heapify(maxH)

    purchase_plan = []

    max_ml_capacity = 10000 * cur_capacity["ml_capacity"]
    while maxH and cur_liquid_inventory["sum"] <= max_ml_capacity:
        print("maxH = ", maxH)
        node = heapq.heappop(maxH)
        print("node = ", node)

        # LARGE
        if (f"LARGE_{node[1]}_BARREL" in available_for_purchase):
            if (cur_gold >= available_for_purchase[f"LARGE_{node[1]}_BARREL"]["price"]) and ((cur_liquid_inventory + available_for_purchase[f"LARGE_{node[1]}_BARREL"]["ml_per_barrel"]) <= max_ml_capacity):
                if available_for_purchase[f"LARGE_{node[1]}_BARREL"]["quantity"] >= 1:
                    purchase_plan.append({
                        "sku" : f"LARGE_{node[1]}_BARREL",
                        "quantity" : 1
                    })
                    # TODO: need to multiply price by quantity purchased when it becomes more than 1
                    cur_gold -= available_for_purchase[f"LARGE_{node[1]}_BARREL"]["price"]
                    cur_liquid_inventory += available_for_purchase[f"LARGE_{node[1]}_BARREL"]["ml_per_barrel"]
        # MEDIUM
        if (f"MEDIUM_{node[1]}_BARREL" in available_for_purchase):
            if (cur_gold >= available_for_purchase[f"MEDIUM_{node[1]}_BARREL"]["price"]) and ((cur_liquid_inventory + available_for_purchase[f"MEDIUM_{node[1]}_BARREL"]["ml_per_barrel"]) <= max_ml_capacity):
                if available_for_purchase[f"MEDIUM_{node[1]}_BARREL"]["quantity"] >= 1:
                    purchase_plan.append({
                        "sku" : f"MEDIUM_{node[1]}_BARREL",
                        "quantity" : 1
                    })
                    # TODO: need to multiply price by quantity purchased when it becomes more than 1
                    cur_gold -= available_for_purchase[f"MEDIUM_{node[1]}_BARREL"]["price"]
                    cur_liquid_inventory += available_for_purchase[f"MEDIUM_{node[1]}_BARREL"]["ml_per_barrel"]
        # SMALL
        if (f"SMALL_{node[1]}_BARREL" in available_for_purchase):
            if (cur_gold >= available_for_purchase[f"SMALL_{node[1]}_BARREL"]["price"]) and ((cur_liquid_inventory + available_for_purchase[f"SMALL_{node[1]}_BARREL"]["ml_per_barrel"]) <= max_ml_capacity):
                if available_for_purchase[f"SMALL_{node[1]}_BARREL"]["quantity"] >= 1:
                    purchase_plan.append({
                        "sku" : f"SMALL_{node[1]}_BARREL",
                        "quantity" : 1
                    })
                    # TODO: need to multiply price by quantity purchased when it becomes more than 1
                    cur_gold -= available_for_purchase[f"SMALL_{node[1]}_BARREL"]["price"]
                    cur_liquid_inventory += available_for_purchase[f"SMALL_{node[1]}_BARREL"]["ml_per_barrel"]

    print("purchase_plan = ", purchase_plan)

    #--- ---#
    
    return purchase_plan

