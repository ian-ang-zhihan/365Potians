from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"

# TODO: convert this to a table in the database
cart_id = 0
carts = {} # {id : {item_sku : quantity}}

@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    global cart_id
    global carts

    cart_id += 1
    if cart_id not in carts:
        carts[cart_id] = {}

    for cart in carts.items():
        print(cart)

    return {
        "cart_id": cart_id
        }


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    global carts

    if cart_id in carts:
        carts[cart_id][item_sku] = cart_item.quantity

    for cart in carts.items():
        print(cart)

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print("cart_checkout.payment = ", cart_checkout.payment)
    
    global carts
    total_potions_bought = 0
    for potion in carts[cart_id].values():
        total_potions_bought += potion

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        gold_result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))

    # TODO: Need to check if you have enough potions in your inventory
    current_potion_inventory = result.fetchone().num_green_potions
    gold = gold_result.fetchone().gold

    if current_potion_inventory < total_potions_bought:
        return []
    # total_gold_paid = int(cart_checkout.payment)

    new_potion_inventory = current_potion_inventory - total_potions_bought
    gold += (50 * total_potions_bought)
    # new_gold = gold + total_gold_paid

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {new_potion_inventory}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold}"))

    # TODO: Update your database after they checkout for minus potions & add gold
    # TODO: you get the item sku & price from your catalog to compute the total

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": gold}
