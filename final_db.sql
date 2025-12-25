-- 1. 建立 Courses (核心表)
CREATE TABLE courses (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    module_presentation_length INTEGER, 
    PRIMARY KEY (code_module, code_presentation)
);

-- 2. 建立 Assessments (評量表)
CREATE TABLE assessments (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_assessment INTEGER,
    assessment_type VARCHAR(45),
    date INTEGER,
    weight FLOAT, 
    PRIMARY KEY (id_assessment),
    FOREIGN KEY (code_module, code_presentation) REFERENCES courses(code_module, code_presentation)
);

-- 3. 建立 Vle (教材表)
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

-- 4. 建立 StudentInfo (學生資訊表)
CREATE TABLE studentInfo (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_student INTEGER,
    gender VARCHAR(10),
    region VARCHAR(45),
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

-- 5. 建立 StudentRegistration (學生註冊表)
CREATE TABLE studentRegistration (
    code_module VARCHAR(45),
    code_presentation VARCHAR(45),
    id_student INTEGER,
    date_registration INTEGER,
    date_unregistration INTEGER,
    PRIMARY KEY (code_module, code_presentation, id_student),
    FOREIGN KEY (code_module, code_presentation, id_student) REFERENCES studentInfo(code_module, code_presentation, id_student)
);

-- 6. 建立 StudentAssessment (學生評量成績表)
CREATE TABLE studentAssessment (
    id_student INTEGER,
    id_assessment INTEGER,
    date_submitted INTEGER,
    is_banked SMALLINT,
    score DOUBLE PRECISION,
    PRIMARY KEY (id_student, id_assessment),
    FOREIGN KEY (id_assessment) REFERENCES assessments(id_assessment)
);

-- 7. 建立 StudentVle (學生互動紀錄表)
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