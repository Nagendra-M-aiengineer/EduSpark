/* ==========================================
   EDUSPARK VTU ACADEMIC FRONTEND SCRIPT
========================================== */

/* ================= TOAST ================= */
function showToast(message) {
    let toast = document.getElementById("toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "toast";
        toast.className = "toast";
        toast.innerHTML = `<i class="fa-solid fa-check"></i> <span id="toastMessage"></span>`;
        document.body.appendChild(toast);
    }
    const messageElement = document.getElementById("toastMessage") || toast;
    messageElement.textContent = message;
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 3200);
}

/* ================= NAVIGATION ACTIONS ================= */
function startLearning() {
    window.location.href = "/register";
}

function exploreCourses() {
    const el = document.getElementById("courses");
    if (el) {
        el.scrollIntoView({ behavior: "smooth" });
    } else {
        window.location.href = "/syllabus";
    }
}

function openCourse(courseId) {
    if (typeof courseId === "number" || (!isNaN(courseId) && courseId > 0)) {
        window.location.href = `/course/${courseId}`;
    } else {
        window.location.href = "/syllabus";
    }
}

function startQuiz() {
    window.location.href = "/mock-tests";
}

function startPractice() {
    window.location.href = "/mock-tests";
}

function showChallenges() {
    window.location.href = "/activity-points";
}

function quickJumpSyllabus() {
    const scheme = document.getElementById("quickScheme") ? document.getElementById("quickScheme").value : "2022";
    const branch = document.getElementById("quickBranch") ? document.getElementById("quickBranch").value : "AIDS";
    const sem = document.getElementById("quickSem") ? document.getElementById("quickSem").value : "6";
    window.location.href = `/syllabus?scheme=${scheme}&branch=${branch}&sem=${sem}`;
}

/* ================= AI STUDY BUDDY API ================= */
async function askAI(customQuestion) {
    const input = document.getElementById("questionInput");
    const response = document.getElementById("aiResponse");

    const question = customQuestion || (input ? input.value.trim() : "");
    if (!question) {
        showToast("Please enter an engineering question first.");
        return;
    }

    if (input) input.value = question;
    if (response) {
        response.style.display = "block";
        response.innerHTML = `
            <div style="padding: 16px; text-align: center; color: var(--primary);">
                <i class="fa-solid fa-spinner fa-spin" style="font-size: 20px; margin-bottom: 8px;"></i>
                <div>Analyzing VTU scheme & generating simplified concept breakdown...</div>
            </div>
        `;
    }

    try {
        const result = await fetch("/api/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question })
        });

        if (!result.ok) throw new Error("Backend unavailable");

        const data = await result.json();
        if (response) {
            response.innerHTML = `
                <div style="background: var(--surface-alt); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: left;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: var(--primary); font-weight: 800;">
                        <i class="fa-solid fa-robot"></i> EduSpark AI Study Assistant
                    </div>
                    ${data.answer}
                </div>
            `;
        }
    } catch (error) {
        if (response) {
            response.innerHTML = `
                <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid #dc2626; border-radius: 12px; padding: 16px; color: #dc2626;">
                    <i class="fa-solid fa-circle-exclamation"></i> Unable to reach AI service right now. Please verify Flask server connection.
                </div>
            `;
        }
    }
}

/* ================= DARK / LIGHT THEME ================= */
function applyTheme(theme) {
    if (theme === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
        document.body.classList.add("dark-theme");
        const btns = document.querySelectorAll("#themeBtn, .theme-toggle");
        btns.forEach(btn => { btn.innerHTML = `<i class="fa-solid fa-sun"></i>`; });
    } else {
        document.documentElement.setAttribute("data-theme", "light");
        document.body.classList.remove("dark-theme");
        const btns = document.querySelectorAll("#themeBtn, .theme-toggle");
        btns.forEach(btn => { btn.innerHTML = `<i class="fa-solid fa-moon"></i>`; });
    }
}

const savedTheme = localStorage.getItem("eduspark_theme") || "light";
applyTheme(savedTheme);

document.addEventListener("DOMContentLoaded", () => {
    const themeBtns = document.querySelectorAll("#themeBtn, .theme-toggle");
    themeBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const isDark = document.documentElement.getAttribute("data-theme") === "dark";
            const newTheme = isDark ? "light" : "dark";
            applyTheme(newTheme);
            localStorage.setItem("eduspark_theme", newTheme);
            showToast(`${newTheme === "dark" ? "Dark" : "Light"} mode enabled`);
        });
    });

    const qInput = document.getElementById("questionInput");
    if (qInput) {
        qInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                askAI();
            }
        });
    }

    // Static Server / Live Server Detection
    const isStaticServer = window.location.protocol === "file:" || (window.location.port && window.location.port !== "5000");
    if (isStaticServer) {
        // Intercept internal links to redirect to port 5000 Flask server
        document.querySelectorAll("a[href^='/'], a[href^='templates/']").forEach(link => {
            const rawHref = link.getAttribute("href");
            if (rawHref && !rawHref.startsWith("#") && !rawHref.startsWith("http")) {
                link.addEventListener("click", (e) => {
                    e.preventDefault();
                    let targetPath = rawHref.replace(/^templates\//, "/");
                    if (!targetPath.startsWith("/")) targetPath = "/" + targetPath;
                    window.location.href = `http://127.0.0.1:5000${targetPath}`;
                });
            }
        });

        // Add prominent notice banner
        const banner = document.createElement("div");
        banner.style.cssText = "position:sticky; top:0; z-index:99999; background:linear-gradient(90deg, #4f46e5, #06b6d4); color:white; padding:12px 20px; font-size:14px; font-weight:700; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.15); display:flex; justify-content:center; align-items:center; gap:14px; flex-wrap:wrap;";
        banner.innerHTML = `
            <span><i class="fa-solid fa-triangle-exclamation"></i> Live Server Detected (Port ${window.location.port || 'file'}). To use full VTU marks, database & AI features:</span>
            <a href="http://127.0.0.1:5000" style="background:white; color:#4f46e5; padding:6px 16px; border-radius:999px; text-decoration:none; font-weight:800; font-size:13px; display:inline-flex; align-items:center; gap:6px;">
                <i class="fa-solid fa-bolt"></i> Open EduSpark on Port 5000
            </a>
        `;
        document.body.insertBefore(banner, document.body.firstChild);
    }
});
