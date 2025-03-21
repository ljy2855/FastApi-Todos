from contextlib import asynccontextmanager
from typing import Dict
import fastapi
from fastapi.applications import HTMLResponse

from repository import FileRepository, SQLiteRepository, Repository
from model import Todoitem


class TodoService:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.repo.load()

    def get_all(self) -> Dict[int, Todoitem]:
        return self.repo.data

    def add(self, item: Todoitem):
        added = self.repo.add(item)
        # SQLite는 id를 자동생성하므로 data에 있는 최신 ID를 찾아야 함
        if hasattr(self.repo, "index_counter"):
            item_id = self.repo.index_counter
        else:
            item_id = max(self.repo.data.keys())
        return {**item.model_dump(), "id": item_id}

    def remove(self, index: int):
        result = self.repo.remove(index)
        return {"success": result is not None}

    def update(self, index: int, item: Todoitem):
        result = self.repo.update(index, item)
        return {"success": result is not None}

    def close(self):
        self.repo.flush()
        self.repo.close()
    

service: TodoService



@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    repo = SQLiteRepository()  # 또는 FileRepository()
    global service
    service = TodoService(repo)
    yield
    service.close()

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
