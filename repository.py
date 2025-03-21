from abc import ABC, abstractmethod
import json
import sqlite3
from typing import Dict
from model import Todoitem


class Repository(ABC):
    data: Dict[int, Todoitem]
    index_counter: int

    @abstractmethod
    def load(self) -> None:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass

    @abstractmethod
    def add(self, item: Todoitem):
        pass

    @abstractmethod
    def remove(self, index: int):
        pass

    @abstractmethod
    def update(self, index: int, item: Todoitem):
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class FileRepository(Repository):
    def __init__(self, file_name="db.json"):
        self.file = open(file_name, "+a")
        self.data: Dict[int, Todoitem] = {}
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
        json.dump(serialized_data, self.file)

    def add(self, item: Todoitem):
        self.index_counter += 1
        self.data[self.index_counter] = item
        return item

    def remove(self, index: int):
        return self.data.pop(index, None)

    def update(self, index: int, item: Todoitem):
        if index in self.data:
            self.data[index] = item
            return item
        return None

    def close(self):
        self.file.close()

class SQLiteRepository(Repository):
    def __init__(self, db_path="sqlite.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.data: Dict[int, Todoitem] = {}
        self.index_counter = 0
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                completed BOOLEAN NOT NULL CHECK (completed IN (0, 1))
            )
        ''')
        self.conn.commit()

    def load(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, description, completed FROM todos")
        rows = cursor.fetchall()
        self.data = {
            row[0]: Todoitem(title=row[1], description=row[2], completed=bool(row[3]))
            for row in rows
        }
        self.index_counter = max(self.data.keys(), default=0)

    def flush(self):
        pass  

    def add(self, item: Todoitem):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)",
            (item.title, item.description, item.completed)
        )
        self.conn.commit()
        item_id = cursor.lastrowid
        self.data[item_id] = item
        self.index_counter = max(self.index_counter, item_id)
        return item

    def remove(self, index: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM todos WHERE id = ?", (index,))
        self.conn.commit()
        return self.data.pop(index, None)

    def update(self, index: int, item: Todoitem):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
            (item.title, item.description, item.completed, index)
        )
        self.conn.commit()
        if cursor.rowcount > 0:
            self.data[index] = item
            return item
        return None

    def close(self):
        self.conn.close()
