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

    insert_parameters = []
    for customer in customers:
        insert_parameters.append({"customer_name" : customer.customer_name,
                                  "character_class" : customer.character_class,
                                  "level" : customer.level})
    
    sql_to_execute = "INSERT INTO customer_visits (customer_name, character_class, level) VALUES (:customer_name, :character_class, :level)"
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), insert_parameters)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    """
    {
  "customer_name": "Valiant Hadrian Ironhart",
  "character_class": "Paladin",
  "level": 5
    }
    """

    insert_parameters = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts DEFAULT VALUES RETURNING cart_id")).mappings()
        print("result = ", result)
        cart_id = result.fetchone()["cart_id"]
        print("cart_id = ", cart_id)
        insert_parameters.append({"cart_id" : cart_id,
                                  "customer_name" : new_cart.customer_name,
                                  "character_class" : new_cart.character_class})
        print("insert_parameter = ", insert_parameters)
        connection.execute(sqlalchemy.text("INSERT INTO customer_purchases (cart_id, customer_id) SELECT :cart_id, customer_visits.id FROM customer_visits WHERE customer_visits.customer_name = :customer_name AND customer_visits.character_class = :character_class"), insert_parameters)
        
        # TODO: instead of just identifying by name, try identifying by name, class & level

    return {
        "cart_id": cart_id
        }


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    print("cart_item = ", item_sku, cart_item)

    insert_parameters = []
    insert_parameters.append({
        "cart_id" : cart_id,
        "item_sku" : item_sku,
        "quantity" : cart_item.quantity
    })

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, catalog_id, potion_quantity) SELECT :cart_id, catalog_id, :quantity FROM catalog WHERE potion_sku = :item_sku"), insert_parameters)

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print("cart_checkout.payment = ", cart_checkout.payment)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT catalog.catalog_id, potion_price, cart_items.potion_quantity FROM cart_items JOIN catalog ON catalog.catalog_id = cart_items.catalog_id WHERE cart_id = :cart_id"), {"cart_id" : cart_id}).mappings().fetchall()
        print("result = ", result)

        
    total_potions_bought = 0
    revenue = 0
    catalog_update_parameters = []

    for item in result:
        total_potions_bought += item["potion_quantity"]
        revenue += (item["potion_price"] * item["potion_quantity"])

        catalog_update_parameters.append({"catalog_id" : item["catalog_id"],
                                          "potion_quantity" : item["potion_quantity"],
                                          "cart_id" : cart_id})
        
    print("catalog_update_parameters = ", catalog_update_parameters)

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE catalog SET quantity = catalog.quantity - :potion_quantity FROM cart_items WHERE catalog.catalog_id = :catalog_id AND cart_items.cart_id = :cart_id"), catalog_update_parameters)
        connection.execute(sqlalchemy.text("UPDATE cha_ching SET gold = gold + :revenue"), {"revenue" : revenue})

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": revenue}
