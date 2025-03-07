from contextlib import asynccontextmanager
import json
from typing import Dict
import fastapi
from fastapi.applications import HTMLResponse
from pydantic import BaseModel

class Todoitem(BaseModel):
    title: str
    description : str
    completed: bool = False


class FileRepository:
    
    def __init__(self,file_name="db.json" ):
        self.file = open(file_name,"+a")
        self.data : Dict[int,Todoitem] = {}
        self.index_counter = 0

    def load(self):
        self.file.seek(0)
        try:
            self.data = {int(k): Todoitem(**v) for k, v in json.load(self.file).items()}
        except json.JSONDecodeError:
            self.data = {}
        self.index_counter = len(self.data)

    def flush(self):
        self.file.seek(0)
        self.file.truncate()
        serialized_data = {k: v.model_dump() for k, v in self.data.items()}
        json.dump(serialized_data,self.file)

    

class TodoService:
    def __init__(self, repo: FileRepository):
        self.repo = repo
        self.repo.load()
        
    def get_all(self):
        return self.repo.data

    def add(self, item: Todoitem):
        new_item = Todoitem(index=len(self.repo.data), **item.model_dump())
        self.repo.index_counter += 1
        self.repo.data[self.repo.index_counter] = new_item
        return item

    def remove(self, index: int):
        try:
            item = self.repo.data.pop(index)
        except KeyError:
            return None
        return item

    def update(self, index: int, item: Todoitem):
        try:
            self.repo.data[index] = item
        except KeyError:
            return None
        return item
    

service: TodoService

@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    repo = FileRepository()
    global service
    service = TodoService(repo)
    yield
    repo.flush()
    repo.file.close()

app = fastapi.FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    with open("templates/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/todos")
def get_items():
    # serialize the data
    todos = service.get_all()
    serialized_data = []
    for id, todo in todos.items():
        data = todo.model_dump()
        data["id"] = id
        serialized_data.append(data)
    return serialized_data

    

@app.post("/todos")
def add_item(item: Todoitem):
    return service.add(item)

@app.delete("/todos/{index}")
def remove_item(index: int):
    return service.remove(index)

@app.put("/todos/{index}")
def update_item(index: int, item: Todoitem):
    return service.update(index, item)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)