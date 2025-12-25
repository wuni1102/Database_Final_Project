import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()
PASSWORD = os.getenv("PASSWORD")
DB_NAME = "final_project" 

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database=DB_NAME,
    user="postgres",
    password=PASSWORD
)

cur = conn.cursor()

print("輸入 table 名稱查詢（輸入 exit 離開）")

while True:
    table_name = input("Table name> ").strip()

    if table_name.lower() in ("exit", "quit"):
        break

    try:
        # 動態 table 名稱（安全寫法）
        query = sql.SQL("SELECT * FROM {}").format(
            sql.Identifier(table_name)
        )
        cur.execute(query)

        rows = cur.fetchall()

        # 取得欄位名稱
        col_names = [desc[0] for desc in cur.description]

        print("\n欄位名稱:")
        print(col_names)

        print("\n資料內容:")
        for row in rows:
            print(row)

        print("-" * 40)

    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        print("❌ Table 不存在")

    except Exception as e:
        conn.rollback()
        print("❌ 發生錯誤:", e)

cur.close()
conn.close()
