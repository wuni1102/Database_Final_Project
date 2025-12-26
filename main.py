from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# 資料庫連線
def get_db_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            database="final_project", # 請確認您的資料庫名稱
            user="postgres",
            password=os.getenv("PASSWORD")
        )
    except Exception as e:
        print("DB Connection Error:", e)
        return None

# Pydantic 模型 (用來接收新增資料)
class Course(BaseModel):
    code_module: str
    code_presentation: str
    presentation_year: int
    presentation_month: str
    module_presentation_length: int

# 1. 取得所有課程 (支援排序)
@app.get("/courses")
def get_courses(sort_by: str = "code_module", order: str = "ASC"):
    conn = get_db_connection()
    if not conn: return {"error": "DB Error"}
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # ⚠️ 為了安全，限制只能針對特定欄位排序
    allowed_sorts = ["code_module", "presentation_year", "module_presentation_length"]
    if sort_by not in allowed_sorts: sort_by = "code_module"
    if order not in ["ASC", "DESC"]: order = "ASC"

    query = f"SELECT * FROM courses ORDER BY {sort_by} {order} LIMIT 100;"
    cur.execute(query)
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    return rows

# 2. 新增課程
@app.post("/courses")
def create_course(course: Course):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO courses (code_module, code_presentation, presentation_year, presentation_month, module_presentation_length)
            VALUES (%s, %s, %s, %s, %s)
        """, (course.code_module, course.code_presentation, course.presentation_year, course.presentation_month, course.module_presentation_length))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "新增成功"}

# 3. 更新課程長度
@app.put("/courses/{code}/{sem}")
def update_course(code: str, sem: str, length: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE courses 
        SET module_presentation_length = %s 
        WHERE code_module = %s AND code_presentation = %s
    """, (length, code, sem))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "更新成功"}

# 4. 刪除課程
@app.delete("/courses/{code}/{sem}")
def delete_course(code: str, sem: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM courses WHERE code_module = %s AND code_presentation = %s", (code, sem))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "刪除成功"}

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse('static/index.html')