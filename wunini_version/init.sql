-- 1. courses：強實體
CREATE TABLE courses (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    presentation_year VARCHAR(45),
    presentation_month VARCHAR(45),
    module_presentation_length INT,
    PRIMARY KEY (code_module, code_presentation) -- 複合主鍵
);

-- 2. student_info：強實體
CREATE TABLE student_info (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_student INT,
    gender VARCHAR(3),
    region VARCHAR(45),
    highest_education VARCHAR(45),
    imd_band VARCHAR(45),
    age_band VARCHAR(16),
    num_of_prev_attempts INT,
    studied_credits INT,
    disability VARCHAR(3),
    final_result VARCHAR(45),
    -- 一個學生在不同課程有不同背景，故主鍵需包含課程資訊
    PRIMARY KEY (id_student, code_module, code_presentation), 
    FOREIGN KEY (code_module, code_presentation) REFERENCES courses(code_module, code_presentation)
);

-- 3. vle：強實體
CREATE TABLE vle (
    id_site INT PRIMARY KEY, -- 單一主鍵
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    activity_type VARCHAR(45),
    week_from REAL,
    week_to REAL,
    FOREIGN KEY (code_module, code_presentation) REFERENCES courses(code_module, code_presentation)
);

-- 4. assessments：強實體
CREATE TABLE assessments (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_assessment INT PRIMARY KEY, -- 單一主鍵
    assessment_type VARCHAR(45),
    date REAL,
    weight REAL,
    FOREIGN KEY (code_module, code_presentation) REFERENCES courses(code_module, code_presentation)
);

-- 5. student_registration：弱實體
CREATE TABLE student_registration (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_student INT,
    date_registration REAL,
    date_unregistration REAL,
    -- 根據實體關聯圖，由課程、學期、學生共同組成
    PRIMARY KEY (code_module, code_presentation, id_student), 
    -- 外鍵必須對應 student_info 的複合主鍵
    FOREIGN KEY (id_student, code_module, code_presentation) REFERENCES student_info(id_student, code_module, code_presentation) 
);

-- 6. student_vle：多對多關聯表
CREATE TABLE student_vle (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_student INT,
    id_site INT,
    date INT,
    sum_click INT,
    PRIMARY KEY (id_student, id_site, code_module, code_presentation), -- 考慮到學生跨課行為，加入課程資訊
    -- 外鍵必須對應 student_info 的複合主鍵
    FOREIGN KEY (id_student, code_module, code_presentation) REFERENCES student_info(id_student, code_module, code_presentation),
    FOREIGN KEY (id_site) REFERENCES vle(id_site)
);

-- 7. student_assessment：多對多關聯表
CREATE TABLE student_assessment (
    id_assessment INT,
    id_student INT,
    date_submitted INT,
    is_banked SMALLINT,
    score FLOAT,
    PRIMARY KEY (id_student, id_assessment), -- 學生對特定評量的分數
    -- 這裡的外鍵需要特別注意：由於 student_info 的 PK 是三項組合，
    -- 而 student_assessment 資料表通常只有 id_student，
    -- 為了維持外鍵約束，建議在資料表中加入 code_module, code_presentation 以匹配
    -- 或者將 student_info 的 PK 改回 id_student（前提是確保數據不會重複）
    -- 按照目前最嚴謹的架構，建議如下：
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    FOREIGN KEY (id_student, code_module, code_presentation) REFERENCES student_info(id_student, code_module, code_presentation),
    FOREIGN KEY (id_assessment) REFERENCES assessments(id_assessment)
);