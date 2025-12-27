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
import math

load_dotenv()

# 設定 API 文件標題
app = FastAPI(title="成績計算與管理系統", description="用於管理成績資料庫的後端 API")

# 資料庫連線
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="final_project", # 請確認資料庫名稱
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

# 1. 取得所有表格名稱 (含過濾功能)
@app.get("/api/tables")
def get_tables():
    conn = get_db_connection()
    if not conn:
        return []
    
    cur = conn.cursor()
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

    # 過濾清單：隱藏不想顯示的表格
    exclude_list = ['sqlite_sequence'] 
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

# ==========================================
# 3. 取得表格資料 (🚀 核心修改：截斷 1000 筆 + 分頁)
# ==========================================
@app.get("/api/data/{table_name}")
def get_data(
    table_name: str, 
    sort_by: Optional[str] = None, 
    order: str = "ASC",
    page: int = 1,      
    limit: int = 100    # 預設每頁 100 筆
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 🔴 硬性限制：最多只看前 1000 筆
    HARD_LIMIT_RECORDS = 1000
    
    # 計算 OFFSET
    offset = (page - 1) * limit

    # 如果請求的資料起點已經超過 1000 筆，直接回傳空值
    if offset >= HARD_LIMIT_RECORDS:
        cur.close()
        conn.close()
        return {
            "data": [],
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total_count": HARD_LIMIT_RECORDS,
                "total_pages": math.ceil(HARD_LIMIT_RECORDS / limit)
            }
        }

    # 如果讀取的範圍會超過 1000，強制把 limit 縮小 (例如讀到第 950 筆時，limit 剩 50)
    if offset + limit > HARD_LIMIT_RECORDS:
        limit = HARD_LIMIT_RECORDS - offset

    try:
        # --- 步驟 1: 算總筆數 (但在這裡我們最多只回報 1000) ---
        count_query = sql.SQL("SELECT COUNT(*) as count FROM {}").format(sql.Identifier(table_name))
        cur.execute(count_query)
        real_count = cur.fetchone()['count']
        
        # 這裡取最小值：如果資料庫只有 50 筆，就顯示 50；如果有 5000 筆，只顯示 1000
        effective_count = min(real_count, HARD_LIMIT_RECORDS)

        # --- 步驟 2: 抓取資料 ---
        query_parts = [sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))]
        
        if sort_by:
            order_sql = sql.SQL("DESC") if order.upper() == "DESC" else sql.SQL("ASC")
            query_parts.append(sql.SQL("ORDER BY {}").format(sql.Identifier(sort_by)))
            query_parts.append(order_sql)
        
        # 使用計算過後的安全 limit
        query_parts.append(sql.SQL("LIMIT {} OFFSET {}").format(sql.Literal(limit), sql.Literal(offset)))
        
        final_query = sql.SQL(" ").join(query_parts)
        
        cur.execute(final_query)
        rows = cur.fetchall()
        
        # 日期轉字串
        for row in rows:
            for key, value in row.items():
                if isinstance(value, (datetime.date, datetime.datetime)):
                    row[key] = str(value)
        
        # 計算總頁數 (基於截斷後的 1000 筆來算)
        # 如果 limit 是 100，effective_count 是 1000，那 total_pages 就是 10
        # 加上 max(1, ...) 避免除以 0 錯誤
        current_limit = 100 if limit == 0 else limit # 防止 limit 被縮減成 0 後計算頁數錯誤，這裡僅作顯示用
        total_pages = math.ceil(effective_count / 100) # 這裡稍微 tricky：總頁數應該基於「前端設定的每頁筆數」來算，但為了簡化，我們先用 100 或前端傳來的原始 limit
        
        # 更精準的總頁數計算：應該用 payload 裡的原始 limit (但這裡已經被修改了)
        # 簡單做法：直接回傳計算結果
        calc_limit = limit if limit > 0 else 100
        total_pages = math.ceil(effective_count / calc_limit)

        # 修正：因為我們動態調整了 limit (例如最後一頁 limit 變小)，導致計算總頁數可能怪怪的
        # 最穩妥的方式是：前端傳來的 limit 預設是 100，我們用 effective_count / 100 來算
        # 但為了通用性，我們回傳時統一用 effective_count
        
        # 重新計算標準總頁數 (假設每頁 100)
        standard_limit = 100
        display_total_pages = math.ceil(effective_count / standard_limit)

        return {
            "data": rows,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total_count": effective_count,
                "total_pages": display_total_pages 
            }
        }

    except Exception as e:
        print(e)
        return {"data": [], "pagination": {"current_page": 1, "total_count": 0, "total_pages": 0}}
        
    finally:
        cur.close()
        conn.close()

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