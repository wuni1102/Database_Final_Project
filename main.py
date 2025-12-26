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
            database="final_project", # 請確認這是您最後成功的資料庫名稱
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

# ✅ 更新專用的模型：包含所有欄位
class UpdateItem(BaseModel):
    code_module: str
    code_presentation: str
    presentation_year: int
    presentation_month: str
    module_presentation_length: int

# 1. 取得所有課程
@app.get("/courses")
def get_courses(sort_by: str = "code_module", order: str = "ASC"):
    conn = get_db_connection()
    if not conn: return {"error": "DB Error"}
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
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

# 3. 更新課程 (✅ 修改版：可以更新所有欄位)
@app.put("/courses/{code}/{sem}")
def update_course(code: str, sem: str, item: UpdateItem):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 這裡會用 item 裡的新資料，去覆寫原本(code, sem) 的資料
        cur.execute("""
            UPDATE courses 
            SET code_module = %s,
                code_presentation = %s,
                presentation_year = %s,
                presentation_month = %s,
                module_presentation_length = %s
            WHERE code_module = %s AND code_presentation = %s
        """, (
            item.code_module, 
            item.code_presentation, 
            item.presentation_year, 
            item.presentation_month, 
            item.module_presentation_length,
            code, # WHERE 條件：舊代碼
            sem   # WHERE 條件：舊學期
        ))
        conn.commit()
        
        if cur.rowcount == 0:
            return {"message": "找不到該課程或資料未變動", "status": "failed"}

    except Exception as e:
        conn.rollback()
        print(f"Update Error: {e}")
        # 如果因為改了代碼導致和其他表格 (FK) 衝突，會回傳 400
        raise HTTPException(status_code=400, detail=f"更新失敗: {e}")
    finally:
        cur.close()
        conn.close()
        
    return {"message": "更新成功", "status": "success"}

# 4. 刪除課程
@app.delete("/courses/{code}/{sem}")
def delete_course(code: str, sem: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM courses WHERE code_module = %s AND code_presentation = %s", (code, sem))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Delete Error: {e}")
        raise HTTPException(status_code=400, detail=f"刪除失敗 (可能有關聯資料): {e}")
    finally:
        cur.close()
        conn.close()
    return {"message": "刪除成功"}

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse('static/index.html')