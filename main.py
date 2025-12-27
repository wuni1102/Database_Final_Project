from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import datetime

load_dotenv()

app = FastAPI()

# 資料庫連線
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="final_project", # 確認資料庫名稱
            user="postgres",
            password=os.getenv("PASSWORD")
        )
        return conn
    except Exception as e:
        print("DB Connection Error:", e)
        return None

# 通用的更新模型 (接收兩部分：要修改成的新資料 data，以及用來定位舊資料的條件 conditions)
class UpdatePayload(BaseModel):
    data: Dict[str, Any]      # SET 欄位 = 值
    conditions: Dict[str, Any] # WHERE 欄位 = 值 (原本的舊資料)

# 通用的新增模型
class CreatePayload(BaseModel):
    data: Dict[str, Any]

# 1. 取得所有表格名稱
@app.get("/api/tables")
def get_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    # 查詢 public schema 下的所有 base table
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return tables

# 2. 取得指定表格的欄位資訊 (包含是否為 PK)
@app.get("/api/columns/{table_name}")
def get_columns(table_name: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 這裡很關鍵：我們需要知道欄位名稱、型別，以及它是否是主鍵(PK)
    # 為了簡化，我們先只抓欄位名稱
    query = sql.SQL("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
    """)
    cur.execute(query, (table_name,))
    columns = cur.fetchall()
    
    cur.close()
    conn.close()
    return columns

# 3. 取得表格資料 (支援動態排序)
@app.get("/api/data/{table_name}")
def get_data(table_name: str, sort_by: Optional[str] = None, order: str = "ASC"):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 安全地構建 SQL 查詢
    query_parts = [sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))]
    
    if sort_by:
        # 決定升序或降序
        order_sql = sql.SQL("DESC") if order.upper() == "DESC" else sql.SQL("ASC")
        query_parts.append(sql.SQL("ORDER BY {}").format(sql.Identifier(sort_by)))
        query_parts.append(order_sql)
    
    query_parts.append(sql.SQL("LIMIT 100")) # 限制 100 筆避免網頁卡死
    
    final_query = sql.SQL(" ").join(query_parts)
    
    try:
        cur.execute(final_query)
        rows = cur.fetchall()
        
        # 處理日期物件，轉成字串以免前端看不懂
        for row in rows:
            for key, value in row.items():
                if isinstance(value, (datetime.date, datetime.datetime)):
                    row[key] = str(value)
                    
    except Exception as e:
        print(e)
        rows = []
        
    cur.close()
    conn.close()
    return rows

# 4. 通用新增功能
@app.post("/api/data/{table_name}")
def create_data(table_name: str, payload: CreatePayload):
    conn = get_db_connection()
    cur = conn.cursor()
    
    data = payload.data
    columns = list(data.keys())
    values = list(data.values())
    
    try:
        # 動態產生 INSERT INTO table (col1, col2) VALUES (%s, %s)
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table_name),
            sql.SQL(', ').join(map(sql.Identifier, columns)),
            sql.SQL(', ').join(sql.Placeholder() * len(values))
        )
        cur.execute(query, values)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "新增成功"}

# 5. 通用更新功能 (最複雜的部分)
@app.put("/api/data/{table_name}")
def update_data(table_name: str, payload: UpdatePayload):
    conn = get_db_connection()
    cur = conn.cursor()
    
    new_data = payload.data       # 要改成的新值
    conditions = payload.conditions # 舊的值 (用來找原本是哪一行)
    
    if not conditions:
        raise HTTPException(status_code=400, detail="無法更新：找不到原始資料對應條件")

    try:
        # 構建 SET 子句 (col1 = %s, col2 = %s)
        set_clause = sql.SQL(', ').join(
            sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()])
            for k in new_data.keys()
        )
        
        # 構建 WHERE 子句 (col1 = %s AND col2 = %s) 用舊資料鎖定行
        where_clause = sql.SQL(' AND ').join(
            sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()])
            for k in conditions.keys()
        )
        
        query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
            sql.Identifier(table_name),
            set_clause,
            where_clause
        )
        
        # 參數順序：SET 的值 + WHERE 的值
        params = list(new_data.values()) + list(conditions.values())
        
        cur.execute(query, params)
        conn.commit()
        
        if cur.rowcount == 0:
            return {"message": "更新失敗：找不到原始資料或資料未變動", "status": "failed"}
            
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "更新成功"}

# 6. 通用刪除功能
@app.post("/api/data/{table_name}/delete") # 這裡用 POST 比較方便傳 JSON body
def delete_data(table_name: str, payload: CreatePayload): # 借用 CreatePayload 因為結構一樣只傳 data
    conn = get_db_connection()
    cur = conn.cursor()
    
    conditions = payload.data # 這裡是傳入 "要刪除的那一行的所有資料" 作為條件
    
    try:
        where_clause = sql.SQL(' AND ').join(
            sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()])
            for k in conditions.keys()
        )
        
        query = sql.SQL("DELETE FROM {} WHERE {}").format(
            sql.Identifier(table_name),
            where_clause
        )
        
        cur.execute(query, list(conditions.values()))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "刪除成功"}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse('static/index.html')