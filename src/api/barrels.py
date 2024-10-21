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

    with db.engine.begin() as connection:
        liquid_inventory = connection.execute(sqlalchemy.text(f"SELECT color, potion_type, num_ml FROM liquid_inventory")).mappings().fetchall()
        print("liquid_inventory = ", liquid_inventory)
        # result = connection.execute(sqlalchemy.text(f"SELECT num_green_ml, num_red_ml, num_blue_ml, gold FROM global_inventory")).mappings()
        # inventory = result.fetchone()

        cha_ching = connection.execute(sqlalchemy.text(f"SELECT gold FROM cha_ching")).mappings().fetchone()
        print("cha_ching = ", cha_ching)
        cur_gold = cha_ching["gold"]

    """
    SELECT color, potion_type, num_ml
    FROM liquid_inventory

    SELECT gold
    FROM cha_ching
    """
    
    # cur_green_ml = inventory["num_green_ml"]
    # cur_red_ml = inventory["num_red_ml"]
    # cur_blue_ml = inventory["num_blue_ml"]
    # cur_gold = inventory["gold"]

    liquid_update_parameters = []
    cost = 0

    for barrel in barrels_delivered:
        liquid_update_parameters.append({
            "new_ml" : barrel.ml_per_barrel * barrel.quantity,
            "potion_type" : barrel.potion_type
        })

        cost += barrel.price

    # for barrel in barrels_delivered:
    #     # Green
    #     if barrel.potion_type == [0, 1, 0, 0]:
    #         cur_green_ml += (barrel.ml_per_barrel * barrel.quantity)
    #         cur_gold -= barrel.price

    #     # Red
    #     if barrel.potion_type == [1, 0, 0, 0]:
    #         cur_red_ml += (barrel.ml_per_barrel * barrel.quantity)
    #         cur_gold -= barrel.price

    #     # Blue
    #     if barrel.potion_type == [0, 0, 1, 0]:
    #         cur_blue_ml += (barrel.ml_per_barrel * barrel.quantity)
    #         cur_gold -= barrel.price
        
    """
    UPDATE liquid_inventory
    SET num_ml = num_ml + :new_ml
    WHERE potion_type = :potion_type

    UPDATE cha_ching
    SET gold = gold - :cost
    """
    print("liquid_update_parameters = ", liquid_update_parameters)
    print("cost = ", cost)

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE liquid_inventory SET num_ml = num_ml + :new_ml WHERE potion_type = :potion_type"), liquid_update_parameters)
        connection.execute(sqlalchemy.text("UPDATE cha_ching SET gold = gold - :cost"), {"cost" : cost})
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {cur_green_ml}"))
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {cur_red_ml}"))
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {cur_blue_ml}"))
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {cur_gold}"))

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

    print("insert_parameters = ", insert_parameters)
    print("available_for_purchase = ", available_for_purchase)

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO barrels_available_for_purchase (sku, ml_per_barrel, potion_type, price) SELECT :sku, :ml_per_barrel, :potion_type, :price WHERE NOT EXISTS (SELECT 1 FROM barrels_available_for_purchase WHERE sku = :sku)"), insert_parameters)

    #--- ---#

    #--- BARREL BUYING LOGIC ---#
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text(f"SELECT potion_sku, quantity FROM catalog WHERE quantity < 10")).mappings().fetchall()
        print("inventory = ", inventory)

        cha_ching = connection.execute(sqlalchemy.text(f"SELECT gold FROM cha_ching")).mappings().fetchone()
        print("cha_ching = ", cha_ching)
        cur_gold = cha_ching["gold"]
    
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num_green_potions, num_red_potions, num_blue_potions, gold FROM global_inventory")).mappings()
    
    SELECT potion_sku, quantity
    FROM catalog
    WHERE quantity < 10


    1. get potions that have quantity < 10
    2. parse through the potion_sku to find out what colors make up that potion
        a. do we need to multiply by (10 - quantity)???
    3. add that to variables
    4. create a max heap to prioritize what barrel to buy
    5. use a for loop
        a. pop each node for each heap
            b. check ml with the offered barrels
                i. if ml_needed == dark and have enough gold, buy the large dark barrel
                ii. if ml_needed is <= 500 and have enough gold, buy the small
                iii. elif ml_needed is <= 2500 and have enough gold, buy the medium 

                OR

                i. if ml_needed == dark and have enough gold, buy the large dark barrel
                ii. elif have enough gold, buy the medium barrel for that color 
                iii. else buy the small barrel (but make sure you have enough gold)

            c. check if you have enough gold
        d. if you satisfy both conditions, append that barrel to the purchase_plan
        e. update your cur_gold
        f. update your cur_ml???
            might need to query the database to get this one and have as a temp variable??

    inventory = result.fetchone()
    green_potion_inventory = (inventory["num_green_potions"], "GREEN")
    red_potion_inventory = (inventory["num_red_potions"], "RED")
    blue_potion_inventory = (inventory["num_blue_potions"], "BLUE")

    gold_inventory = inventory["gold"]
    
    """
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
    print("maxH = ", maxH)

    purchase_plan = []

    # MIGHT WANT TO CONSIDER POPPING ONLY THE TOP PART OF THE MAX HEAP
    # THE AMOUNT NEEDED DOESN'T REALLY EVEN MATTER WHEN BUYING THE BARRELS. IT WAS MAINLY FOR FIGURING OUT WHICH ONE TO BUY FIRST SINCE IT'S A PRIORITY QUEUE
    # RIGHT NOW, IF YOU HAVE THE MONEY AND IT'S AVAILABLE, BUY A LARGE BARREL IF NOT A MEDIUM BARREL IF NOT A SMALL BARREL
    # THAT SHOULD HELP WITH THE DARK BARREL CASE AS WELL

    # TODO: WHEN BUYING LARGE POTIONS, YOU NEED TO CHECK IF YOU HAVE ENOUGH CAPACITY
    while maxH:
        node = heapq.heappop(maxH)
        # LARGE
        if (f"LARGE_{node[1]}_BARREL" in available_for_purchase):
            if (cur_gold >= available_for_purchase[f"LARGE_{node[1]}_BARREL"]["price"]):
                if available_for_purchase[f"LARGE_{node[1]}_BARREL"]["quantity"] >= 1:
                    purchase_plan.append({
                        "sku" : f"LARGE_{node[1]}_BARREL",
                        "quantity" : 1
                    })
                    # TODO: need to multiply price by quantity purchased when it becomes more than 1
                    cur_gold -= available_for_purchase[f"LARGE_{node[1]}_BARREL"]["price"]
        # MEDIUM
        elif (f"MEDIUM_{node[1]}_BARREL" in available_for_purchase):
            if (cur_gold >= available_for_purchase[f"MEDIUM_{node[1]}_BARREL"]["price"]):
                if available_for_purchase[f"MEDIUM_{node[1]}_BARREL"]["quantity"] >= 1:
                    purchase_plan.append({
                        "sku" : f"MEDIUM_{node[1]}_BARREL",
                        "quantity" : 1
                    })
                    # TODO: need to multiply price by quantity purchased when it becomes more than 1
                    cur_gold -= available_for_purchase[f"MEDIUM_{node[1]}_BARREL"]["price"]
        # SMALL
        elif (f"SMALL_{node[1]}_BARREL" in available_for_purchase):
            if (cur_gold >= available_for_purchase[f"SMALL_{node[1]}_BARREL"]["price"]):
                if available_for_purchase[f"SMALL_{node[1]}_BARREL"]["quantity"] >= 1:
                    purchase_plan.append({
                        "sku" : f"SMALL_{node[1]}_BARREL",
                        "quantity" : 1
                    })
                    # TODO: need to multiply price by quantity purchased when it becomes more than 1
                    cur_gold -= available_for_purchase[f"SMALL_{node[1]}_BARREL"]["price"]

    print("purchase_plan = ", purchase_plan)

    #--- ---#
    """
    min_available_potion = min(green_potion_inventory[0], red_potion_inventory[0], blue_potion_inventory[0])
    for p, c in [red_potion_inventory, blue_potion_inventory, green_potion_inventory]:
        if min_available_potion == p:
            min_available_color = c
    """

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
    
    """
    
    return purchase_plan

