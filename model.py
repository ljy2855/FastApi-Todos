
from pydantic import BaseModel


class Todoitem(BaseModel):
    title: str
    description : str
    completed: bool = False