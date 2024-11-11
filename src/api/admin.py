from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    with db.engine.begin() as connection:
        """
        For v4:
        - Truncate relevant (ledger) tables
            - Potion entries
            - Barrel entries
            - cha_ching entries
            - capacity entries
            - Carts
            - Cart_items
        - For gold, insert one row with 100 gold, transaction type = "BASE"
        - For capacity, insert one row with 1 potion_cap & 1 ml_cap, transaction_type = "BASE"
        """

        connection.execute(sqlalchemy.text("TRUNCATE carts CASCADE"))
        connection.execute(sqlalchemy.text("TRUNCATE potion_entries, barrel_entries, cha_ching_entries, capacity_entries"))
        
        connection.execute(sqlalchemy.text("INSERT INTO cha_ching_entries (transaction_id, transaction_type, cha_change) VALUES (0, 'BASE', 100)"))

        connection.execute(sqlalchemy.text("INSERT INTO capacity_entries (transaction_id, transaction_type, potion_capacity, ml_capacity) VALUES (0, 'BASE', 1, 1)"))
        
        potion_population = """
                                INSERT INTO potion_entries (transaction_id, transaction_type, potion_type, potion_change) VALUES
                                (1, 'BASE', '{100, 0, 0, 0}', 0),
                                (1, 'BASE', '{0, 100, 0, 0}', 0),
                                (1, 'BASE', '{0, 0, 100, 0}', 0),
                                (1, 'BASE', '{0, 0, 0, 100}', 0),
                                (1, 'BASE', '{50, 50, 0, 0}', 0),
                                (1, 'BASE', '{50, 0, 50, 0}', 0),
                                (1, 'BASE', '{0, 50, 50, 0}', 0),
                                (1, 'BASE', '{25, 25, 25, 25}', 0);
                            """

        connection.execute(sqlalchemy.text(potion_population))

        barrel_population = """
                                INSERT INTO barrel_entries (transaction_id, transaction_type, potion_type, liquid_change) VALUES
                                (1, 'BASE', '{1, 0, 0, 0}', 0),
                                (1, 'BASE', '{0, 1, 0, 0}', 0),
                                (1, 'BASE', '{0, 0, 1, 0}', 0),
                                (1, 'BASE', '{0, 0, 0, 1}', 0);
                            """
        connection.execute(sqlalchemy.text(barrel_population))

    return "OK"

