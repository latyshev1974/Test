from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

app = FastAPI()

# Подключение к базе
conn = psycopg2.connect(
    host="pg-demo",
    port=5432,
    dbname="mydb",
    user="myuser",
    password="mypassword"
)

class NoteCreate(BaseModel):
    title: str
    content: str

@app.get("/")
def root():
    return {"message": "API работает! Попробуй /docs для документации"}

@app.get("/notes")
def get_notes():
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM notes ORDER BY created_at DESC")
        rows = cur.fetchall()
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()

@app.post("/notes")
def create_note(note: NoteCreate):
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "INSERT INTO notes (title, content) VALUES (%s, %s) RETURNING *",
            (note.title, note.content)
        )
        new_row = cur.fetchone()
        conn.commit()
        return new_row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()

@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Проверяем существование
        cur.execute("SELECT id FROM notes WHERE id = %s", (note_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Заметка не найдена")

        # Удаляем и возвращаем удалённые данные
        cur.execute("DELETE FROM notes WHERE id = %s RETURNING *", (note_id,))
        deleted_row = cur.fetchone()
        conn.commit()

        return {
            "message": "Заметка удалена",
            "deleted": deleted_row
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()

@app.put("/notes/{note_id}")
def update_note(note_id: int, note: NoteCreate):
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Проверяем, существует ли заметка
        cur.execute("SELECT id FROM notes WHERE id = %s", (note_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Заметка не найдена")

        # 2. Обновляем данные
        cur.execute(
            "UPDATE notes SET title = %s, content = %s WHERE id = %s RETURNING *",
            (note.title, note.content, note_id)
        )
        updated_row = cur.fetchone()
        conn.commit()

        return {
            "message": "Заметка обновлена",
            "updated": updated_row
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
