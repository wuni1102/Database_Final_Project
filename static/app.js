// 1. 讀取並顯示資料 (Read)
async function fetchCourses() {
    const tableBody = document.getElementById("course-table-body");
    tableBody.innerHTML = "<tr><td colspan='6' class='text-center'>⏳ 資料載入中...</td></tr>";

    try {
        // 呼叫後端 API
        const response = await fetch(`${API_URL}/courses`);
        const data = await response.json();

        tableBody.innerHTML = ""; // 清空表格

        data.forEach(course => {
            // 產生唯一的 ID，例如: input-AAA-2019J
            const uniqueId = `input-${course.code_module}-${course.code_presentation}`;

            const row = `
                <tr>
                    <td>${course.code_module}</td>
                    <td>${course.code_presentation}</td>
                    <td>${course.presentation_year}</td>
                    <td>${course.presentation_month}</td>
                    
                    <td>
                        <input type="number" 
                               id="${uniqueId}" 
                               class="form-control form-control-sm" 
                               value="${course.module_presentation_length}" 
                               style="width: 80px; margin: 0 auto;">
                    </td>
                    
                    <td>
                        <button class="btn btn-warning btn-sm" 
                            onclick="updateCourse('${course.code_module}', '${course.code_presentation}')">
                            ✏️ 更新
                        </button>
                        <button class="btn btn-danger btn-sm" 
                            onclick="deleteCourse('${course.code_module}', '${course.code_presentation}')">
                            🗑️ 刪除
                        </button>
                    </td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });

    } catch (error) {
        console.error(error);
        tableBody.innerHTML = "<tr><td colspan='6' class='text-danger text-center'>❌ 無法載入資料，請檢查後端</td></tr>";
    }
}

// 2. 更新資料 (Update)
async function updateCourse(code, sem) {
    // 透過剛剛產生的唯一 ID 找到那個輸入框
    const inputId = `input-${code}-${sem}`;
    const inputElement = document.getElementById(inputId);
    const newLength = inputElement.value; // 取得你輸入的新數字

    // 檢查是否有輸入
    if (!newLength) {
        alert("請輸入數值！");
        return;
    }

    try {
        // 送出 PUT 請求給後端
        const response = await fetch(`${API_URL}/courses/${code}/${sem}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ length: parseInt(newLength) })
        });

        const result = await response.json();

        if (response.ok) {
            alert("✅ 更新成功！");
            // 不用重新整理整個頁面，這樣體驗比較好，或者你可以呼叫 fetchCourses() 重整
            // fetchCourses(); 
        } else {
            alert("❌ 更新失敗: " + result.message);
        }
    } catch (error) {
        console.error("更新錯誤:", error);
        alert("❌ 連線錯誤");
    }
}