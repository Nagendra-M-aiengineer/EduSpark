import sqlite3
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_DB = os.path.join(BASE_DIR, "eduspark.db")

# In Vercel serverless functions, the root is read-only; copy to /tmp for write access
if os.environ.get("VERCEL"):
    DATABASE = "/tmp/eduspark.db"
    if not os.path.exists(DATABASE) and os.path.exists(ORIGINAL_DB):
        shutil.copy2(ORIGINAL_DB, DATABASE)
else:
    DATABASE = ORIGINAL_DB

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_vtu_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Ensure users table has academic fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            college TEXT DEFAULT 'VTU Affiliated Engineering College',
            usn TEXT DEFAULT '',
            academic_year TEXT DEFAULT '2025-2026',
            admission_year INTEGER DEFAULT 2022,
            branch_code TEXT DEFAULT 'AIDS',
            scheme_code TEXT DEFAULT '2022',
            current_year INTEGER DEFAULT 3,
            current_sem INTEGER DEFAULT 6,
            is_admin INTEGER DEFAULT 0,
            avatar TEXT DEFAULT '👨‍🎓',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check and add any missing columns in users
    existing_cols = [c[1] for c in cursor.execute("PRAGMA table_info(users)").fetchall()]
    new_cols = {
        "college": "TEXT DEFAULT 'VTU Affiliated Engineering College'",
        "usn": "TEXT DEFAULT ''",
        "academic_year": "TEXT DEFAULT '2025-2026'",
        "admission_year": "INTEGER DEFAULT 2022",
        "branch_code": "TEXT DEFAULT 'AIDS'",
        "scheme_code": "TEXT DEFAULT '2022'",
        "current_year": "INTEGER DEFAULT 3",
        "current_sem": "INTEGER DEFAULT 6",
        "is_admin": "INTEGER DEFAULT 0"
    }
    for col, definition in new_cols.items():
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")

    # 2. Schemes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schemes (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            year_introduced INTEGER,
            total_credits INTEGER DEFAULT 160,
            official_portal_url TEXT,
            description TEXT
        )
    """)

    # 3. Branches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            short_name TEXT,
            icon TEXT,
            department TEXT
        )
    """)

    # 4. Courses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_code TEXT NOT NULL,
            branch_code TEXT NOT NULL,
            semester INTEGER NOT NULL,
            course_code TEXT NOT NULL,
            course_name TEXT NOT NULL,
            course_type TEXT DEFAULT 'PCC',
            credits REAL DEFAULT 3,
            cie_max INTEGER DEFAULT 50,
            see_max INTEGER DEFAULT 50,
            total_max INTEGER DEFAULT 100,
            syllabus_url TEXT DEFAULT '',
            official_pdf_url TEXT DEFAULT '',
            source_status TEXT DEFAULT 'VTU Official',
            last_updated TEXT DEFAULT '2025-2026',
            description TEXT DEFAULT '',
            faculty TEXT DEFAULT '',
            icon TEXT DEFAULT 'fa-book'
        )
    """)

    # 5. Course Units
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            unit_number INTEGER NOT NULL,
            unit_title TEXT NOT NULL,
            hours INTEGER DEFAULT 8,
            syllabus_content TEXT,
            simplified_explanation TEXT,
            real_life_analogy TEXT,
            visual_diagram_svg TEXT,
            key_notes TEXT,
            vtu_exam_questions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        )
    """)

    # 6. Student Marks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            cie_marks REAL DEFAULT 0,
            see_marks REAL DEFAULT 0,
            total_marks REAL DEFAULT 0,
            grade TEXT DEFAULT 'F',
            grade_point INTEGER DEFAULT 0,
            result TEXT DEFAULT 'Fail',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id)
        )
    """)

    # 7. Student Course Progress
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            unit_id INTEGER NOT NULL,
            is_completed INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id, unit_id)
        )
    """)

    # 8. Activity Points
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_name TEXT NOT NULL,
            category TEXT NOT NULL,
            activity_date TEXT,
            organization TEXT,
            description TEXT,
            points INTEGER NOT NULL DEFAULT 10,
            certificate_url TEXT DEFAULT '',
            status TEXT DEFAULT 'Approved',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 9. Internships
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company TEXT NOT NULL,
            domain TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            duration TEXT DEFAULT '4 Weeks',
            internship_type TEXT DEFAULT 'Industry',
            mentor_name TEXT,
            status TEXT DEFAULT 'Ongoing',
            report_status TEXT DEFAULT 'In Progress',
            presentation_status TEXT DEFAULT 'Pending',
            certificate_url TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 10. NPTEL Courses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nptel_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            provider TEXT DEFAULT 'Swayam / NPTEL',
            duration TEXT DEFAULT '12 Weeks',
            course_url TEXT DEFAULT 'https://nptel.ac.in/courses',
            credits INTEGER DEFAULT 3,
            enrollment_info TEXT,
            weekly_plan TEXT,
            assignment_tracker TEXT DEFAULT '10/12 Assignments Submitted',
            status TEXT DEFAULT 'Ongoing',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 11. Mock Quizzes / Tests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mock_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            unit_number INTEGER DEFAULT 1,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            explanation TEXT DEFAULT ''
        )
    """)

    # 12. Password Reset OTPs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    seed_vtu_academic_data(conn)
    conn.close()
    print("VTU database tables initialized and seeded successfully.")


def seed_vtu_academic_data(conn):
    cursor = conn.cursor()

    # Seed Schemes (Exclusively 2022 and 2025 Schemes)
    schemes = [
        ("2022", "VTU 2022 Scheme", 2022, 160, "https://vtu.ac.in/en/b-e-scheme-syllabus/#menu2", "Outcome Based Education (OBE) & Choice Based Credit System (CBCS)"),
        ("2025", "VTU 2025 Scheme", 2025, 160, "https://vtu.ac.in/en/b-e-scheme-syllabus/", "Next-generation engineering curriculum")
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO schemes (code, name, year_introduced, total_credits, official_portal_url, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, schemes)

    # Seed Branches
    branches = [
        ("AIDS", "Artificial Intelligence & Data Science", "AI & DS", "fa-brain", "Dept. of AI & Data Science"),
        ("CSE", "Computer Science & Engineering", "CSE", "fa-code", "Dept. of Computer Science"),
        ("AIML", "Artificial Intelligence & Machine Learning", "AI & ML", "fa-robot", "Dept. of AI & Machine Learning"),
        ("ISE", "Information Science & Engineering", "ISE", "fa-network-wired", "Dept. of Information Science"),
        ("ECE", "Electronics & Communication Engineering", "ECE", "fa-microchip", "Dept. of Electronics & Communication"),
        ("ME", "Mechanical Engineering", "Mechanical", "fa-gears", "Dept. of Mechanical Engineering"),
        ("CIVIL", "Civil Engineering", "Civil", "fa-building-columns", "Dept. of Civil Engineering"),
        ("EEE", "Electrical & Electronics Engineering", "EEE", "fa-bolt", "Dept. of Electrical & Electronics")
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO branches (code, name, short_name, icon, department)
        VALUES (?, ?, ?, ?, ?)
    """, branches)

    # Check if courses already exist
    count = cursor.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    if count > 0:
        return

    # Seed AI & DS 2022 Scheme Semester 1 - 8 Courses
    aids_2022_courses = [
        # SEMESTER 1
        ("2022", "AIDS", 1, "BMATS101", "Mathematics for CSE Stream-I", "BSC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BMATS101.pdf", "fa-calculator", "Calculus and Differential Equations, Linear Algebra, and Numerical Methods"),
        ("2022", "AIDS", 1, "BCHES102", "Chemistry for CSE Stream", "BSC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCHES102.pdf", "fa-flask", "Sensors, Energy systems, Display devices, Polymers and Green Chemistry"),
        ("2022", "AIDS", 1, "BCEDK103", "Computer-Aided Engineering Drawing", "ESC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCEDK103.pdf", "fa-compass-drafting", "Orthographic and Isometric Projections, Solid Geometry, CAD models"),
        ("2022", "AIDS", 1, "BENGK104", "Communicative English", "AEC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BENGK104.pdf", "fa-comments", "Grammar, Speaking skills, Technical reading, and listening"),
        ("2022", "AIDS", 1, "BKSKK107", "Samskruthika Kannada", "HSMC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BKSKK107.pdf", "fa-language", "Kannada cultural heritage, modern poetry, and historical essays"),
        ("2022", "AIDS", 1, "BIDTK158", "Innovation and Design Thinking", "AEC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BIDTK158.pdf", "fa-lightbulb", "Empathy mapping, Ideation, Prototyping, and Design Thinking sprints"),
        ("2022", "AIDS", 1, "BPLCK105B", "Introduction to Python Programming", "ESC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BPLCK105B.pdf", "fa-brands fa-python", "Control flow, Functions, Lists, Tuples, Dictionaries, and File I/O"),
        ("2022", "AIDS", 1, "BECEK105A", "Introduction to Electrical Engineering", "ESC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BECEK105A.pdf", "fa-bolt", "AC/DC circuits, Transformers, Induction motors, and Protective devices"),

        # SEMESTER 2
        ("2022", "AIDS", 2, "BMATS201", "Mathematics-II for CSE Stream", "BSC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BMATS201.pdf", "fa-square-root-variable", "Vector Calculus, Laplace Transforms, and Numerical Solutions of ODEs"),
        ("2022", "AIDS", 2, "BPHYS202", "Applied Physics for CSE Stream", "BSC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BPHYS202.pdf", "fa-atom", "Quantum Mechanics, Lasers, Optical Fibers, and Superconductivity"),
        ("2022", "AIDS", 2, "BPOPS203", "Principles of Programming Using C", "ESC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BPOPS203.pdf", "fa-code", "Pointers, Dynamic memory allocation, Structures, and File Handling in C"),
        ("2022", "AIDS", 2, "BPWSK206", "Professional Writing Skills in English", "AEC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BPWSK206.pdf", "fa-pen-nib", "Technical reports, Proposals, Formal correspondence, and Resumes"),
        ("2022", "AIDS", 2, "BICOK207", "Indian Constitution", "HSMC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BICOK207.pdf", "fa-scale-balanced", "Preamble, Fundamental Rights, Union Executive, and Judiciary"),
        ("2022", "AIDS", 2, "BSFHK258", "Scientific Foundations of Health", "AEC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BSFHK258.pdf", "fa-heart-pulse", "Health literacy, Nutrition, Preventive medicine, and Mental wellbeing"),
        ("2022", "AIDS", 2, "BESCK204E", "Green Buildings", "ESC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BESCK204E.pdf", "fa-leaf", "Sustainable architecture, Energy conservation, and Rating systems"),
        ("2022", "AIDS", 2, "BMEEK205", "Introduction to Mechanical Engineering", "ESC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BMEEK205.pdf", "fa-gear", "IC Engines, Steam turbines, Refrigeration, and Manufacturing basics"),

        # SEMESTER 3
        ("2022", "AIDS", 3, "BCS301", "Mathematics for Computer Science", "BSC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS301.pdf", "fa-chart-line", "Probability distributions, Joint distributions, Markov Chains, and Graph Theory"),
        ("2022", "AIDS", 3, "BCS302", "Digital Design & Computer Organization", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS302.pdf", "fa-microchip", "Combinational & Sequential logic, CPU architecture, Cache & Memory hierarchy"),
        ("2022", "AIDS", 3, "BCS303", "Operating Systems", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS303.pdf", "fa-server", "Process management, CPU scheduling, Memory allocation, and File systems"),
        ("2022", "AIDS", 3, "BCS304", "Data Structures and Applications", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS304.pdf", "fa-sitemap", "Stacks, Queues, Linked Lists, Trees, Graphs, Hashing, and Applications"),
        ("2022", "AIDS", 3, "BCSL305", "Data Structures Lab", "PCC", 1.5, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCSL305.pdf", "fa-laptop-code", "Implementation of Linear and Non-linear data structures in C/C++"),
        ("2022", "AIDS", 3, "BSCK307", "Social Connect and Responsibility", "AEC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BSCK307.pdf", "fa-people-group", "Community engagement, Village surveys, Plantation, and Social audits"),
        ("2022", "AIDS", 3, "BPEK359", "Physical Education", "AEC", 0, 50, 50, 100, "", "fa-person-running", "Fitness, Athletics, Sportsmanship, and Physical wellness activities"),
        ("2022", "AIDS", 3, "BPLCK305A", "Data Analytics with Excel", "ESC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BPLCK305A.pdf", "fa-file-excel", "Formulas, Pivot tables, Power Query, What-If analysis, and Data dashboarding"),
        ("2022", "AIDS", 3, "BCS306A", "Object Oriented Programming with Java", "PCC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS306A.pdf", "fa-brands fa-java", "Classes, Inheritance, Polymorphism, Exception handling, Multi-threading, and Collections"),

        # SEMESTER 4
        ("2022", "AIDS", 4, "BCS401", "Analysis & Design of Algorithms", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS401.pdf", "fa-diagram-project", "Divide & Conquer, Greedy method, Dynamic programming, Backtracking, and NP-Completeness"),
        ("2022", "AIDS", 4, "BAD402", "Artificial Intelligence", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD402.pdf", "fa-brain", "Search algorithms, Knowledge representation, Probabilistic reasoning, and Expert systems"),
        ("2022", "AIDS", 4, "BCS403", "Database Management Systems", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS403.pdf", "fa-database", "ER Modeling, Relational Algebra, SQL, Normalization (1NF-BCNF), and Transactions"),
        ("2022", "AIDS", 4, "BCSL404", "Analysis & Design of Algorithms Lab", "PCC", 1.5, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCSL404.pdf", "fa-terminal", "Algorithm implementations, asymptotic analysis, and empirical time testing"),
        ("2022", "AIDS", 4, "BBOC407", "Biology for Computer Engineers", "BSC", 2, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BBOC407.pdf", "fa-dna", "Cellular biology, Neural computation analogies, Bio-sensors, and Bioinformatics"),
        ("2022", "AIDS", 4, "BUHK408", "Universal Human Values Course", "HSMC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BUHK408.pdf", "fa-hand-holding-heart", "Human aspirations, Harmony in family & society, Professional ethics"),
        ("2022", "AIDS", 4, "BYOK459", "Yoga", "AEC", 0, 50, 50, 100, "", "fa-spa", "Asanas, Pranayama, Meditation techniques, and Stress reduction"),
        ("2022", "AIDS", 4, "BCS405A", "Discrete Mathematical Structures", "PCC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS405A.pdf", "fa-cubes", "Set Theory, Relations, Functions, Mathematical Induction, and Combinatorics"),
        ("2022", "AIDS", 4, "BAD406B", "MongoDB", "AEC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD406B.pdf", "fa-leaf", "Document databases, Aggregation pipelines, Indexing, and Atlas integration"),

        # SEMESTER 5
        ("2022", "AIDS", 5, "BCS501", "Software Engineering and Project Management", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS501.pdf", "fa-list-check", "Agile methodologies, Requirements engineering, Architecture design, Testing, and Scrum"),
        ("2022", "AIDS", 5, "BCS502", "Computer Networks", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS502.pdf", "fa-network-wired", "OSI & TCP/IP stack, Routing protocols (OSPF/BGP), Flow control, and Socket API"),
        ("2022", "AIDS", 5, "BCS503", "Theory of Computation", "PCC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS503.pdf", "fa-infinity", "Finite Automata, Regular Expressions, Context-Free Grammars, and Turing Machines"),
        ("2022", "AIDS", 5, "BADL504", "Data Visualization Lab", "PCC", 1.5, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BADL504.pdf", "fa-chart-pie", "Tableau, PowerBI, Matplotlib, Seaborn, and interactive web dashboard creation"),
        ("2022", "AIDS", 5, "BADP505", "Mini Project", "PROJ", 2, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BADP505.pdf", "fa-diagram-project", "Practical application development solving realistic community or industry problems"),
        ("2022", "AIDS", 5, "BRMK556", "Research Methodology and IPR", "PCC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BRMK556.pdf", "fa-magnifying-glass-chart", "Literature review, Statistical hypothesis testing, Patents, Trademarks, and Ethics"),
        ("2022", "AIDS", 5, "BESK508", "Environmental Studies and E-Waste Management", "AEC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BESK508.pdf", "fa-recycle", "Ecosystems, Pollution prevention, Circular economy, and Electronic waste recycling"),
        ("2022", "AIDS", 5, "BNSS559", "National Service Scheme", "AEC", 0, 50, 50, 100, "", "fa-handshake", "Community welfare, Health camps, Literacy drives, and Disaster management"),
        ("2022", "AIDS", 5, "BCS515C", "Cloud Computing", "PEC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS515C.pdf", "fa-cloud", "Virtualization, AWS/GCP architecture, Serverless, Containers, and Cloud Security"),

        # SEMESTER 6
        ("2022", "AIDS", 6, "BAD601", "Big Data Analytics", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD601.pdf", "fa-cubes-stacked", "Hadoop ecosystem, HDFS, MapReduce, Apache Spark, and Streaming analytics"),
        ("2022", "AIDS", 6, "BAD602", "Machine Learning", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD602.pdf", "fa-robot", "Supervised & Unsupervised learning, Decision trees, SVM, Ensembles, and Clustering"),
        ("2022", "AIDS", 6, "BADP606", "Project Phase-I", "PROJ", 2, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BADP606.pdf", "fa-bars-progress", "Problem formulation, Literature survey, Requirement analysis, and Initial prototype"),
        ("2022", "AIDS", 6, "BADL604", "Machine Learning Lab", "PCC", 1.5, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BADL604.pdf", "fa-flask-vial", "Hands-on model building, cross-validation, hyperparameter tuning using Scikit-Learn"),
        ("2022", "AIDS", 6, "BMUS659", "Music", "AEC", 0, 50, 50, 100, "", "fa-music", "Indian classical music foundations, Ragas, Rhythm structures, and Sonic appreciation"),
        ("2022", "AIDS", 6, "BIKS608", "Indian Knowledge System", "AEC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BIKS608.pdf", "fa-scroll", "Traditional astronomy, Vedic mathematics, Metallurgy, and Ancient engineering"),
        ("2022", "AIDS", 6, "BAEC607", "Water Conservation and Rainwater Harvesting", "AEC", 1, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAEC607.pdf", "fa-droplet", "Hydrological cycle, Aquifer recharge, Rainwater harvesting design, and Quality testing"),
        ("2022", "AIDS", 6, "BCS615A", "UI/UX", "PEC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS615A.pdf", "fa-palette", "User research, Wireframing, Figma design systems, Usability heuristics, and Prototyping"),
        ("2022", "AIDS", 6, "BAD613A", "Natural Language Processing", "PEC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD613A.pdf", "fa-comment-dots", "Tokenization, Word embeddings, POS tagging, Transformers, and Sentiment classification"),

        # SEMESTER 7
        ("2022", "AIDS", 7, "BAD701", "Deep Learning and Reinforcement Learning", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD701.pdf", "fa-brain", "Feedforward nets, CNNs, RNNs, LSTMs, Q-learning, Policy gradients, and Actor-Critic models"),
        ("2022", "AIDS", 7, "BAD702", "Data Security and Privacy", "PCC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD702.pdf", "fa-shield-halved", "Cryptography, Differential privacy, Federated learning security, and GDPR compliance"),
        ("2022", "AIDS", 7, "BAD713A", "Statistical Machine Learning", "PEC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD713A.pdf", "fa-chart-area", "Bayesian inference, EM algorithm, Gaussian processes, and Graphical models"),
        ("2022", "AIDS", 7, "BAD724B", "Social Network Analysis", "PEC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD724B.pdf", "fa-share-nodes", "Network topology, Centrality measures, Community detection, and Influence propagation"),
        ("2022", "AIDS", 7, "BENV755", "Conservation of Natural Resources", "OEC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BENV755.pdf", "fa-seedling", "Biodiversity preservation, Wildlife corridors, Soil conservation, and Renewable energy"),
        ("2022", "AIDS", 7, "BADP706", "Major Project Phase-1", "PROJ", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BADP706.pdf", "fa-diagram-project", "High-level design, Hardware/Software setup, Core module implementation, and Review"),
        ("2022", "AIDS", 7, "BACT707", "Activity-Based Academic Component", "AEC", 1, 50, 50, 100, "", "fa-award", "Technical paper publication, Patent filing, or State-level Hackathon participation"),

        # SEMESTER 8
        ("2022", "AIDS", 8, "BNPT801", "NPTEL Online Course - Advanced AI", "OEC", 3, 50, 50, 100, "https://nptel.ac.in/courses/106/106/106106184/", "fa-graduation-cap", "Swayam / NPTEL 12-week verified proctored online course credit transfer"),
        ("2022", "AIDS", 8, "BNPT802", "NPTEL Online Course - Data Science Ethics", "PEC", 3, 50, 50, 100, "https://nptel.ac.in/courses/106/105/106105152/", "fa-scale-unbalanced", "AI algorithmic bias, fairness, transparency, and accountability frameworks"),
        ("2022", "AIDS", 8, "BAD803", "Professional Elective - Computer Vision", "PEC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BAD803.pdf", "fa-eye", "Image processing, Feature extraction, YOLO object detection, and Vision Transformers"),
        ("2022", "AIDS", 8, "BOEC804", "Open Elective - Tech Entrepreneurship", "OEC", 3, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BOEC804.pdf", "fa-rocket", "Startup lifecycle, Business model canvas, Venture capital pitching, and IP strategy"),
        ("2022", "AIDS", 8, "BINT805", "Full Semester Industry Internship", "INT", 10, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BINT805.pdf", "fa-briefcase", "16-week full-time industry internship with industrial mentor & faculty guide"),
        ("2022", "AIDS", 8, "BADP806", "Major Project Phase-2 / Defense", "PROJ", 6, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BADP806.pdf", "fa-trophy", "Complete system implementation, deployment, benchmark evaluation, and Viva-Voce defense")
    ]

    for item in aids_2022_courses:
        cursor.execute("""
            INSERT INTO courses (
                scheme_code, branch_code, semester, course_code, course_name,
                course_type, credits, cie_max, see_max, total_max,
                syllabus_url, icon, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    # Seed core units for key subjects like Machine Learning (BAD602), Big Data Analytics (BAD601), Operating Systems (BCS303), DBMS (BCS403), etc.
    seed_course_units(cursor)

    # Also seed representative courses for CSE 2022, AIML 2022, ECE 2022, ME 2022, CIVIL 2022, and 2025 schemes
    seed_other_branches_and_schemes(cursor)

    conn.commit()


def seed_course_units(cursor):
    # Retrieve Machine Learning course ID
    ml_row = cursor.execute("SELECT id FROM courses WHERE course_code = 'BAD602'").fetchone()
    if ml_row:
        ml_id = ml_row[0]
        ml_units = [
            (
                ml_id, 1, "Introduction to Machine Learning & Concept Learning", 8,
                "Well-posed learning problems, Designing a learning system, Perspectives and issues in machine learning. Concept learning: A concept learning task, Concept learning as search, Find-S algorithm, Version spaces and Candidate-Elimination algorithm, Inductive bias.",
                "Machine Learning is teaching computers to recognize patterns from past data instead of writing hardcoded rules. Concept learning searches through hypotheses to find a rule that fits training examples.",
                "Imagine teaching a child to recognize a 'Fruit'. You show them apples, bananas, and oranges (positive examples), and potatoes (negative example). Over time, their mental concept sharpens.",
                """<svg viewBox="0 0 700 180" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                    <rect x="20" y="50" width="130" height="70" rx="14" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                    <text x="85" y="80" text-anchor="middle" font-size="13" font-weight="bold" fill="#312e81">Training Data</text>
                    <text x="85" y="100" text-anchor="middle" font-size="11" fill="#4338ca">Past Experiences</text>
                    <path d="M150 85 L210 85" stroke="#4f46e5" stroke-width="3" marker-end="url(#arrow)"/>
                    <rect x="210" y="50" width="160" height="70" rx="14" fill="#fae8ff" stroke="#a855f7" stroke-width="2"/>
                    <text x="290" y="80" text-anchor="middle" font-size="13" font-weight="bold" fill="#581c87">ML Algorithm</text>
                    <text x="290" y="100" text-anchor="middle" font-size="11" fill="#7e22ce">Find-S / Candidate-Elim</text>
                    <path d="M370 85 L430 85" stroke="#a855f7" stroke-width="3"/>
                    <rect x="430" y="50" width="130" height="70" rx="14" fill="#ccfbf1" stroke="#0d9488" stroke-width="2"/>
                    <text x="495" y="80" text-anchor="middle" font-size="13" font-weight="bold" fill="#134e4a">Hypothesis (h)</text>
                    <text x="495" y="100" text-anchor="middle" font-size="11" fill="#0f766e">Trained Model</text>
                    <path d="M560 85 L610 85" stroke="#0d9488" stroke-width="3"/>
                    <rect x="610" y="50" width="80" height="70" rx="14" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
                    <text x="650" y="90" text-anchor="middle" font-size="12" font-weight="bold" fill="#78350f">Predictions</text>
                </svg>""",
                "• Well-posed learning: A computer program learns from Experience (E) with respect to Task (T) and Performance measure (P) if performance improves with experience.\n• Find-S: Starts with most specific hypothesis <0,0,0...> and generalizes only when encountering positive training instances.\n• Candidate-Elimination: Maintains General boundary G and Specific boundary S enclosing all consistent hypotheses.\n• Inductive Bias: Necessary assumptions enabling generalization beyond observed data.",
                "1. Define a well-posed learning problem with two examples. (VTU 2023, 6 marks)\n2. Explain the Candidate-Elimination algorithm with an illustrative example. (VTU 2024, 10 marks)\n3. What is Inductive Bias? Why is it necessary for a learner? (VTU 2022, 6 marks)"
            ),
            (
                ml_id, 2, "Decision Tree Learning", 8,
                "Decision tree representation, Appropriate problems for decision tree learning, Basic decision tree learning algorithm: ID3, Entropy, Information Gain, Hypothesis space search in decision tree learning, Inductive bias, Issues in decision tree learning: Overfitting, Pruning.",
                "Decision trees make decisions by asking a hierarchy of questions. At each step, the algorithm picks the question that gives the highest 'Information Gain' (reduction in chaos/entropy).",
                "Think of playing 20 Questions to guess an animal. If you ask 'Does it have legs?' you cut the possibilities in half much faster than asking 'Is it named Bob?'.",
                """<svg viewBox="0 0 700 180" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="350" cy="35" r="28" fill="#4f46e5" />
                    <text x="350" y="40" text-anchor="middle" font-size="11" font-weight="bold" fill="white">Outlook</text>
                    <line x1="330" y1="60" x2="200" y2="100" stroke="#94a3b8" stroke-width="2"/>
                    <line x1="350" y1="63" x2="350" y2="100" stroke="#94a3b8" stroke-width="2"/>
                    <line x1="370" y1="60" x2="500" y2="100" stroke="#94a3b8" stroke-width="2"/>
                    <text x="245" y="75" font-size="11" fill="#64748b">Sunny</text>
                    <text x="360" y="85" font-size="11" fill="#64748b">Overcast</text>
                    <text x="450" y="75" font-size="11" fill="#64748b">Rain</text>
                    <rect x="150" y="105" width="100" height="40" rx="8" fill="#f1f5f9" stroke="#64748b"/>
                    <text x="200" y="130" text-anchor="middle" font-size="11" font-weight="bold">Humidity?</text>
                    <rect x="300" y="105" width="100" height="40" rx="8" fill="#dcfce7" stroke="#16a34a"/>
                    <text x="350" y="130" text-anchor="middle" font-size="12" font-weight="bold" fill="#15803d">Play: YES</text>
                    <rect x="450" y="105" width="100" height="40" rx="8" fill="#f1f5f9" stroke="#64748b"/>
                    <text x="500" y="130" text-anchor="middle" font-size="11" font-weight="bold">Windy?</text>
                </svg>""",
                "• Entropy: S = - sum(p_i * log2(p_i)). Measures uncertainty in dataset.\n• Information Gain: Gain(S, A) = Entropy(S) - sum(|Sv|/|S| * Entropy(Sv)).\n• Overfitting: Happens when tree fits training noise. Handled by Reduced Error Pruning or Rule Post-Pruning.",
                "1. Compute Entropy and Information Gain for given dataset and identify the root node. (VTU 2023, 10 marks)\n2. Explain ID3 algorithm steps and its inductive bias. (VTU 2022, 8 marks)\n3. How to avoid overfitting in Decision Trees? (VTU 2024, 6 marks)"
            ),
            (
                ml_id, 3, "Neural Networks & Perceptrons", 8,
                "Biological motivation, Neural network representation, Perceptrons, Representational power of perceptrons, Perceptron training rule, Gradient descent and Delta rule, Multilayer networks, Backpropagation algorithm, Derivation of backpropagation weight update rule.",
                "Artificial Neural Networks are computational networks inspired by the human brain. Multilayer Perceptrons use the Backpropagation algorithm (gradient descent via chain rule) to learn non-linear boundaries.",
                "Like tuning guitar strings: you pluck a string (forward pass), hear how far off-pitch it is (error calculation), and twist the pegs clockwise/counter-clockwise to reduce the error (backpropagation weight update).",
                """<svg viewBox="0 0 700 170" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="100" cy="50" r="18" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                    <circle cx="100" cy="110" r="18" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                    <circle cx="350" cy="40" r="18" fill="#fae8ff" stroke="#a855f7" stroke-width="2"/>
                    <circle cx="350" cy="80" r="18" fill="#fae8ff" stroke="#a855f7" stroke-width="2"/>
                    <circle cx="350" cy="120" r="18" fill="#fae8ff" stroke="#a855f7" stroke-width="2"/>
                    <circle cx="600" cy="80" r="22" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
                    <line x1="118" y1="50" x2="332" y2="40" stroke="#94a3b8" stroke-width="1.5"/>
                    <line x1="118" y1="50" x2="332" y2="80" stroke="#94a3b8" stroke-width="1.5"/>
                    <line x1="118" y1="110" x2="332" y2="80" stroke="#94a3b8" stroke-width="1.5"/>
                    <line x1="118" y1="110" x2="332" y2="120" stroke="#94a3b8" stroke-width="1.5"/>
                    <line x1="368" y1="40" x2="578" y2="80" stroke="#94a3b8" stroke-width="1.5"/>
                    <line x1="368" y1="80" x2="578" y2="80" stroke="#94a3b8" stroke-width="1.5"/>
                    <line x1="368" y1="120" x2="578" y2="80" stroke="#94a3b8" stroke-width="1.5"/>
                    <text x="100" y="155" text-anchor="middle" font-size="12" font-weight="bold">Input Layer</text>
                    <text x="350" y="155" text-anchor="middle" font-size="12" font-weight="bold">Hidden Layer</text>
                    <text x="600" y="155" text-anchor="middle" font-size="12" font-weight="bold">Output Layer</text>
                </svg>""",
                "• Single Perceptron can only classify linearly separable functions (fails on XOR).\n• Sigmoid Activation: sigma(y) = 1 / (1 + e^(-y)), gives smooth derivative sigma * (1 - sigma).\n• Backpropagation: Uses calculus chain rule to propagate error delta from output layer back to hidden layers to update weights w_ij = w_ij + eta * delta_j * x_i.",
                "1. Prove that a single perceptron cannot represent the XOR function. (VTU 2023, 6 marks)\n2. Derive the weight update rule for the Backpropagation algorithm. (VTU 2024, 10 marks)\n3. Differentiate between Batch Gradient Descent and Stochastic Gradient Descent. (VTU 2022, 6 marks)"
            ),
            (
                ml_id, 4, "Bayesian Learning & Naive Bayes", 8,
                "Bayes theorem, Maximum A Posteriori (MAP) and Maximum Likelihood (ML) hypotheses, Bayes optimal classifier, Gibbs algorithm, Naive Bayes classifier, Bayesian belief networks, EM algorithm.",
                "Bayesian reasoning calculates the probability that a hypothesis is true given evidence: P(h|D) = (P(D|h) * P(h)) / P(D). Naive Bayes assumes all features are conditionally independent given the class label.",
                "Email Spam Filter: If an email contains words like 'Lottery', 'Win', and 'Cash', Naive Bayes computes the combined probability that it is spam versus regular mail.",
                """<svg viewBox="0 0 700 170" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                    <rect x="50" y="40" width="180" height="80" rx="14" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                    <text x="140" y="70" text-anchor="middle" font-size="13" font-weight="bold" fill="#312e81">Prior P(h)</text>
                    <text x="140" y="95" text-anchor="middle" font-size="11" fill="#4338ca">Initial belief before data</text>
                    <text x="260" y="85" font-size="24" font-weight="bold" fill="#64748b">×</text>
                    <rect x="290" y="40" width="180" height="80" rx="14" fill="#fae8ff" stroke="#a855f7" stroke-width="2"/>
                    <text x="380" y="70" text-anchor="middle" font-size="13" font-weight="bold" fill="#581c87">Likelihood P(D|h)</text>
                    <text x="380" y="95" text-anchor="middle" font-size="11" fill="#7e22ce">How likely data fits h</text>
                    <text x="500" y="85" font-size="24" font-weight="bold" fill="#64748b">→</text>
                    <rect x="530" y="40" width="150" height="80" rx="14" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
                    <text x="605" y="70" text-anchor="middle" font-size="13" font-weight="bold" fill="#14532d">Posterior P(h|D)</text>
                    <text x="605" y="95" text-anchor="middle" font-size="11" fill="#15803d">Updated probability</text>
                </svg>""",
                "• Bayes Theorem: P(h|D) = (P(D|h) * P(h)) / P(D)\n• MAP Hypothesis: h_MAP = argmax P(D|h) * P(h)\n• Naive Bayes: P(y | x1...xn) proportional to P(y) * product(P(xi | y))\n• Bayesian Belief Networks: Directed Acyclic Graphs representing conditional independence properties.",
                "1. State and prove Bayes theorem. Apply it to medical diagnosis problem. (VTU 2023, 8 marks)\n2. Explain the Naive Bayes classifier with text classification example. (VTU 2024, 10 marks)\n3. What is Bayes Optimal Classifier? Why is it impractical? (VTU 2022, 6 marks)"
            ),
            (
                ml_id, 5, "Instance-Based Learning & Reinforcement Learning", 8,
                "k-Nearest Neighbor (k-NN) learning, Distance-weighted nearest neighbor algorithm, Locally weighted regression, Radial Basis Functions (RBF), Case-Based Reasoning. Reinforcement Learning: Q-learning, Temporal Difference learning, Bellman optimality equation.",
                "Instance-Based Learning stores training instances directly ('Lazy Learning') and defers computation until a query arrives. Reinforcement learning trains an agent to choose actions that maximize cumulative rewards over time.",
                "k-NN is like asking your 5 closest neighbors for advice. Reinforcement Learning is like training a puppy: treats for good actions (reward), no treats for bad actions (penalty).",
                """<svg viewBox="0 0 700 170" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                    <rect x="60" y="45" width="160" height="80" rx="14" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
                    <text x="140" y="80" text-anchor="middle" font-size="15" font-weight="bold" fill="#78350f">Agent (Model)</text>
                    <text x="140" y="102" text-anchor="middle" font-size="11" fill="#b45309">Makes Decision</text>
                    <path d="M220 70 L460 70" stroke="#4f46e5" stroke-width="3" marker-end="url(#arrow)"/>
                    <text x="340" y="60" text-anchor="middle" font-size="12" font-weight="bold" fill="#4f46e5">Action (A)</text>
                    <rect x="470" y="45" width="170" height="80" rx="14" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                    <text x="555" y="80" text-anchor="middle" font-size="15" font-weight="bold" fill="#312e81">Environment</text>
                    <text x="555" y="102" text-anchor="middle" font-size="11" fill="#4338ca">World Simulation</text>
                    <path d="M470 105 L220 105" stroke="#16a34a" stroke-width="3"/>
                    <text x="340" y="125" text-anchor="middle" font-size="12" font-weight="bold" fill="#16a34a">Reward (R) + New State (S')</text>
                </svg>""",
                "• k-NN: Classifies based on Euclidean distance d(x, y) = sqrt(sum((xi - yi)^2)). Curse of dimensionality affects k-NN.\n• Q-Learning: Q(s, a) = Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)].\n• Exploration vs Exploitation tradeoff is balanced by epsilon-greedy policies.",
                "1. Explain k-Nearest Neighbor algorithm and discuss its advantages and disadvantages. (VTU 2023, 8 marks)\n2. Formulate Q-learning and explain the Bellman update equation. (VTU 2024, 10 marks)\n3. Differentiate between Lazy and Eager learning with examples. (VTU 2022, 6 marks)"
            )
        ]
        cursor.executemany("""
            INSERT INTO course_units (
                course_id, unit_number, unit_title, hours,
                syllabus_content, simplified_explanation, real_life_analogy,
                visual_diagram_svg, key_notes, vtu_exam_questions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ml_units)

        # Seed sample mock questions for Machine Learning
        ml_questions = [
            (ml_id, 1, "Which of the following algorithms searches for the most specific hypothesis consistent with positive examples?", "Candidate-Elimination", "Find-S", "ID3", "Backpropagation", "B", "Find-S ignores negative instances and generalizes only for positive training instances."),
            (ml_id, 1, "In the Version Space representation, the S boundary represents:", "Most general hypotheses", "Most specific hypotheses", "Null hypotheses", "Optimal neural weights", "B", "S-boundary contains the most specific hypotheses consistent with the training examples."),
            (ml_id, 2, "In ID3 decision tree learning, the metric used to measure impurity in a dataset is:", "Euclidean Distance", "Information Gain", "Entropy", "Gini Index", "C", "Entropy measures the randomness or impurity in a sample of training data."),
            (ml_id, 3, "A single-layer perceptron with a linear threshold unit can represent which logical function?", "XOR", "XNOR", "AND", "Parity", "C", "A single perceptron is a linear classifier and can only separate linearly separable functions such as AND, OR, NAND, NOR."),
            (ml_id, 4, "Naive Bayes classifier is called 'naive' because:", "It requires very little computation", "It assumes conditional independence between features given the class", "It works only on binary labels", "It does not require prior probabilities", "B", "The naive assumption is that all attributes are conditionally independent given the target value.")
        ]
        cursor.executemany("""
            INSERT INTO mock_questions (
                course_id, unit_number, question_text, option_a, option_b, option_c, option_d, correct_option, explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ml_questions)

    # Seed Big Data Analytics units (BAD601)
    bd_row = cursor.execute("SELECT id FROM courses WHERE course_code = 'BAD601'").fetchone()
    if bd_row:
        bd_id = bd_row[0]
        bd_units = [
            (
                bd_id, 1, "Introduction to Big Data & Hadoop Ecosystem", 8,
                "Big Data characteristics (5 V's: Volume, Velocity, Variety, Veracity, Value), Distributed file systems, Hadoop architecture, HDFS Daemons: NameNode, DataNode, Secondary NameNode, Block replication, Rack awareness.",
                "Big Data refers to datasets too large and fast for traditional single-server databases. Hadoop splits massive files across commodity computers and processes data right where it lives.",
                "Instead of having one librarian read 1,000,000 books, you distribute 1,000 books to 1,000 students across 100 library tables.",
                """<svg viewBox="0 0 700 160" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                    <rect x="50" y="30" width="160" height="100" rx="14" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                    <text x="130" y="65" text-anchor="middle" font-size="14" font-weight="bold" fill="#312e81">NameNode (Master)</text>
                    <text x="130" y="90" text-anchor="middle" font-size="11" fill="#4338ca">Holds Metadata in RAM</text>
                    <text x="130" y="108" text-anchor="middle" font-size="11" fill="#4338ca">Block Mapping</text>
                    <path d="M210 80 L320 80" stroke="#4f46e5" stroke-width="3"/>
                    <rect x="320" y="15" width="160" height="40" rx="8" fill="#dcfce7" stroke="#16a34a"/>
                    <text x="400" y="40" text-anchor="middle" font-size="12" font-weight="bold" fill="#14532d">DataNode 1 (Block A, B)</text>
                    <rect x="320" y="60" width="160" height="40" rx="8" fill="#dcfce7" stroke="#16a34a"/>
                    <text x="400" y="85" text-anchor="middle" font-size="12" font-weight="bold" fill="#14532d">DataNode 2 (Block B, C)</text>
                    <rect x="320" y="105" width="160" height="40" rx="8" fill="#dcfce7" stroke="#16a34a"/>
                    <text x="400" y="130" text-anchor="middle" font-size="12" font-weight="bold" fill="#14532d">DataNode 3 (Block A, C)</text>
                </svg>""",
                "• HDFS default block size: 128 MB.\n• Replication Factor: default is 3 (2 blocks on same rack, 1 on different rack for disaster recovery).\n• NameNode is Single Point of Failure (SPOF) in Hadoop 1.x, resolved by Active-Standby with ZooKeeper in 2.x+.",
                "1. Explain HDFS architecture and the roles of NameNode and DataNode. (VTU 2024, 10 marks)\n2. Detail the 5 V's of Big Data with real-world industry examples. (VTU 2023, 8 marks)"
            ),
            (
                bd_id, 2, "Hadoop MapReduce Framework & YARN", 8,
                "MapReduce programming model, Map phase, Shuffle and Sort phase, Reduce phase, Combiners, Partitioners, YARN architecture: ResourceManager, NodeManager, ApplicationMaster, Container allocation.",
                "MapReduce processes big data in two phases: Map extracts key-value pairs; Shuffle & Sort groups matching keys; Reduce aggregates values to produce final summaries.",
                "Counting ballots in an election: Each voting booth counts votes per candidate locally (Map + Combiner), all tallies are consolidated by election headquarters (Reduce).",
                """<svg viewBox="0 0 700 150" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                    <rect x="30" y="45" width="110" height="60" rx="10" fill="#e0e7ff" stroke="#4f46e5"/>
                    <text x="85" y="80" text-anchor="middle" font-size="12" font-weight="bold">Input Split</text>
                    <path d="M140 75 L190 75" stroke="#4f46e5" stroke-width="2"/>
                    <rect x="190" y="45" width="110" height="60" rx="10" fill="#fae8ff" stroke="#a855f7"/>
                    <text x="245" y="80" text-anchor="middle" font-size="12" font-weight="bold">Map &lt;k1, v1&gt;</text>
                    <path d="M300 75 L350 75" stroke="#a855f7" stroke-width="2"/>
                    <rect x="350" y="45" width="130" height="60" rx="10" fill="#fef3c7" stroke="#d97706"/>
                    <text x="415" y="80" text-anchor="middle" font-size="12" font-weight="bold">Shuffle &amp; Sort</text>
                    <path d="M480 75 L530 75" stroke="#d97706" stroke-width="2"/>
                    <rect x="530" y="45" width="130" height="60" rx="10" fill="#dcfce7" stroke="#16a34a"/>
                    <text x="595" y="80" text-anchor="middle" font-size="12" font-weight="bold">Reduce &lt;k2, v2&gt;</text>
                </svg>""",
                "• Map: Transforms raw input into intermediate key-value pairs (k2, v2).\n• Partitioning: Decides which reducer receives which key.\n• YARN separates resource management (ResourceManager) from job monitoring (ApplicationMaster).",
                "1. Write and explain a complete WordCount MapReduce algorithm. (VTU 2024, 10 marks)\n2. Explain YARN architecture and execution lifecycle. (VTU 2023, 8 marks)"
            )
        ]
        cursor.executemany("""
            INSERT INTO course_units (
                course_id, unit_number, unit_title, hours,
                syllabus_content, simplified_explanation, real_life_analogy,
                visual_diagram_svg, key_notes, vtu_exam_questions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, bd_units)


def seed_other_branches_and_schemes(cursor):
    # CSE 2022 Scheme Sample Courses
    cse_courses = [
        ("2022", "CSE", 3, "BCS301", "Mathematics for Computer Science", "BSC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS301.pdf", "fa-calculator", "Probability, Random Variables and Graph Theory"),
        ("2022", "CSE", 3, "BCS302", "Digital Design & Computer Organization", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS302.pdf", "fa-microchip", "Boolean logic, CPU Datapath, and Memory Subsystems"),
        ("2022", "CSE", 3, "BCS303", "Operating Systems", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS303.pdf", "fa-server", "Processes, Scheduling, Deadlocks, Paging, and File Systems"),
        ("2022", "CSE", 3, "BCS304", "Data Structures and Applications", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS304.pdf", "fa-sitemap", "Arrays, Linked Lists, Trees, Graphs, and Hash Tables"),
        ("2022", "CSE", 4, "BCS401", "Analysis & Design of Algorithms", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS401.pdf", "fa-diagram-project", "Complexity analysis, Greedy, Dynamic Programming"),
        ("2022", "CSE", 4, "BCS402", "Microcontrollers & Embedded Systems", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS402.pdf", "fa-microchip", "ARM cortex architecture, Interfacing, and Real-time operating systems"),
        ("2022", "CSE", 4, "BCS403", "Database Management Systems", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS403.pdf", "fa-database", "Relational Model, SQL, Normalization, Transactions"),
        ("2022", "CSE", 5, "BCS501", "Software Engineering and Project Management", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS501.pdf", "fa-list-check", "Agile, Requirements, System Modeling, Software Testing"),
        ("2022", "CSE", 5, "BCS502", "Computer Networks", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS502.pdf", "fa-network-wired", "Protocol Architecture, LANs, Routing, TCP, Congestion Control"),
        ("2022", "CSE", 6, "BCS601", "Full Stack Development", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS601.pdf", "fa-laptop-code", "React, Node.js, Express, REST APIs, and Cloud Deployment"),
        ("2022", "CSE", 6, "BCS602", "Compiler Design", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCS602.pdf", "fa-gears", "Lexical analysis, Parsing, Syntax Directed Translation, Code Generation")
    ]
    for item in cse_courses:
        cursor.execute("""
            INSERT OR IGNORE INTO courses (
                scheme_code, branch_code, semester, course_code, course_name,
                course_type, credits, cie_max, see_max, total_max,
                syllabus_url, icon, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    # ECE 2022 Scheme Sample Courses
    ece_courses = [
        ("2022", "ECE", 3, "BEC301", "Engineering Mathematics-III", "BSC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BEC301.pdf", "fa-square-root-variable", "Fourier series, Partial Differential Equations, Z-Transforms"),
        ("2022", "ECE", 3, "BEC302", "Digital System Design using Verilog", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BEC302.pdf", "fa-microchip", "Verilog HDL, Combinational & Sequential hardware synthesis"),
        ("2022", "ECE", 4, "BEC401", "Signals and Systems", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BEC401.pdf", "fa-wave-square", "Continuous and Discrete time signals, LTI systems, DTFT, FFT"),
        ("2022", "ECE", 5, "BEC501", "Electromagnetic Waves & Antennas", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BEC501.pdf", "fa-tower-broadcast", "Maxwell's equations, Waveguides, Radiation patterns, and Antenna arrays"),
        ("2022", "ECE", 6, "BEC601", "VLSI Design", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BEC601.pdf", "fa-memory", "MOS transistor theory, CMOS fabrication, Layout design rules, Static timing analysis")
    ]
    for item in ece_courses:
        cursor.execute("""
            INSERT OR IGNORE INTO courses (
                scheme_code, branch_code, semester, course_code, course_name,
                course_type, credits, cie_max, see_max, total_max,
                syllabus_url, icon, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    # Mechanical 2022 Scheme Sample Courses
    me_courses = [
        ("2022", "ME", 3, "BME301", "Material Science & Metallurgy", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BME301.pdf", "fa-cubes", "Crystal structures, Phase diagrams, Heat treatment, and Alloys"),
        ("2022", "ME", 4, "BME401", "Applied Thermodynamics", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BME401.pdf", "fa-fire", "Gas power cycles, Vapor compression refrigeration, Air conditioning"),
        ("2022", "ME", 5, "BME501", "Design of Machine Elements-I", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BME501.pdf", "fa-gear", "Stress concentration, Fatigue design, Shafts, Keys, and Couplings"),
        ("2022", "ME", 6, "BME601", "Heat Transfer & Fluid Machinery", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BME601.pdf", "fa-temperature-high", "Conduction, Convection, Radiation, Heat exchangers, and Turbines")
    ]
    for item in me_courses:
        cursor.execute("""
            INSERT OR IGNORE INTO courses (
                scheme_code, branch_code, semester, course_code, course_name,
                course_type, credits, cie_max, see_max, total_max,
                syllabus_url, icon, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    # Civil 2022 Scheme Sample Courses
    civil_courses = [
        ("2022", "CIVIL", 3, "BCV301", "Mechanics of Materials", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCV301.pdf", "fa-building", "Simple stresses and strains, Shear force & Bending moment diagrams"),
        ("2022", "CIVIL", 4, "BCV401", "Fluid Mechanics & Hydraulics", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCV401.pdf", "fa-water", "Fluid statics, Bernoulli's equation, Flow through pipes, and Open channels"),
        ("2022", "CIVIL", 5, "BCV501", "Design of RC Structural Elements", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCV501.pdf", "fa-trowel-bricks", "Limit state method, Beams, Slabs, Columns, and Footing design"),
        ("2022", "CIVIL", 6, "BCV601", "Geotechnical Engineering", "PCC", 4, 50, 50, 100, "https://vtu.ac.in/pdf/2022syll/BCV601.pdf", "fa-mountain", "Soil classification, Compaction, Permeability, Shear strength, and Bearing capacity")
    ]
    for item in civil_courses:
        cursor.execute("""
            INSERT OR IGNORE INTO courses (
                scheme_code, branch_code, semester, course_code, course_name,
                course_type, credits, cie_max, see_max, total_max,
                syllabus_url, icon, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    # VTU 2025 Scheme sample
    cursor.execute("""
        INSERT OR IGNORE INTO courses (
            scheme_code, branch_code, semester, course_code, course_name,
            course_type, credits, cie_max, see_max, total_max,
            syllabus_url, icon, description
        ) VALUES ('2025', 'AIDS', 1, '25MAT101', 'Calculus & Computational Linear Algebra', 'BSC', 4, 50, 50, 100, 'https://vtu.ac.in/en/b-e-scheme-syllabus/', 'fa-calculator', 'Next-Gen VTU 2025 Scheme Foundation Mathematics')
    """)


def seed_sample_student_data(user_id, branch_code='AIDS', scheme_code='2022'):
    conn = get_db()
    cursor = conn.cursor()

    # NOTE: We DO NOT insert fake or random marks. Marks must be original and accurate, imported from official VTU Results.

    # Activity points seed
    act_count = cursor.execute("SELECT COUNT(*) FROM activity_points WHERE user_id = ?", (user_id,)).fetchone()[0]
    if act_count == 0:
        activities = [
            (user_id, "Smart India Hackathon (SIH) 2024 Finalist", "Hackathons", "2024-09-15", "Ministry of Education & AICTE", "National level hackathon software edition", 20, "https://sih.gov.in", "Approved"),
            (user_id, "VTU Inter-Collegiate State Level Tech Fest", "Technical events", "2024-11-20", "VTU Belagavi", "Presented paper on Distributed Machine Learning Systems", 15, "https://vtu.ac.in", "Approved"),
            (user_id, "AWS Certified Cloud Practitioner Workshop", "Workshops", "2024-08-10", "AWS Academy & EduSpark", "Hands-on cloud architecture and serverless lab", 10, "", "Approved"),
            (user_id, "NSS 7-Day Rural Cleanliness & Digital Literacy Camp", "NSS", "2024-02-14", "NSS Karnataka Unit", "Conducted rural school computer literacy drive", 20, "", "Approved"),
            (user_id, "Google Developer Student Clubs (GDSC) Android Jam", "Innovation", "2024-05-18", "GDSC Chapter", "Built community problem-solving Flutter app", 10, "", "Approved")
        ]
        cursor.executemany("""
            INSERT INTO activity_points (
                user_id, activity_name, category, activity_date, organization, description, points, certificate_url, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, activities)

    # Internship seed
    int_count = cursor.execute("SELECT COUNT(*) FROM internships WHERE user_id = ?", (user_id,)).fetchone()[0]
    if int_count == 0:
        cursor.execute("""
            INSERT INTO internships (
                user_id, company, domain, start_date, end_date, duration, internship_type,
                mentor_name, status, report_status, presentation_status, certificate_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, "Infosys Springboard", "Data Science & Big Data Engineering",
            "2024-06-01", "2024-07-28", "8 Weeks", "Industry",
            "Dr. Rajesh Kumar (Principal Architect)", "Completed", "Submitted", "Completed",
            "https://infyspringboard.onwingspan.com"
        ))

    # NPTEL seed
    nptel_count = cursor.execute("SELECT COUNT(*) FROM nptel_courses WHERE user_id = ?", (user_id,)).fetchone()[0]
    if nptel_count == 0:
        cursor.execute("""
            INSERT INTO nptel_courses (
                user_id, course_name, provider, duration, course_url, credits,
                enrollment_info, weekly_plan, assignment_tracker, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, "Deep Learning by Prof. Mitesh Khapra (IIT Madras)",
            "Swayam / NPTEL", "12 Weeks", "https://nptel.ac.in/courses/106106184",
            3, "Roll: NPTEL24CS98S23 - Verified Enrollment",
            "Weeks 1-4: Feedforward & Optimization | Weeks 5-8: CNNs & Computer Vision | Weeks 9-12: RNNs & Transformers",
            "10/12 Assignments Submitted (Avg Score: 88%)", "Ongoing"
        ))

    conn.commit()
    conn.close()


def calculate_student_gpa(user_id):
    """
    Computes SGPA per semester and overall CGPA using official VTU CBCS credit formula (VTU Results / VTU Verse standard):
    SGPA = sum(Credits * GradePoint) / sum(Credits) for given semester
    CGPA = sum(All Credits * GradePoint) / sum(All Credits)
    Percentage = (CGPA - 0.75) * 10
    """
    conn = get_db()
    cursor = conn.cursor()

    marks = cursor.execute("""
        SELECT sm.semester, sm.grade_point, sm.total_marks, sm.result, c.credits, c.course_code, c.course_name
        FROM student_marks sm
        JOIN courses c ON sm.course_id = c.id
        WHERE sm.user_id = ?
        ORDER BY sm.semester ASC
    """, (user_id,)).fetchall()

    conn.close()

    if not marks:
        return {
            "sgpa_by_sem": {},
            "cgpa": "Pending",
            "percentage": "Pending",
            "vtu_class": "Awaiting Results",
            "total_credits_earned": 0,
            "total_registered_credits": 0,
            "total_credits_scheme": 160,
            "completed_subjects": 0,
            "remaining_subjects": 42,
            "progress_percentage": 0.0,
            "has_official_results": False
        }

    sem_totals = {}
    all_registered_credits = 0
    all_weighted_gp = 0
    passed_credits = 0
    completed_subjects = 0

    for row in marks:
        sem, gp, total_m, res, cr = row["semester"], row["grade_point"], row["total_marks"], row["result"], row["credits"]
        if sem not in sem_totals:
            sem_totals[sem] = {"weighted_gp": 0, "credits": 0, "courses": 0}
        
        # In VTU CBCS: Failed course has GP 0, but credits are registered in denominator
        sem_totals[sem]["weighted_gp"] += (gp * cr)
        sem_totals[sem]["credits"] += cr
        sem_totals[sem]["courses"] += 1

        all_registered_credits += cr
        all_weighted_gp += (gp * cr)

        if gp >= 4 and res == 'Pass':
            completed_subjects += 1
            passed_credits += cr

    sgpa_by_sem = {}
    for sem, data in sem_totals.items():
        if data["credits"] > 0:
            sgpa_by_sem[sem] = round(data["weighted_gp"] / data["credits"], 2)
        else:
            sgpa_by_sem[sem] = 0.0

    cgpa = round(all_weighted_gp / all_registered_credits, 2) if all_registered_credits > 0 else 0.0
    
    # VTU Official Percentage formula: (CGPA - 0.75) * 10 (as used in VTU Results & VTU Verse)
    percentage = round((cgpa - 0.75) * 10, 2) if cgpa >= 0.75 else round(cgpa * 10, 2)
    progress_percentage = min(100.0, round((passed_credits / 160.0) * 100, 1))

    # Official VTU Class Classification (CBCS Regulation)
    vtu_class = "First Class with Distinction" if cgpa >= 7.75 else (
        "First Class" if cgpa >= 6.75 else (
            "Second Class" if cgpa >= 5.75 else (
                "Pass Class" if cgpa >= 5.0 else "Fail / Backlog"
            )
        )
    )

    return {
        "sgpa_by_sem": sgpa_by_sem,
        "cgpa": cgpa,
        "percentage": percentage,
        "vtu_class": vtu_class,
        "total_credits_earned": round(passed_credits, 1),
        "total_registered_credits": round(all_registered_credits, 1),
        "total_credits_scheme": 160,
        "completed_subjects": completed_subjects,
        "remaining_subjects": max(0, 42 - completed_subjects),
        "progress_percentage": progress_percentage,
        "has_official_results": (all_registered_credits > 0)
    }

if __name__ == "__main__":
    init_vtu_db()
