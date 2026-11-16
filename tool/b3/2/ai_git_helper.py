#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass

try:
    import anthropic
except ImportError:
    print("[오류] anthropic 패키지가 설치되지 않았습니다.")
    print("       설치 방법: pip3 install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[경고] python-dotenv 패키지가 설치되지 않았습니다.")
    print("       .env 파일을 사용하려면 설치하세요: pip3 install python-dotenv")
    print("       시스템 환경변수는 계속 사용 가능합니다.\n")


DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://copa.codyssey.kr")

PROMPT_DIFF_LIMIT = 3000
PLACEHOLDER_BULLET = "- (작성 필요)"
INDENT = " " * 11
HINT_INDENT = " " * 7

# APITimeoutError는 APIConnectionError의 하위 클래스라 먼저 둔다.
API_ERROR_HINTS = [
    (anthropic.AuthenticationError, "인증 실패: ANTHROPIC_API_KEY를 확인하세요"),
    (anthropic.PermissionDeniedError, "권한 없음: API Key의 사용 권한/잔여 토큰을 확인하세요"),
    (anthropic.NotFoundError, "모델 또는 엔드포인트 없음: -m 모델 ID와 ANTHROPIC_BASE_URL을 확인하세요"),
    (anthropic.RateLimitError, "요청 한도 초과: 잠시 후 다시 시도하세요"),
    (anthropic.APITimeoutError, "응답 시간 초과: 잠시 후 다시 시도하세요"),
    (anthropic.APIConnectionError, "네트워크 오류: 인터넷 연결과 ANTHROPIC_BASE_URL을 확인하세요"),
    (anthropic.BadRequestError, "잘못된 요청: -t(0.0~1.0), --max-tokens 값을 확인하세요"),
]

# 구체적인 패턴을 먼저 적용해야 마지막 일반 토큰 패턴에 먹히지 않는다.
SENSITIVE_PATTERNS = [
    (re.compile(r'password\s*[=:]\s*["\']?[^"\'\s]+["\']?', re.IGNORECASE), "password=***MASKED***"),
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "***MASKED_EMAIL***"),
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "***MASKED_API_KEY***"),
    (re.compile(r"[A-Za-z0-9_-]{20,}"), "***MASKED_TOKEN***"),
]


@dataclass(frozen=True)
class Task:
    name: str
    request: str
    requirements: str
    body_format: str
    title_limit: int
    guide: str
    title_recommended: int = 0  # 0이면 검사 안 함
    required_sections: tuple = ()
    title_body_together: bool = False


COMMIT = Task(
    name="커밋 메시지",
    request="커밋 메시지를",
    requirements=(
        "- 커밋 제목: 50자 이내 (최대 72자)\n"
        "- 커밋 제목은 변경의 핵심을 명확하게 표현\n"
        "- 커밋 본문(선택): 변경된 파일 또는 핵심 변경 사항을 불릿으로 요약"
    ),
    body_format="- [변경 사항 1]\n- [변경 사항 2]",
    title_limit=72,
    title_recommended=50,
    guide="위 메시지를 복사하여 git commit에 사용하세요.",
    title_body_together=True,
)

PR = Task(
    name="PR",
    request="Pull Request 제목과 본문을",
    requirements=(
        "- PR 제목: 최대 80자, 변경의 핵심을 명확하게 표현\n"
        "- PR 본문: Why, What, How to Test 섹션으로 구성\n"
        "- 각 섹션에 최소 1개 이상의 불릿 포함"
    ),
    body_format=(
        "## Why (변경 배경)\n- [배경 설명 1]\n\n"
        "## What (핵심 변경 사항)\n- [변경 사항 1]\n- [변경 사항 2]\n\n"
        "## How to Test (테스트 방법)\n- [테스트 방법 1]"
    ),
    title_limit=80,
    guide="위 내용을 GitHub PR 작성 시 사용하세요.",
    required_sections=("Why", "What", "How to Test"),
)

TASKS = {"commit": COMMIT, "pr": PR}


def run_git(*args: str) -> str:
    try:
        result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError("git 명령을 찾을 수 없습니다. Git을 설치하세요.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git {' '.join(args)} 실행 실패: {e.stderr.strip()}")
    return result.stdout


def is_git_repo() -> bool:
    try:
        run_git("rev-parse", "--git-dir")
        return True
    except RuntimeError:
        return False


