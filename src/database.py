import os
import dotenv
from sqlalchemy import create_engine, MetaData, Table

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

# print(database_connection_url())

metadata = MetaData()
engine = create_engine(database_connection_url(), pool_pre_ping=True)

cart_items = Table("cart_items", metadata, autoload_with = engine)
catalog = Table("catalog", metadata, autoload_with = engine)
customer_purchases = Table("customer_purchases", metadata, autoload_with = engine)
customer_profiles = Table("customer_profiles", metadata, autoload_with = engine)

# print("cart_items.c = ", cart_items.c)
# print("cart_items.c.keys() = ", cart_items.c.keys())

# print("catalog.c = ", catalog.c)
# print("catalog.c.keys() = ", catalog.c.keys())

# print("customer_purchases.c = ", customer_purchases.c)
# print("customer_purchases.c.keys() = ", customer_purchases.c.keys())

# print("customer_profiles.c = ", customer_profiles.c)
# print("customer_profiles.c.keys() = ", customer_profiles.c.keys())