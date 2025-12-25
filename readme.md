資料夾結構：
YourProject/
├── .env
├── .gitignore
├── init.sql
├── import.py
├── connect.py
├── dropAll.sql
└── data/
    ├── student_info.csv
    ├── courses.csv
    └── ... (其餘 5 個 CSV)
    注意csv檔案的檔名要改成lower camel case，data資料夾、.env要自己新增

建構資料庫：
1. 連線到sql database
2. 新增一個.env檔，輸入你的postgres password，如下：
PASSWORD = 0000
3. 執行import.py(記得pip需要的py庫, student_registration匯入成功後要等一陣子是正常的) - 完成~