def get_changes(status: str) -> tuple[str, str]:
    staged = run_git("diff", "--staged")
    if not staged:
        return status, run_git("diff")
    # staged 변경이 커밋 대상이므로 파일 목록도 staged 파일(첫 글자가 공백/? 아님)만 남긴다.
    return "\n".join(line for line in status.splitlines() if line[:1] not in " ?"), staged


def apply_safe_mode(diff: str, max_files: int, max_lines: int) -> str:
    for pattern, replacement in SENSITIVE_PATTERNS:
        diff = pattern.sub(replacement, diff)

    head, *files = diff.split("diff --git")
    if len(files) > max_files:
        diff = "diff --git".join([head, *files[:max_files]])
        diff += f"\n\n... (나머지 {len(files) - max_files}개 파일 생략됨)"

    lines = diff.split("\n")
    if len(lines) > max_lines:
        diff = "\n".join(lines[:max_lines])
        diff += f"\n\n... (나머지 {len(lines) - max_lines}줄 생략됨)"

    return diff


def build_prompt(task: Task, status: str, diff: str) -> str:
    return f"""아래 Git 변경 사항을 분석하여 {task.request} 작성해주세요.

**요구사항:**
{task.requirements}
- 한글로 작성

**변경 파일 목록:**
{status}

**변경 내용 (diff):**
{diff[:PROMPT_DIFF_LIMIT]}

**출력 형식:**
제목: [{task.name} 제목]

본문:
{task.body_format}
"""


def split_title_body(text: str) -> tuple[str, str]:
    title, body_lines, in_body = "", [], False
    for line in text.strip().splitlines():
        if not in_body and line.startswith("제목:"):
            title = line.removeprefix("제목:").strip()
        elif line.startswith("본문:"):
            in_body = True
        elif in_body:
            body_lines.append(line)

    if not title:  # 모델이 형식을 안 지키면 첫 줄을 제목으로
        first, _, rest = text.strip().partition("\n")
        return first.strip(), rest.strip()
    return title, "\n".join(body_lines).strip()


class AIClient:
    def __init__(self, api_key: str, model: str, temperature: float | None, max_tokens: int):
        self.client = anthropic.Anthropic(api_key=api_key, base_url=BASE_URL)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.call_count = 0

    def ask(self, prompt: str) -> str:
        self.call_count += 1
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
                # SDK 2.x와 Codyssey 게이트웨이는 temperature를 받지 않아서, -t를 지정했을 때만 본문에 넣는다.
                extra_body=None if self.temperature is None else {"temperature": self.temperature},
            )
        except anthropic.APIError as e:
            reason = next((hint for cls, hint in API_ERROR_HINTS if isinstance(e, cls)), "API 오류")
            raise RuntimeError(f"AI API 호출 실패 - {reason}\n{HINT_INDENT}상세: {e}") from e
        if not message.content:
            raise RuntimeError("AI 응답이 비어 있습니다. --max-tokens 값을 늘려보세요.")
        return message.content[0].text


def warn(message: str):
    print(f"{INDENT}[경고] {message}")


def has_bullet(lines) -> bool:
    return any(line.lstrip().startswith(("-", "*")) for line in lines)


def ensure_sections(body: str, names: tuple) -> str:
    sections = [["", []]]  # [헤더, 내용 줄들], 첫 칸은 헤더 앞 내용
    for line in body.splitlines():
        if line.startswith("#"):
            sections.append([line, []])
        else:
            sections[-1][1].append(line)

    for name in names:
        section = next((s for s in sections if name.lower() in s[0].lower()), None)
        if section is None:
            warn(f"'{name}' 섹션 누락 → 섹션 추가")
            sections.append([f"## {name}", [PLACEHOLDER_BULLET]])
        elif not has_bullet(section[1]):
            warn(f"'{name}' 섹션에 불릿 없음 → 불릿 추가")
            section[1].insert(0, PLACEHOLDER_BULLET)

    blocks = ("\n".join(filter(None, [header, *lines])).strip() for header, lines in sections)
    return "\n\n".join(b for b in blocks if b)


