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
def askForTable():
    for i, name in enumerate(TABLE_LIST):
        print(f"{i + 1}. {name}")
    num = int(input("表格編號> ").strip())
    return TABLE_LIST[num - 1]

def get_columns(table_name):
    cur.execute(
        sql.SQL("SELECT * FROM {} LIMIT 0").format(
            sql.Identifier(table_name)
        )
    )
    return [desc[0] for desc in cur.description]


def retrieve_data():
    table = askForTable()
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

def retrieve_data_sorted():
    table = askForTable()
    cols = get_columns(table)

    print("\n選擇排序欄位：")
    print("0. 不排序")
    for i, c in enumerate(cols, 1):
        print(f"{i}. {c}")

    idx = int(input("欄位編號> "))
    order = input("排序方向 (ASC/DESC)> ").upper()

    if idx == 0:
        query = sql.SQL("SELECT * FROM {}").format(
            sql.Identifier(table)
        )
    else:
        query = sql.SQL(
            "SELECT * FROM {} ORDER BY {} {}"
        ).format(
            sql.Identifier(table),
            sql.Identifier(cols[idx - 1]),
            sql.SQL(order if order in ("ASC", "DESC") else "ASC")
        )

    cur.execute(query)
    rows = cur.fetchall()
    cols_name = [d[0] for d in cur.description]

    print(tabulate(rows, headers=cols_name, tablefmt="psql"))

def add_data():
    table = askForTable()
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
    table = askForTable()
    try:
        cols = get_columns(table)

        # 顯示欄位選單
        print("\n請選擇欄位：")
        for i, col in enumerate(cols, 1):
            print(f"{i}. {col}")

        # 選擇要更新的欄位
        set_idx = int(input("\n要更新的欄位編號> ")) - 1
        set_col = cols[set_idx]
        new_val = input("新值> ")

        # 選擇條件欄位
        where_idx = int(input("\n條件欄位編號> ")) - 1
        where_col = cols[where_idx]
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

    except (IndexError, ValueError):
        conn.rollback()
        print("❌ 請輸入正確的欄位編號\n")

    except Exception as e:
        conn.rollback()
        print("❌ 更新失敗:", e)

def delete_data():
    table = askForTable()
    try:
        cols = get_columns(table)
        for i, col in enumerate(cols, 1):
            print(f"{i}. {col}")
        where_idx = int(input("\n條件欄位編號> ")) - 1
        where_col = cols[where_idx]
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

    except (IndexError, ValueError):
        conn.rollback()
        print("❌ 請輸入正確的欄位編號\n")

    except Exception as e:
        conn.rollback()
        print("❌ 刪除失敗:", e)


# ========= 主選單 =========
def main():
    while True:
        print("""
======== PostgreSQL CRUD CLI ========
1. Retrieve data
2. Retrieve data (sorted)
3. Add data
4. Update data
5. Delete data
6. Exit
====================================
""")
        choice = input("Choose> ").strip()

        if choice == "1":
            retrieve_data()
        elif choice == "2":
            retrieve_data_sorted()
        elif choice == "3":
            add_data()
        elif choice == "4":
            update_data()
        elif choice == "5":
            delete_data()
        elif choice == "6":
            break
        else:
            print("❌ 無效選項\n")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()