import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()
PASSWORD = os.getenv("PASSWORD")
DB_NAME = "final_project"
TABLE_LIST = ["assessments", "courses", "student_assessment",
              "student_info", "student_registration", "student_vle", "vle"]

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database=DB_NAME,
    user="postgres",
    password=PASSWORD
)

cur = conn.cursor()

# ========= 工具函式 =========
def printTableList():
    print(f"tables: {TABLE_LIST}")

def get_columns(table_name):
    cur.execute(
        sql.SQL("SELECT * FROM {} LIMIT 0").format(
            sql.Identifier(table_name)
        )
    )
    return [desc[0] for desc in cur.description]


def retrieve_data():
    printTableList()
    table = input("Table name> ").strip()
    try:
        query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
        cur.execute(query)

        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

        if not rows:
            print("（沒有資料）\n")
            return

        print()
        print(tabulate(rows, headers=cols, tablefmt="psql"))
        print()

    except Exception as e:
        conn.rollback()
        print("❌ 查詢失敗:", e)


def add_data():
    printTableList()
    table = input("Table name> ").strip()
    try:
        cols = get_columns(table)
        print("欄位:", cols)

        values = []
        for c in cols:
            values.append(input(f"{c}: "))

        query = sql.SQL(
            "INSERT INTO {} ({}) VALUES ({})"
        ).format(
            sql.Identifier(table),
            sql.SQL(', ').join(map(sql.Identifier, cols)),
            sql.SQL(', ').join(sql.Placeholder() * len(cols))
        )

        cur.execute(query, values)
        conn.commit()
        print("✅ 新增成功\n")

    except Exception as e:
        conn.rollback()
        print("❌ 新增失敗:", e)


def update_data():
    printTableList()
    table = input("Table name> ").strip()
    try:
        cols = get_columns(table)
        print("欄位:", cols)

        set_col = input("要更新的欄位> ")
        new_val = input("新值> ")

        where_col = input("條件欄位> ")
        where_val = input("條件值> ")

        query = sql.SQL(
            "UPDATE {} SET {} = %s WHERE {} = %s"
        ).format(
            sql.Identifier(table),
            sql.Identifier(set_col),
            sql.Identifier(where_col)
        )

        cur.execute(query, (new_val, where_val))
        conn.commit()
        print("✅ 更新完成\n")

    except Exception as e:
        conn.rollback()
        print("❌ 更新失敗:", e)


def delete_data():
    printTableList()
    table = input("Table name> ").strip()
    try:
        where_col = input("條件欄位> ")
        where_val = input("條件值> ")

        query = sql.SQL(
            "DELETE FROM {} WHERE {} = %s"
        ).format(
            sql.Identifier(table),
            sql.Identifier(where_col)
        )

        cur.execute(query, (where_val,))
        conn.commit()
        print("✅ 刪除完成\n")

    except Exception as e:
        conn.rollback()
        print("❌ 刪除失敗:", e)


# ========= 主選單 =========
def main():
    while True:
        print("""
======== PostgreSQL CRUD CLI ========
1. Retrieve data
2. Add data
3. Update data
4. Delete data
5. Exit
====================================
""")
        choice = input("Choose> ").strip()

        if choice == "1":
            retrieve_data()
        elif choice == "2":
            add_data()
        elif choice == "3":
            update_data()
        elif choice == "4":
            delete_data()
        elif choice == "5":
            break
        else:
            print("❌ 無效選項\n")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()