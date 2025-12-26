const API_URL = "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
    fetchCourses();
});

// 1. Retrieve & Sort
async function fetchCourses() {
    const sortValue = document.getElementById("sortSelect").value;
    const orderValue = document.getElementById("orderSelect").value; // 新增排序方向
    const tableBody = document.getElementById("course-table-body");
    
    tableBody.innerHTML = "<tr><td colspan='6' class='text-center'>⏳ 載入中...</td></tr>";

    try {
        // 傳送 sort_by 和 order 給後端
        const response = await fetch(`${API_URL}/courses?sort_by=${sortValue}&order=${orderValue}`);
        const data = await response.json();

        tableBody.innerHTML = "";
        data.forEach(course => {
            const row = `
                <tr>
                    <td><strong>${course.code_module}</strong></td>
                    <td>${course.code_presentation}</td>
                    <td>${course.presentation_year}</td>
                    <td>${course.presentation_month}</td>
                    <td>
                        <input type="number" class="form-control form-control-sm" 
                               value="${course.module_presentation_length}" 
                               id="len-${course.code_module}-${course.code_presentation}" style="width: 80px;">
                    </td>
                    <td>
                        <button class="btn btn-sm btn-warning me-1" 
                            onclick="updateCourse('${course.code_module}', '${course.code_presentation}')">✏️ 更新</button>
                        <button class="btn btn-sm btn-danger" 
                            onclick="deleteCourse('${course.code_module}', '${course.code_presentation}')">🗑️ 刪除</button>
                    </td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    } catch (error) {
        console.error(error);
        tableBody.innerHTML = "<tr><td colspan='6' class='text-danger'>❌ 連線失敗</td></tr>";
    }
}

// 2. Add
async function createCourse() {
    const newCourse = {
        code_module: document.getElementById("newCode").value.toUpperCase(),
        code_presentation: document.getElementById("newSem").value,
        presentation_year: parseInt(document.getElementById("newYear").value),
        presentation_month: document.getElementById("newMonth").value,
        module_presentation_length: parseInt(document.getElementById("newLen").value)
    };

    if (!newCourse.code_module || !newCourse.code_presentation) return alert("❌ 請輸入代碼與學期");

    try {
        const response = await fetch(`${API_URL}/courses`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newCourse)
        });
        if (response.ok) { alert("✅ 新增成功"); fetchCourses(); }
        else { const err = await response.json(); alert("❌ 失敗: " + err.detail); }
    } catch (e) { alert("❌ 錯誤: " + e); }
}

// 3. Update
async function updateCourse(code, sem) {
    const newLength = document.getElementById(`len-${code}-${sem}`).value;
    try {
        const response = await fetch(`${API_URL}/courses/${code}/${sem}?length=${newLength}`, { method: "PUT" });
        if (response.ok) { alert("✅ 更新成功"); fetchCourses(); }
        else { alert("❌ 更新失敗"); }
    } catch (e) { alert("❌ 錯誤: " + e); }
}

// 4. Delete
async function deleteCourse(code, sem) {
    if (!confirm("⚠️ 確定刪除？")) return;
    try {
        const response = await fetch(`${API_URL}/courses/${code}/${sem}`, { method: "DELETE" });
        if (response.ok) { alert("✅ 刪除成功"); fetchCourses(); }
        else { alert("❌ 刪除失敗"); }
    } catch (e) { alert("❌ 錯誤: " + e); }
}