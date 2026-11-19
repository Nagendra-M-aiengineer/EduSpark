import sqlite3

DATABASE = "eduspark.db"

def seed_rich_subject_units():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Subject 1: Deep Learning and Reinforcement Learning (BAD701)
    dl_row = cursor.execute("SELECT id FROM courses WHERE course_code = 'BAD701'").fetchone()
    if dl_row:
        dl_id = dl_row[0]
        # Check if units already exist
        if cursor.execute("SELECT COUNT(*) FROM course_units WHERE course_id = ?", (dl_id,)).fetchone()[0] == 0:
            dl_units = [
                (
                    dl_id, 1, "Deep Forward Networks & Optimization for Deep Models", 8,
                    "Example: Learning XOR, Gradient-Based Learning, Hidden Units (ReLU, Sigmoid, Tanh, Maxout), Architecture Design, Regularization for Deep Learning (Weight decay, Dropout, Data augmentation), Optimization (SGD, Momentum, RMSProp, Adam).",
                    "Deep forward networks (multilayer perceptrons) approximate mathematical functions through composed layers. Optimization algorithms like Adam adaptively scale learning rates to slide down error surfaces quickly.",
                    "Think of descending a foggy mountain in skis. Momentum keeps you sliding past small bumps, and Adam adjusts your ski wax depending on whether the snow is slushy or icy.",
                    """<svg viewBox="0 0 700 160" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                        <rect x="30" y="40" width="120" height="70" rx="12" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                        <text x="90" y="70" text-anchor="middle" font-size="12" font-weight="bold">Input Features</text>
                        <text x="90" y="90" text-anchor="middle" font-size="10" fill="#4338ca">X1, X2... Xn</text>
                        <path d="M150 75 L220 75" stroke="#4f46e5" stroke-width="2"/>
                        <rect x="220" y="30" width="140" height="90" rx="12" fill="#fae8ff" stroke="#a855f7" stroke-width="2"/>
                        <text x="290" y="65" text-anchor="middle" font-size="12" font-weight="bold">ReLU Hidden Layers</text>
                        <text x="290" y="85" text-anchor="middle" font-size="10" fill="#7e22ce">f(x) = max(0, x)</text>
                        <text x="290" y="103" text-anchor="middle" font-size="10" fill="#7e22ce">+ Dropout (p=0.5)</text>
                        <path d="M360 75 L430 75" stroke="#a855f7" stroke-width="2"/>
                        <rect x="430" y="30" width="130" height="90" rx="12" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
                        <text x="495" y="65" text-anchor="middle" font-size="12" font-weight="bold">Adam Optimizer</text>
                        <text x="495" y="85" text-anchor="middle" font-size="10" fill="#b45309">1st &amp; 2nd Moment</text>
                        <text x="495" y="103" text-anchor="middle" font-size="10" fill="#b45309">Estimations</text>
                        <path d="M560 75 L620 75" stroke="#d97706" stroke-width="2"/>
                        <rect x="620" y="40" width="60" height="70" rx="12" fill="#dcfce7" stroke="#16a34a"/>
                        <text x="650" y="80" text-anchor="middle" font-size="12" font-weight="bold" fill="#14532d">Loss</text>
                    </svg>""",
                    "• ReLU (Rectified Linear Unit): g(z) = max(0, z). Avoids vanishing gradients that plague Sigmoid.\n• Dropout: Randomly zeros activations during training with probability p to prevent co-adaptation of neurons.\n• Adam: Combines Momentum (moving average of gradients) and RMSProp (moving average of squared gradients).",
                    "1. Explain why ReLU is preferred over Sigmoid in deep networks. (VTU 2024, 6 marks)\n2. Formulate the Adam optimization update algorithm. (VTU 2023, 10 marks)\n3. How does Dropout regularize deep neural networks? (VTU 2024, 8 marks)"
                ),
                (
                    dl_id, 2, "Convolutional Neural Networks (CNNs)", 8,
                    "The Convolution Operation, Motivation: Sparse interactions, Parameter sharing, Equivariance, Pooling (Max pooling, Average pooling), Convolution and Pooling as an Infinitely Strong Prior, Strides, Padding, Famous architectures: LeNet, AlexNet, VGG, ResNet.",
                    "CNNs are specialized neural networks for grid-structured data like images. Instead of connecting every pixel to every neuron, CNNs slide small feature filters across the image to detect edges, textures, and objects.",
                    "Like an art detective examining a painting with a small magnifying glass (kernel), sliding row-by-row to spot signatures and brush strokes without needing to see the whole canvas at once.",
                    """<svg viewBox="0 0 700 160" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                        <rect x="30" y="35" width="110" height="80" rx="8" fill="#e0e7ff" stroke="#4f46e5"/>
                        <text x="85" y="70" text-anchor="middle" font-size="11" font-weight="bold">Input Image</text>
                        <text x="85" y="90" text-anchor="middle" font-size="10" fill="#4338ca">224×224×3</text>
                        <path d="M140 75 L180 75" stroke="#4f46e5" stroke-width="2"/>
                        <rect x="180" y="35" width="110" height="80" rx="8" fill="#fae8ff" stroke="#a855f7"/>
                        <text x="235" y="70" text-anchor="middle" font-size="11" font-weight="bold">Conv2D (3×3)</text>
                        <text x="235" y="90" text-anchor="middle" font-size="10" fill="#7e22ce">64 Filters</text>
                        <path d="M290 75 L330 75" stroke="#a855f7" stroke-width="2"/>
                        <rect x="330" y="45" width="100" height="60" rx="8" fill="#fef3c7" stroke="#d97706"/>
                        <text x="380" y="75" text-anchor="middle" font-size="11" font-weight="bold">Max Pool 2×2</text>
                        <text x="380" y="93" text-anchor="middle" font-size="10" fill="#b45309">Downsampling</text>
                        <path d="M430 75 L470 75" stroke="#d97706" stroke-width="2"/>
                        <rect x="470" y="30" width="100" height="90" rx="8" fill="#fbcfe8" stroke="#db2777"/>
                        <text x="520" y="70" text-anchor="middle" font-size="11" font-weight="bold">ResNet Skip</text>
                        <text x="520" y="90" text-anchor="middle" font-size="10" fill="#9d174d">F(x) + x</text>
                        <path d="M570 75 L610 75" stroke="#db2777" stroke-width="2"/>
                        <rect x="610" y="40" width="70" height="70" rx="8" fill="#dcfce7" stroke="#16a34a"/>
                        <text x="645" y="80" text-anchor="middle" font-size="12" font-weight="bold" fill="#14532d">Class</text>
                    </svg>""",
                    "• Sparse Connectivity: Neurons in layer m connect only to small local patches of layer m-1.\n• Parameter Sharing: The same kernel weights are reused across the entire image.\n• ResNet Residual Connections: y = F(x) + x allows training networks with 100+ layers without vanishing gradients.",
                    "1. Detail the three foundational properties of CNNs: Sparse Interactions, Parameter Sharing, and Equivariance. (VTU 2024, 10 marks)\n2. Explain the architecture of ResNet and discuss why residual connections solve the degradation problem. (VTU 2023, 10 marks)"
                )
            ]
            cursor.executemany("""
                INSERT INTO course_units (
                    course_id, unit_number, unit_title, hours,
                    syllabus_content, simplified_explanation, real_life_analogy,
                    visual_diagram_svg, key_notes, vtu_exam_questions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, dl_units)

    # Subject 2: Operating Systems (BCS303)
    os_row = cursor.execute("SELECT id FROM courses WHERE course_code = 'BCS303'").fetchone()
    if os_row:
        os_id = os_row[0]
        if cursor.execute("SELECT COUNT(*) FROM course_units WHERE course_id = ?", (os_id,)).fetchone()[0] == 0:
            os_units = [
                (
                    os_id, 1, "Introduction to Operating Systems & System Calls", 8,
                    "What Operating Systems Do, Computer-System Organization and Architecture, Operating-System Structure, Operating-System Operations, Process Management, Memory Management, Storage Management, Protection and Security, Computing Environments, Operating-System Services, User and Operating-System Interface, System Calls, Types of System Calls, System Programs.",
                    "An Operating System is a resource manager and abstract interface between computer hardware and software applications. System calls provide the programmatic interface through which a program requests services from the OS kernel.",
                    "The OS is like the manager of a busy restaurant: the CPU is the chef, RAM is the kitchen counter, hard drive is the pantry, and system calls are the orders placed by waiters.",
                    """<svg viewBox="0 0 700 150" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                        <rect x="50" y="30" width="180" height="90" rx="14" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                        <text x="140" y="65" text-anchor="middle" font-size="14" font-weight="bold" fill="#312e81">User Space</text>
                        <text x="140" y="90" text-anchor="middle" font-size="11" fill="#4338ca">User Application Code</text>
                        <path d="M230 75 L350 75" stroke="#4f46e5" stroke-width="3"/>
                        <text x="290" y="65" text-anchor="middle" font-size="11" font-weight="bold" fill="#4f46e5">Trap / Syscall</text>
                        <rect x="350" y="30" width="300" height="90" rx="14" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
                        <text x="500" y="65" text-anchor="middle" font-size="14" font-weight="bold" fill="#14532d">Kernel Space (Privileged Mode)</text>
                        <text x="500" y="90" text-anchor="middle" font-size="11" fill="#15803d">File I/O, Memory Allocation, Device Control</text>
                    </svg>""",
                    "• Dual-Mode Operation: User mode (bit 1) and Kernel mode (bit 0) protect system resources.\n• Five categories of System Calls: Process control, File management, Device management, Information maintenance, Communications.",
                    "1. What is a system call? Explain the sequence of steps when a user invokes a read() system call. (VTU 2023, 8 marks)\n2. Explain Dual-Mode operation and how the timer interrupts malicious user loops. (VTU 2024, 8 marks)"
                ),
                (
                    os_id, 2, "Process Management & CPU Scheduling", 8,
                    "Process Concept: Process State, Process Control Block (PCB), Process Scheduling, Operations on Processes. CPU Scheduling: Basic Concepts, Scheduling Criteria, Scheduling Algorithms: FCFS, SJF, Priority, Round Robin, Multilevel Queue Scheduling, Thread Scheduling.",
                    "A process is a program in execution. The CPU scheduler decides which ready process receives the CPU core next, balancing throughput, response time, and fairness.",
                    "Round Robin scheduling is like a carousel ride: each child gets 2 minutes on the pony, and if they want another ride, they join the back of the queue.",
                    """<svg viewBox="0 0 700 150" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="80" cy="75" r="30" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                        <text x="80" y="80" text-anchor="middle" font-size="11" font-weight="bold">NEW</text>
                        <line x1="110" y1="75" x2="190" y2="75" stroke="#4f46e5" stroke-width="2"/>
                        <circle cx="220" cy="75" r="30" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
                        <text x="220" y="80" text-anchor="middle" font-size="11" font-weight="bold">READY</text>
                        <line x1="250" y1="75" x2="330" y2="75" stroke="#4f46e5" stroke-width="2"/>
                        <circle cx="360" cy="75" r="30" fill="#fae8ff" stroke="#a855f7" stroke-width="2"/>
                        <text x="360" y="80" text-anchor="middle" font-size="11" font-weight="bold">RUNNING</text>
                        <line x1="390" y1="75" x2="470" y2="75" stroke="#4f46e5" stroke-width="2"/>
                        <circle cx="500" cy="75" r="30" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
                        <text x="500" y="80" text-anchor="middle" font-size="11" font-weight="bold">TERMINATED</text>
                        <path d="M360 105 L360 135 L220 135 L220 105" fill="none" stroke="#64748b" stroke-width="2"/>
                        <text x="290" y="145" text-anchor="middle" font-size="10" fill="#64748b">Interrupt / Time Quantum Expired</text>
                    </svg>""",
                    "• Process Control Block (PCB): Holds PID, Program Counter, Registers, Memory limits, Open files.\n• Preemptive vs Non-preemptive scheduling.\n• Round Robin (RR): Ready queue is treated as circular FIFO. Each process is assigned time quantum q (typically 10-100 ms).",
                    "1. For the given set of processes with arrival time and burst time, draw Gantt chart and compute average turnaround and waiting time using SJF and Round Robin (q=2). (VTU 2024, 12 marks)\n2. Explain the components of PCB and state diagram of a process. (VTU 2023, 8 marks)"
                )
            ]
            cursor.executemany("""
                INSERT INTO course_units (
                    course_id, unit_number, unit_title, hours,
                    syllabus_content, simplified_explanation, real_life_analogy,
                    visual_diagram_svg, key_notes, vtu_exam_questions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, os_units)

    # Subject 3: Database Management Systems (BCS403)
    db_row = cursor.execute("SELECT id FROM courses WHERE course_code = 'BCS403'").fetchone()
    if db_row:
        db_id = db_row[0]
        if cursor.execute("SELECT COUNT(*) FROM course_units WHERE course_id = ?", (db_id,)).fetchone()[0] == 0:
            db_units = [
                (
                    db_id, 1, "Introduction to Database Systems & ER Modeling", 8,
                    "Characteristics of database approach, Actors on the scene, Workers behind the scene, Advantages of using DBMS, Data models, Schemas, and Instances, Three-Schema architecture and Data Independence, Database languages and Interfaces, ER model concepts, Entities, Attributes, Relationships, Constraints, Enhanced ER (EER) modeling.",
                    "A Database Management System manages organized collections of data with ACID guarantees (Atomicity, Consistency, Isolation, Durability). ER diagrams visually capture real-world entities and associations before writing schema SQL.",
                    "An ER diagram is like the architect's blueprint for a house: before laying bricks (creating tables in SQL), you draft rooms (entities) and doorways (relationships).",
                    """<svg viewBox="0 0 700 150" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                        <rect x="50" y="45" width="130" height="60" rx="8" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
                        <text x="115" y="80" text-anchor="middle" font-size="14" font-weight="bold">STUDENT</text>
                        <line x1="180" y1="75" x2="260" y2="75" stroke="#4f46e5" stroke-width="2"/>
                        <polygon points="310,40 360,75 310,110 260,75" fill="#fae8ff" stroke="#a855f7" stroke-width="2"/>
                        <text x="310" y="80" text-anchor="middle" font-size="11" font-weight="bold">Enrolls_In</text>
                        <line x1="360" y1="75" x2="440" y2="75" stroke="#4f46e5" stroke-width="2"/>
                        <rect x="440" y="45" width="130" height="60" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
                        <text x="505" y="80" text-anchor="middle" font-size="14" font-weight="bold">COURSE</text>
                    </svg>""",
                    "• Three-Schema Architecture: Internal (physical storage), Conceptual (logical tables/keys), and External (user views).\n• Logical Data Independence: Changing conceptual schema without having to change external views.\n• Cardinality ratios: 1:1, 1:N, M:N.",
                    "1. Explain Three-Schema Architecture and discuss Physical vs Logical data independence. (VTU 2023, 8 marks)\n2. Design an ER diagram for a University Management System specifying primary keys, structural constraints, and weak entities. (VTU 2024, 10 marks)"
                ),
                (
                    db_id, 2, "Relational Model, SQL & Normalization", 8,
                    "Relational model constraints: Domain, Key, Integrity, Foreign keys. SQL: DDL, DML, Nested queries, Aggregates, Joins. Normalization: Functional dependencies, 1NF, 2NF, 3NF, BCNF, Multivalued dependencies, 4NF.",
                    "Normalization decomposes tables to eliminate redundancy, avoid insert/update/delete anomalies, and preserve dependencies.",
                    "Organizing a messy closet into dedicated labelled bins: socks in one drawer, shirts in another. If you buy a new shirt, you don't need to rewrite the sock drawer.",
                    """<svg viewBox="0 0 700 150" class="concept-svg" xmlns="http://www.w3.org/2000/svg">
                        <rect x="30" y="45" width="110" height="60" rx="10" fill="#fef3c7" stroke="#d97706"/>
                        <text x="85" y="70" text-anchor="middle" font-size="12" font-weight="bold">1NF</text>
                        <text x="85" y="90" text-anchor="middle" font-size="10" fill="#78350f">Atomic Values</text>
                        <path d="M140 75 L190 75" stroke="#d97706" stroke-width="2"/>
                        <rect x="190" y="45" width="120" height="60" rx="10" fill="#e0e7ff" stroke="#4f46e5"/>
                        <text x="250" y="70" text-anchor="middle" font-size="12" font-weight="bold">2NF</text>
                        <text x="250" y="90" text-anchor="middle" font-size="10" fill="#312e81">No Partial FDs</text>
                        <path d="M310 75 L360 75" stroke="#4f46e5" stroke-width="2"/>
                        <rect x="360" y="45" width="130" height="60" rx="10" fill="#fae8ff" stroke="#a855f7"/>
                        <text x="425" y="70" text-anchor="middle" font-size="12" font-weight="bold">3NF</text>
                        <text x="425" y="90" text-anchor="middle" font-size="10" fill="#581c87">No Transitive FDs</text>
                        <path d="M490 75 L540 75" stroke="#a855f7" stroke-width="2"/>
                        <rect x="540" y="45" width="130" height="60" rx="10" fill="#dcfce7" stroke="#16a34a"/>
                        <text x="605" y="70" text-anchor="middle" font-size="12" font-weight="bold">BCNF</text>
                        <text x="605" y="90" text-anchor="middle" font-size="10" fill="#14532d">Every det is superkey</text>
                    </svg>""",
                    "• 1NF: Disallows multi-valued or composite attributes (all table cells are atomic).\n• 2NF: In 1NF and no non-prime attribute is partially dependent on any candidate key.\n• 3NF: In 2NF and no non-prime attribute is transitively dependent on candidate keys.\n• BCNF: In 3NF and for every functional dependency X -> Y, X must be a superkey.",
                    "1. Define 1NF, 2NF, 3NF and BCNF with concrete counter-examples. (VTU 2024, 10 marks)\n2. Given R(A, B, C, D, E) and F = {A->B, BC->E, ED->A}, find candidate keys and highest normal form. (VTU 2023, 10 marks)"
                )
            ]
            cursor.executemany("""
                INSERT INTO course_units (
                    course_id, unit_number, unit_title, hours,
                    syllabus_content, simplified_explanation, real_life_analogy,
                    visual_diagram_svg, key_notes, vtu_exam_questions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, db_units)

    conn.commit()
    conn.close()
    print("Rich course units seeded successfully.")

if __name__ == "__main__":
    seed_rich_subject_units()
