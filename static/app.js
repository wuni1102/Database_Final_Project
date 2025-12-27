const API_URL = "http://127.0.0.1:8000";

// ✅ 1. 讀取並顯示資料 (Read)
async function fetchCourses() {
    const tableBody = document.getElementById("course-table-body");
    
    // 取得排序設定 (對應你的 HTML 下拉選單)
    const sortBy = document.getElementById("sortSelect").value;
    const order = document.getElementById("orderSelect").value;

    tableBody.innerHTML = "<tr><td colspan='6' class='text-center'>⏳ 資料載入中...</td></tr>";

    try {
        // 將排序參數帶入網址
        const response = await fetch(`${API_URL}/courses?sort_by=${sortBy}&order=${order}`);
        const data = await response.json();

        tableBody.innerHTML = ""; // 清空表格

        if (data.length === 0) {
            tableBody.innerHTML = "<tr><td colspan='6' class='text-center'>資料庫是空的</td></tr>";
            return;
        }

        data.forEach(course => {
            const uniqueId = `input-${course.code_module}-${course.code_presentation}`;
            
            const row = `
                <tr>
                    <td>${course.code_module}</td>
                    <td>${course.code_presentation}</td>
                    <td>${course.presentation_year}</td>
                    <td>${course.presentation_month}</td>
                    <td>
                        <input type="number" id="${uniqueId}" class="form-control form-control-sm mx-auto" 
                               value="${course.module_presentation_length}" style="width: 80px;">
                    </td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="updateCourse('${course.code_module}', '${course.code_presentation}')">✏️ 更新</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteCourse('${course.code_module}', '${course.code_presentation}')">🗑️ 刪除</button>
                    </td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });

    } catch (error) {
        console.error("載入失敗:", error);
        tableBody.innerHTML = `<tr><td colspan='6' class='text-danger text-center'>❌ 無法載入資料 (請確認後端已啟動)</td></tr>`;
    }
}

// ✅ 2. 新增課程 (Create) - 對應你的 HTML 輸入框
async function createCourse() {
    const code = document.getElementById("newCode").value;
    const sem = document.getElementById("newSem").value;
    const year = document.getElementById("newYear").value;
    const month = document.getElementById("newMonth").value;
    const length = document.getElementById("newLen").value;

    if (!code || !sem || !year || !month || !length) {
        alert("⚠️ 所有欄位都必須填寫！");
        return;
    }

    const newCourse = {
        code_module: code,
        code_presentation: sem,
        presentation_year: parseInt(year),
        presentation_month: month,
        module_presentation_length: parseInt(length)
    };

    try {
        const response = await fetch(`${API_URL}/courses`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newCourse)
        });

        if (response.ok) {
            alert("✅ 新增成功！");
            fetchCourses(); // 重新整理
            // 清空輸入框
            document.getElementById("newCode").value = "";
            document.getElementById("newSem").value = "";
        } else {
            const result = await response.json();
            alert("❌ 新增失敗: " + (result.detail || "未知錯誤"));
        }
    } catch (error) {
        console.error(error);
        alert("❌ 連線錯誤");
    }
}

// ✅ 3. 更新資料 (Update)
async function updateCourse(code, sem) {
    const inputId = `input-${code}-${sem}`;
    const newLength = document.getElementById(inputId).value;

    if (!newLength) { alert("請輸入數值"); return; }

    try {
        const response = await fetch(`${API_URL}/courses/${code}/${sem}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ length: parseInt(newLength) })
        });
        
        if (response.ok) {
            alert("✅ 更新成功！");
            fetchCourses();
        } else {
            alert("❌ 更新失敗");
        }
    } catch (error) {
        alert("❌ 連線錯誤");
    }
}

// ✅ 4. 刪除資料 (Delete)
async function deleteCourse(code, sem) {
    if (!confirm(`確定要刪除 ${code} ${sem} 嗎？`)) return;

    try {
        const response = await fetch(`${API_URL}/courses/${code}/${sem}`, { method: "DELETE" });
        if (response.ok) {
            alert("🗑️ 刪除成功");
            fetchCourses();
        } else {
            alert("❌ 刪除失敗");
        }
    } catch (error) {
        alert("❌ 連線錯誤");
    }
}

// 👇👇👇 最重要的一行：網頁載入後自動執行！ 👇👇👇
document.addEventListener("DOMContentLoaded", fetchCourses);