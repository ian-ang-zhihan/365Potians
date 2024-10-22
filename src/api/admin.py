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
        connection.execute(sqlalchemy.text("UPDATE catalog SET quantity = 0"))
        connection.execute(sqlalchemy.text("UPDATE liquid_inventory SET num_ml = 0"))
        connection.execute(sqlalchemy.text("UPDATE cha_ching SET gold = 100"))
        connection.execute(sqlalchemy.text("UPDATE storage_capacity SET potion_capacity = 1, ml_capacity = 1"))
        connection.execute(sqlalchemy.text("TRUNCATE carts CASCADE"))

    return "OK"

