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

# ==========================================
# 🚀 修改重點：設定 API 文件的標題
# ==========================================
app = FastAPI(title="成績計算與管理系統", description="用於管理成績資料庫的後端 API")

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

# 通用的更新模型
class UpdatePayload(BaseModel):
    data: Dict[str, Any]      
    conditions: Dict[str, Any] 

# 通用的新增模型
class CreatePayload(BaseModel):
    data: Dict[str, Any]

# 1. 取得所有表格名稱 (已加入過濾清單)
@app.get("/api/tables")
def get_tables():
    conn = get_db_connection()
    if not conn:
        return []
        
    cur = conn.cursor()
    # 查詢 public schema 下的所有 base table
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    all_tables = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()

    # 定義要「無視」的表格清單
    exclude_list = ['sqlite_sequence'] 

    # 過濾表格
    real_tables = [t for t in all_tables if t not in exclude_list]

    return real_tables

# 2. 取得指定表格的欄位資訊
@app.get("/api/columns/{table_name}")
def get_columns(table_name: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
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

# 3. 取得表格資料
@app.get("/api/data/{table_name}")
def get_data(table_name: str, sort_by: Optional[str] = None, order: str = "ASC"):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query_parts = [sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))]
    
    if sort_by:
        order_sql = sql.SQL("DESC") if order.upper() == "DESC" else sql.SQL("ASC")
        query_parts.append(sql.SQL("ORDER BY {}").format(sql.Identifier(sort_by)))
        query_parts.append(order_sql)
    
    query_parts.append(sql.SQL("LIMIT 100"))
    
    final_query = sql.SQL(" ").join(query_parts)
    
    try:
        cur.execute(final_query)
        rows = cur.fetchall()
        
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

# 5. 通用更新功能
@app.put("/api/data/{table_name}")
def update_data(table_name: str, payload: UpdatePayload):
    conn = get_db_connection()
    cur = conn.cursor()
    
    new_data = payload.data      
    conditions = payload.conditions 
    
    if not conditions:
        raise HTTPException(status_code=400, detail="無法更新：找不到原始資料對應條件")

    try:
        set_clause = sql.SQL(', ').join(
            sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()])
            for k in new_data.keys()
        )
        
        where_clause = sql.SQL(' AND ').join(
            sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()])
            for k in conditions.keys()
        )
        
        query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
            sql.Identifier(table_name),
            set_clause,
            where_clause
        )
        
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
@app.post("/api/data/{table_name}/delete")
def delete_data(table_name: str, payload: CreatePayload):
    conn = get_db_connection()
    cur = conn.cursor()
    
    conditions = payload.data
    
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