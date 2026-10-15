const menuToggle = document.querySelector("#menu-toggle");
const sideMenu = document.querySelector("#sidemenu");
const themeToggle = document.querySelector("#theme-toggle");
const navbar = document.querySelector(".navbar");
const scrollTopButton = document.querySelector("#scroll-top");

const projectsStatus = document.querySelector("#projects-status");
const projectsList = document.querySelector("#projects-list");

const contactForm = document.querySelector("#contact-form");
const formStatus = document.querySelector("#form-status");

const projectApiUrl = "https://api.github.com/users/ji-min0/repos?sort=updated&per_page=100";

// 모바일 메뉴
const menuClose = document.querySelector("#menu-close");

function closeMenu() {
    sideMenu.classList.remove("active");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "메뉴 열기");
    menuToggle.innerHTML =
        '<i class="fas fa-bars" aria-hidden="true"></i>';
}

menuToggle.addEventListener("click", () => {
    const isOpen = sideMenu.classList.toggle("active");

    menuToggle.setAttribute("aria-expanded", String(isOpen));
    menuToggle.setAttribute(
        "aria-label",
        isOpen ? "메뉴 닫기" : "메뉴 열기"
    );

    menuToggle.innerHTML = isOpen
        ? '<i class="fas fa-xmark" aria-hidden="true"></i>'
        : '<i class="fas fa-bars" aria-hidden="true"></i>';
});

menuClose.addEventListener("click", closeMenu);

sideMenu.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener("click", closeMenu);
});

// 다크 모드
const savedTheme = localStorage.getItem("portfolio-theme");
const initialTheme =
    savedTheme === "light" || savedTheme === "dark"
        ? savedTheme
        : "light";

document.documentElement.dataset.theme = initialTheme;

function updateThemeButton() {
    const isDark = document.documentElement.dataset.theme === "dark";

    themeToggle.innerHTML = isDark
        ? '<i class="fas fa-sun" aria-hidden="true"></i>'
        : '<i class="fas fa-moon" aria-hidden="true"></i>';

    themeToggle.setAttribute(
        "aria-label",
        isDark ? "라이트 모드로 변경" : "다크 모드로 변경"
    );
}

updateThemeButton();

themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.dataset.theme;
    const nextTheme = currentTheme === "dark" ? "light" : "dark";

    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem("portfolio-theme", nextTheme);

    updateThemeButton();
});

// 스크롤에 따른 내비게이션과 맨 위로 버튼
function updateScrollUI() {
    const scrollY = window.scrollY;

    navbar.classList.toggle("scrolled", scrollY >= 60);
    scrollTopButton.hidden = scrollY < 300;
}

window.addEventListener("scroll", updateScrollUI, { passive: true });
updateScrollUI();

scrollTopButton.addEventListener("click", () => {
    window.scrollTo({
        top: 0,
        behavior: "smooth",
    });
});

// 스크롤 애니메이션
const revealElements = document.querySelectorAll(".reveal");

if ("IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver(
        (entries, observer) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        {
            threshold: 0.2,
        }
    );

    revealElements.forEach((element) => {
        revealObserver.observe(element);
    });
} else {
    revealElements.forEach((element) => {
        element.classList.add("visible");
    });
}

// API 데이터에 포함된 HTML 특수문자 처리
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        };

        return entities[character];
    });
}

// GitHub 프로젝트 카드 렌더링
function renderProjects(repositories) {
    projectsList.innerHTML = repositories
        .map((repository) => {
            const name = escapeHTML(repository.name);
            const description = escapeHTML(
                repository.description || "등록된 프로젝트 설명이 없습니다."
            );
            const language = escapeHTML(repository.language || "미지정");
            const stars = Number(repository.stargazers_count) || 0;
            const url = escapeHTML(repository.html_url);

            return `
                <article class="work">
                    <div class="work-content">
                        <i class="fab fa-github work-icon" aria-hidden="true"></i>
                        <h3>${name}</h3>
                        <p>${description}</p>

                        <div class="project-meta">
                            <span>Language: ${language}</span>
                            <span>
                                <i class="fas fa-star" aria-hidden="true"></i>
                                ${stars}
                            </span>
                        </div>

                        <a
                            class="project-link"
                            href="${url}"
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label="${name} GitHub 저장소 열기"
                        >
                            View Repository
                            <i class="fas fa-arrow-up-right-from-square"
                               aria-hidden="true"></i>
                        </a>
                    </div>
                </article>
            `;
        })
        .join("");
}

// GitHub API 상태 관리
async function loadProjects() {
    projectsStatus.textContent = "프로젝트를 불러오는 중...";
    projectsList.innerHTML = "";

    try {
        const response = await fetch(projectApiUrl);

        if (!response.ok) {
            throw new Error(`GitHub API 요청 실패: ${response.status}`);
        }

        const repositories = await response.json();
        const filteredRepositories = repositories.filter((repository) =>
            repository.name.toLowerCase().startsWith("codyssey")
        );

        if (!Array.isArray(repositories)) {
            throw new Error("올바르지 않은 API 응답입니다.");
        }

        if (filteredRepositories.length === 0) {
            projectsStatus.textContent = "표시할 프로젝트가 없습니다.";
            return;
        }

        renderProjects(filteredRepositories);
        projectsStatus.textContent = "";
    } catch (error) {
        console.error("프로젝트 로딩 실패:", error);

        projectsStatus.innerHTML = `
            <p>프로젝트를 불러올 수 없습니다.</p>
            <button class="retry-button" id="retry-projects" type="button">
                다시 시도
            </button>
        `;

        document
            .querySelector("#retry-projects")
            .addEventListener("click", loadProjects);
    }
}

loadProjects();

// 문의 폼 유효성 검사
const nameInput = document.querySelector("#contact-name");
const emailInput = document.querySelector("#contact-email");
const messageInput = document.querySelector("#contact-message");

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function showFieldError(input, message) {
    const errorElement = document.querySelector(
        `#${input.id.replace("contact-", "")}-error`
    );

    errorElement.textContent = message;
    input.classList.toggle("invalid", Boolean(message));
    input.setAttribute("aria-invalid", String(Boolean(message)));
}

function validateField(input) {
    const value = input.value.trim();
    let errorMessage = "";

    if (!value) {
        errorMessage = "필수 입력 항목입니다.";
    } else if (input === emailInput && !emailPattern.test(value)) {
        errorMessage = "올바른 이메일 형식을 입력해 주세요.";
    }

    showFieldError(input, errorMessage);

    return errorMessage === "";
}

const formInputs = [nameInput, emailInput, messageInput];

formInputs.forEach((input) => {
    input.addEventListener("input", () => {
        validateField(input);
        formStatus.textContent = "";
    });
});

contactForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const validationResults = formInputs.map((input) =>
        validateField(input)
    );

    if (validationResults.includes(false)) {
        formStatus.textContent = "입력 내용을 확인해 주세요.";

        const firstInvalidInput = formInputs.find(
            (input) => input.getAttribute("aria-invalid") === "true"
        );

        firstInvalidInput?.focus();
        return;
    }

    formStatus.textContent =
        "입력 확인이 완료되었습니다.";

    contactForm.reset();

    formInputs.forEach((input) => {
        showFieldError(input, "");
    });
});