def polish(task: Task, title: str, body: str) -> tuple[str, str]:
    title = title.splitlines()[0].strip() if title else ""
    if not title:
        warn("제목이 비어 있습니다. 직접 작성하세요.")
    elif len(title) > task.title_limit:
        warn(f"{task.name} 제목 {len(title)}자 → 최대 {task.title_limit}자로 자름")
        title = title[:task.title_limit - 3].rstrip() + "..."
    elif task.title_recommended and len(title) > task.title_recommended:
        warn(f"{task.name} 제목 {len(title)}자 (권장: {task.title_recommended}자 이내)")

    if task.required_sections:
        body = ensure_sections(body, task.required_sections)
    elif body and not has_bullet(body.splitlines()):
        warn("본문에 불릿 요약이 없습니다. 핵심 변경 사항을 불릿으로 정리하세요.")

    return title, body


SECTION_RULE = "─" * 50


def print_section(title: str, content: str):
    print(f"\n[ {title} ]\n\n{content}\n\n{SECTION_RULE}")


def exit_with(tag: str, message: str, *hints: str, code: int = 1):
    print(f"[{tag}] {message}")
    for hint in hints:
        print(HINT_INDENT + hint)
    sys.exit(code)


def check_git_changes() -> str:
    if not is_git_repo():
        exit_with("오류", "현재 디렉토리가 Git 리포지토리가 아닙니다.",
                  "Git 리포지토리 초기화: git init")

    # status --short는 staged, unstaged, untracked를 모두 포함한다.
    status = run_git("status", "--short")
    if not status.strip():
        exit_with("정보", "변경 사항이 없습니다.", code=0)
    return status


def get_api_key() -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        exit_with("오류", "ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.",
                  ".env 파일을 생성하거나 다음 명령어를 실행하세요:",
                  "export ANTHROPIC_API_KEY='your-api-key'")
    return api_key


def collect_diff(args, status: str) -> tuple[str, str]:
    print("[단계 1/3] Git 변경 사항 수집 중...")
    status, diff = get_changes(status)

    if args.safe_mode:
        diff = apply_safe_mode(diff, args.max_files, args.max_lines)
        print(f"{INDENT}안전 모드 활성화")
        print(f"{INDENT}- 최대 파일 수: {args.max_files}개")
        print(f"{INDENT}- 최대 줄 수: {args.max_lines}줄")

    file_count = len(status.strip().splitlines())
    print(f"{INDENT}변경된 파일: {file_count}개\n")
    return status, diff


def run(task: Task, args):
    status = check_git_changes()
    status, diff = collect_diff(args, status)
    api_key = get_api_key()

    print(f"[단계 2/3] 생성 요청 중 (모델: {args.model}, temp: {'기본' if args.temperature is None else args.temperature})...")
    ai = AIClient(api_key, args.model, args.temperature, args.max_tokens)
    title, body = split_title_body(ai.ask(build_prompt(task, status, diff)))

    print("[단계 3/3] 결과 검증 및 다듬기 중...")
    title, body = polish(task, title, body)

    print(f"\n{SECTION_RULE}")
    print_section("변경 파일 목록 (git status)", status.rstrip())
    if task.title_body_together:
        print_section(f"생성된 {task.name}", f"{title}\n\n{body}".strip())
    else:
        print_section(f"생성된 {task.name} 제목", title)
        print_section(f"생성된 {task.name} 본문", body)

    print(f"\n[통계] API 호출: {ai.call_count}회")
    print(f"[안내] {task.guide}\n")


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-m", "--model", default=DEFAULT_MODEL,
                        help=f"사용할 AI 모델 (기본: {DEFAULT_MODEL})")
    common.add_argument("-t", "--temperature", type=float,
                        help="Temperature 값 (0.0~1.0, 기본: 전송 안 함, 현재 Codyssey API는 미지원)")
    common.add_argument("--max-tokens", type=int, default=1024,
                        help="최대 토큰 수 (기본: 1024)")
    common.add_argument("--safe-mode", action="store_true",
                        help="안전 모드 활성화 (민감정보 마스킹 및 diff 제한)")
    common.add_argument("--max-files", type=int, default=10,
                        help="안전 모드: 최대 파일 수 (기본: 10)")
    common.add_argument("--max-lines", type=int, default=200,
                        help="안전 모드: 최대 줄 수 (기본: 200)")

    parser = argparse.ArgumentParser(description="AI 기반 Git 커밋/PR 자동 생성기")
    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령")
    subparsers.add_parser("commit", parents=[common], help="커밋 메시지 생성")
    subparsers.add_parser("pr", parents=[common], help="Pull Request 설명 생성")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        run(TASKS[args.command], args)
    except RuntimeError as e:
        print(f"\n[오류] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
