資料夾結構：
YourProject/
├── .env                # (需自行新增) 存放資料庫密碼
├── .gitignore
├── init.sql            # 資料庫初始化腳本
├── connect.py          # 資料庫連線測試
├── import.py           # 資料匯入腳本 (CSV -> DB)
├── main.py             # 核心後端程式 (FastAPI)
├── dropAll.sql         # 清除資料表用
├── static/             # (重要) 存放網頁前端檔案
│   ├── index.html      # 網頁主畫面
│   └── app.js          # 前端邏輯 (Fetch API)
└── data/               # (需自行新增) 存放 CSV 來源檔
    ├── studentInfo.csv # (注意) 檔名需改為 lowerCamelCase
    ├── courses.csv
    └── ...

建構資料庫：
1. 連線到sql database
2. 新增一個.env檔，輸入你的postgres password，如下：
PASSWORD = 0000
3. 執行import.py(記得pip需要的py庫, student_registration匯入成功後要等一陣子是正常的) - 完成~

安裝 Python 依賴庫
開啟終端機 (Terminal)，執行以下指令安裝所需套件：
pip install fastapi uvicorn psycopg2-binary python-dotenv pandas

先python import.py 會跳出
======== PostgreSQL CRUD CLI ========
1. Retrieve data
2. Retrieve data (sorted)
3. Add data
4. Update data
5. Delete data
6. Exit
然後關掉這個輸入uvicorn main:app --reload
當終端機顯示 Uvicorn running on http://127.0.0.1:8000 後
點網址就可以進去了
