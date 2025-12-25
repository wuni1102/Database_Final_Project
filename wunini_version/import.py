import os
import io
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. 載入環境變數
load_dotenv()
PASSWORD = os.getenv("PASSWORD")
DB_NAME = "final_project" 
# 使用 psycopg2 作為驅動程式以支援 raw_connection
engine = create_engine(f"postgresql+psycopg2://postgres:{PASSWORD}@localhost:5432/{DB_NAME}")

def init_db_schema():
    """執行 init.sql 建立資料表結構"""
    print("⏳ 正在初始化資料表結構...")
    try:
        with engine.connect() as conn:
            with open("init.sql", "r", encoding="utf-8") as f:
                sql_commands = f.read()
                conn.execute(text(sql_commands))
                conn.commit()
        print("🚀 Schema 建立成功！")
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")

def import_csv_data():
    """使用 PostgreSQL COPY 指令高效匯入資料"""
    data_order = [
        "courses",              
        "student_info",         
        "vle",                  
        "assessments",          
        "student_registration", 
        "student_vle",          
        "student_assessment"    
    ]
    
    print("📋 正在預載入 assessments 參考資料...")
    df_assess_bridge = pd.read_csv("data/assessments.csv")[['id_assessment', 'code_module', 'code_presentation']]

    # 建立原始連接
    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        print("⏳ 開始高效匯入資料 (COPY mode)...")
        
        for table_name in data_order:
            file_path = f"data/{table_name}.csv"
            if not os.path.exists(file_path):
                print(f"⚠️ 找不到檔案 {file_path}，跳過...")
                continue

            try:
                # 判斷是否需要用 Pandas 先處理欄位 (如 courses)
                if table_name == "courses":
                    df = pd.read_csv(file_path)
                    # 執行複合屬性拆分
                    df['presentation_year'] = df['code_presentation'].str[:4].astype(int)
                    df['presentation_month'] = df['code_presentation'].str[4:]
                    
                    df.to_sql(table_name, engine, if_exists="append", index=False)
                    # print(f"✅ {table_name} 匯入成功 (共 {len(df)} 筆)")
                
                elif table_name == "student_assessment":
                    # 核心邏輯：透過 Left Join 補全 code_module 與 code_presentation
                    df = pd.merge(df, df_assess_bridge, on='id_assessment', how='left')
                    output = io.StringIO()
                    # na_rep='' 確保輸出的流中，原本是空值的地方變成不帶引號的空位
                    df.to_csv(output, index=False, header=False, na_rep='') 
                    output.seek(0)
                    
                    sql = f"COPY {table_name} FROM STDIN WITH (FORMAT CSV, NULL '')"
                    cursor.copy_expert(sql, output)
                else:
                    # 讀取時將空字串與引號內的空值都視為 NaN
                    df = pd.read_csv(file_path, keep_default_na=True, na_values=[''])
                    
                    output = io.StringIO()
                    # na_rep='' 確保輸出的流中，原本是空值的地方變成不帶引號的空位
                    df.to_csv(output, index=False, header=False, na_rep='') 
                    output.seek(0)
                    
                    sql = f"COPY {table_name} FROM STDIN WITH (FORMAT CSV, NULL '')"
                    cursor.copy_expert(sql, output)
                
                print(f"✅ {table_name} 匯入完成！")
            
            except Exception as e:
                print(f"❌ {table_name} 匯入失敗: {e}")
                raw_conn.rollback() # 發生錯誤時回滾
        
        raw_conn.commit()
    finally:
        raw_conn.close()

def drop_all_tables():
    tables = [
        "student_registration", "student_vle", "student_assessment",
        "student_info", "courses", "vle", "assessments"
    ]
    with engine.connect() as conn:
        for table in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
            print(f"🗑️ 已刪除資料表: {table}")
        conn.commit()
    print("✨ 所有資料表已清空。")

if __name__ == "__main__":
    drop_all_tables()
    init_db_schema()
    import_csv_data()
    print("🎊 全部資料匯入流程完成！")