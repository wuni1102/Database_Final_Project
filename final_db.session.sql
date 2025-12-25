-- 1. Courses (修正：加入 module_presentation_length)
CREATE TABLE courses (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    module_presentation_length INTEGER, 
    PRIMARY KEY (code_module, code_presentation)
);

-- 2. Assessments (順序符合 CSV)
CREATE TABLE assessments (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_assessment INTEGER,
    assessment_type VARCHAR(45),
    date INTEGER,
    weight INTEGER,
    PRIMARY KEY (id_assessment),
    FOREIGN KEY (code_module, code_presentation) REFERENCES courses(code_module, code_presentation)
);

-- 3. Vle (順序符合 CSV)
CREATE TABLE vle (
    id_site INTEGER,
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    activity_type VARCHAR(45),
    week_from INTEGER,
    week_to INTEGER,
    PRIMARY KEY (id_site),
    FOREIGN KEY (code_module, code_presentation) REFERENCES courses(code_module, code_presentation)
);

-- 4. StudentInfo (修正：欄位順序調整以符合 CSV)
CREATE TABLE studentInfo (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_student INTEGER,
    gender VARCHAR(10),
    region VARCHAR(45),           -- 注意：region 通常在 gender 後面
    highest_education VARCHAR(45),
    imd_band VARCHAR(20),
    age_band VARCHAR(20),
    num_of_prev_attempts INTEGER,
    studied_credits INTEGER,
    disability VARCHAR(10),
    final_result VARCHAR(45),
    PRIMARY KEY (code_module, code_presentation, id_student),
    FOREIGN KEY (code_module, code_presentation) REFERENCES courses(code_module, code_presentation)
);

-- 5. StudentRegistration (順序符合 CSV)
CREATE TABLE studentRegistration (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_student INTEGER,
    date_registration INTEGER,
    date_unregistration INTEGER,
    PRIMARY KEY (code_module, code_presentation, id_student),
    FOREIGN KEY (code_module, code_presentation, id_student) REFERENCES studentInfo(code_module, code_presentation, id_student)
);

-- 6. StudentAssessment (修正：id_assessment 通常在 CSV 第一欄，但為了保險我們讓它寬容一點，如果報錯我們再調)
-- 備註：標準 CSV 順序通常是 id_student 在前，如果不對我們等下看錯誤訊息
CREATE TABLE studentAssessment (
    id_student INTEGER,
    id_assessment INTEGER,
    date_submitted INTEGER,
    is_banked SMALLINT,
    score DOUBLE PRECISION,
    PRIMARY KEY (id_student, id_assessment),
    FOREIGN KEY (id_assessment) REFERENCES assessments(id_assessment)
);

-- 7. StudentVle (順序符合 CSV)
CREATE TABLE studentVle (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_student INTEGER,
    id_site INTEGER,
    date INTEGER,
    sum_click INTEGER,
    FOREIGN KEY (code_module, code_presentation, id_student) REFERENCES studentInfo(code_module, code_presentation, id_student),
    FOREIGN KEY (id_site) REFERENCES vle(id_site)
);