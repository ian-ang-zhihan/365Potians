from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from sqlalchemy import Table, desc, asc
from src import database as db
# from database import cart_items, catalog, customer_purchases, customer_profiles

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
    search_page: str = "1",
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
    results_per_page = 5

    # Log input
    print("customer_name = ", customer_name)
    print("potion_sku = ", potion_sku)
    print("search_page = ", search_page)
    print("sort_col = ", sort_col)
    print("sort_order = ", sort_order)

    search_items = db.cart_items.join(
                                db.catalog, db.cart_items.c.catalog_id == db.catalog.c.catalog_id
                            ).join(
                                db.customer_purchases, db.customer_purchases.c.cart_id == db.cart_items.c.cart_id
                            ).join(
                                db.customer_profiles, db.customer_purchases.c.customer_id == db.customer_profiles.c.id
                            )
    
    # print("search_items.c = ", search_items.c)
    # print("search_items.c.keys() = ", search_items.c.keys())

    query = sqlalchemy.select(
                    search_items.c.cart_items_cart_item_id,
                    search_items.c.catalog_potion_name,
                    search_items.c.customer_profiles_customer_name,
                    (search_items.c.cart_items_potion_quantity * search_items.c.catalog_potion_price).label("line_item_total"),
                    search_items.c.customer_purchases_created_at.label("timestamp")
                ).distinct().select_from(search_items)

    # Apply filters 
    if customer_name:
        query = query.where(search_items.c.customer_profiles_customer_name.ilike(f"%{customer_name}%"))
    if potion_sku:
        query = query.where(search_items.c.catalog_potion_name.ilike(f"%{potion_sku}%"))

    # Apply sorting
    query = query.order_by(desc(sort_col.value) if sort_order.value == "desc" else asc(sort_col.value))

    # Pagination setup
    offset = (int(search_page) - 1) * results_per_page if search_page else 0

    query = query.limit(results_per_page + 1).offset(offset)
    # print("query = ", query)
    
    try:
        with db.engine.begin() as connection:
                results = connection.execute(query).fetchall()
    except Exception as e:
        print(e)
        return {"previous": "", "next": "", "results": []}

    print("len(results) = ", len(results))

    # Pagination tokens
    if search_page:
        prev = str(int(search_page) - 1) if int(search_page) > 1 else ""
        next = str(int(search_page) + 1) if len(results) > results_per_page else ""
    else:
        prev = next = ""

    items = results[:results_per_page] if len(results) > results_per_page else results
    # print("items = ", items)
    
    results_data = []
    for item in items:
        results_data.append(
            {
                "line_item_id": item.cart_item_id,
                "item_sku": item.potion_name,
                "customer_name": item.customer_name,
                "line_item_total": item.line_item_total,
                "timestamp": item.timestamp,
            }
        )

    print("prev = ", prev)
    print("next = ", next)
    print("results_data = ", results_data)
    print("len(results_data) = ", len(results_data))

    """
    SELECT cart_item_id, catalog.potion_name, customer_profiles.customer_name, cart_items.potion_quantity * catalog.potion_price AS line_item_total, customer_purchases.created_at AS timestamp
    FROM cart_items
    JOIN catalog ON cart_items.catalog_id = catalog.catalog_id
    JOIN customer_purchases ON customer_purchases.cart_id = cart_items.cart_id
    JOIN customer_profiles ON customer_purchases.customer_id = customer_profiles.id
    WHERE 
        customer_profiles.customer_name = :customer_name
        AND
        catalog.potion_name = :potion_sku
    ORDER BY :sort_col :sort_order
    OFFSET :search_page
    LIMIT 5

    [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ]
    """

    return {
        "previous": prev,
        "next": next,
        "results": results_data
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
    

    with db.engine.begin() as connection:
        # Log customer visits
        connection.execute(sqlalchemy.text("INSERT INTO customer_visits (customer_name, character_class, level) VALUES (:customer_name, :character_class, :level)"), insert_parameters)

        # Log customer profiles
        sql_to_execute = """
                            INSERT INTO customer_profiles (customer_name, character_class, level) 
                            SELECT :customer_name, :character_class, :level 
                            WHERE NOT EXISTS 
                                (
                                    SELECT 1 
                                    FROM customer_profiles 
                                    WHERE customer_name = :customer_name AND character_class = :character_class AND level = :level
                                )
                         """
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
        cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts DEFAULT VALUES RETURNING cart_id")).mappings().fetchone()["cart_id"]

        print("cart_id = ", cart_id)
        insert_parameters.append({"cart_id" : cart_id,
                                  "customer_name" : new_cart.customer_name,
                                  "character_class" : new_cart.character_class,
                                  "level" : new_cart.level})
        print("insert_parameter = ", insert_parameters)

        sql_to_execute = """
                            INSERT INTO customer_purchases (cart_id, customer_id) 
                            SELECT :cart_id, customer_profiles.id 
                            FROM customer_profiles WHERE customer_name = :customer_name AND character_class = :character_class AND level = :level
                         """
        connection.execute(sqlalchemy.text(sql_to_execute), insert_parameters)

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
        sql_to_execute = """
                            INSERT INTO cart_items (cart_id, catalog_id, potion_quantity) 
                            SELECT :cart_id, catalog_id, :quantity 
                            FROM catalog 
                            WHERE potion_sku = :item_sku
                         """
        connection.execute(sqlalchemy.text(sql_to_execute), insert_parameters)

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print("cart_checkout.payment = ", cart_checkout.payment)

    """
    
    """
    with db.engine.begin() as connection:
        sql_to_execute = """
                            SELECT potion_type, potion_price, cart_items.potion_quantity
                            FROM cart_items
                            JOIN catalog ON catalog.catalog_id = cart_items.catalog_id
                            WHERE cart_id = :cart_id
                         """
        result = connection.execute(sqlalchemy.text(sql_to_execute), {"cart_id" : cart_id}).mappings().fetchall()
        print("result = ", result)

        
    total_potions_bought = 0
    revenue = 0
    potion_update_parameters = []

    for item in result:
        total_potions_bought += item["potion_quantity"]
        revenue += (item["potion_price"] * item["potion_quantity"])
        
        potion_update_parameters.append(
            {
                "transaction_id" : cart_id,
                "transaction_type" : "POTION_SALE",
                "potion_type" : item["potion_type"],
                "potion_change" : -item["potion_quantity"]
            }
        )
        
    print("potion_update_parameters = ", potion_update_parameters)

    cha_ching_parameters = {
        "transaction_id" : cart_id,
        "transaction_type" : "POTION_SALE",
        "revenue" : revenue
    }

    with db.engine.begin() as connection:
        sql_to_execute = """
                            INSERT INTO potion_entries (transaction_id, transaction_type, potion_type, potion_change) VALUES
                            (:transaction_id, :transaction_type, :potion_type, :potion_change)
                         """
        connection.execute(sqlalchemy.text(sql_to_execute), potion_update_parameters)
        
        sql_to_execute = """
                            INSERT INTO cha_ching_entries (transaction_id, transaction_type, cha_change) VALUES 
                            (:transaction_id, :transaction_type, :revenue)
                         """
        connection.execute(sqlalchemy.text(sql_to_execute), cha_ching_parameters)

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": revenue}
