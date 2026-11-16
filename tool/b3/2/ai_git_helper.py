#!/usr/bin/env python3
"""
AI 기반 Git 커밋/PR 자동 생성기
Git 변경 사항을 분석하여 커밋 메시지와 PR 설명을 자동으로 생성합니다.
"""

import os
import sys
import subprocess
import argparse
import re
from typing import Optional, Tuple
import json
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("[오류] anthropic 패키지가 설치되지 않았습니다.")
    print("       설치 방법: pip3 install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    # .env 파일 로드
    load_dotenv()
except ImportError:
    print("[경고] python-dotenv 패키지가 설치되지 않았습니다.")
    print("       .env 파일을 사용하려면 설치하세요: pip3 install python-dotenv")
    print("       시스템 환경변수는 계속 사용 가능합니다.\n")


class GitHelper:
    """Git 명령을 실행하고 변경 사항을 수집하는 클래스"""
    
    @staticmethod
    def check_git_repo() -> bool:
        """현재 디렉토리가 Git 리포지토리인지 확인"""
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def get_status() -> str:
        """git status 결과 반환"""
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"[실패] git status 실행 실패: {e}")
            sys.exit(1)
    
    @staticmethod
    def get_diff(safe_mode: bool = False, max_files: int = 10, max_lines: int = 200) -> str:
        """git diff 결과 반환 (safe_mode일 경우 제한 적용)"""
        try:
            result = subprocess.run(
                ["git", "diff", "--staged"],
                check=True,
                capture_output=True,
                text=True
            )
            diff = result.stdout
            
            # staged 변경이 없으면 unstaged diff도 확인
            if not diff:
                result = subprocess.run(
                    ["git", "diff"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                diff = result.stdout
            
            if safe_mode:
                diff = GitHelper._apply_safe_mode(diff, max_files, max_lines)
            
            return diff
        except subprocess.CalledProcessError as e:
            print(f"[실패] git diff 실행 실패: {e}")
            sys.exit(1)
    
    @staticmethod
    def _apply_safe_mode(diff: str, max_files: int, max_lines: int) -> str:
        """안전 모드: 민감정보 마스킹 및 diff 제한"""
        # 1. 민감정보 패턴 마스킹
        patterns = [
            (r'[A-Za-z0-9_-]{20,}', '***MASKED_TOKEN***'),  # API 키 형태
            (r'sk-[A-Za-z0-9]{20,}', '***MASKED_API_KEY***'),  # OpenAI 스타일
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***MASKED_EMAIL***'),  # 이메일
            (r'password\s*[=:]\s*["\']?[^"\'\s]+["\']?', 'password=***MASKED***'),  # 비밀번호
        ]
        
        for pattern, replacement in patterns:
            diff = re.sub(pattern, replacement, diff, flags=re.IGNORECASE)
        
        # 2. 파일 수 제한
        file_diffs = diff.split('diff --git')
        if len(file_diffs) > max_files + 1:  # 첫 번째는 빈 문자열
            diff = 'diff --git'.join(file_diffs[:max_files + 1])
            diff += f"\n\n... (나머지 {len(file_diffs) - max_files - 1}개 파일 생략됨)"
        
        # 3. 줄 수 제한
        lines = diff.split('\n')
        if len(lines) > max_lines:
            diff = '\n'.join(lines[:max_lines])
            diff += f"\n\n... (나머지 {len(lines) - max_lines}줄 생략됨)"
        
        return diff
    
    @staticmethod
    def has_changes() -> bool:
        """변경 사항이 있는지 확인"""
        status = GitHelper.get_status()
        diff = GitHelper.get_diff()
        return bool(status.strip() or diff.strip())


class AIHelper:
    """AI API를 사용하여 커밋 메시지와 PR 설명을 생성하는 클래스"""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4", 
                 temperature: float = 0.7, max_tokens: int = 1024):
        # Codyssey API Base URL 설정
        base_url = os.environ.get('ANTHROPIC_BASE_URL', 'https://copa.codyssey.kr')
        
        self.client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_call_count = 0
    
    def generate_commit_message(self, status: str, diff: str) -> str:
        """커밋 메시지 생성"""
        prompt = self._build_commit_prompt(status, diff)
        self.api_call_count += 1
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            raise Exception(f"AI API 호출 실패: {str(e)}")
    
    def generate_pr_description(self, status: str, diff: str) -> Tuple[str, str]:
        """PR 제목과 본문 생성"""
        prompt = self._build_pr_prompt(status, diff)
        self.api_call_count += 1
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = message.content[0].text
            return self._parse_pr_result(result)
        except Exception as e:
            raise Exception(f"AI API 호출 실패: {str(e)}")
    
    def _build_commit_prompt(self, status: str, diff: str) -> str:
        """커밋 메시지 생성 프롬프트"""
        return f"""아래 Git 변경 사항을 분석하여 커밋 메시지를 작성해주세요.

**요구사항:**
- 커밋 제목: 50자 이내 (최대 72자)
- 커밋 제목은 변경의 핵심을 명확하게 표현
- 커밋 본문(선택): 변경된 파일 또는 핵심 변경 사항을 불릿으로 요약
- 한글로 작성

**변경 파일 목록:**
{status}

**변경 내용 (diff):**
{diff[:3000]}

**출력 형식:**
제목: [50자 이내의 커밋 제목]

본문:
- [변경 사항 1]
- [변경 사항 2]
"""
    
    def _build_pr_prompt(self, status: str, diff: str) -> str:
        """PR 설명 생성 프롬프트"""
        return f"""아래 Git 변경 사항을 분석하여 Pull Request 제목과 본문을 작성해주세요.

**요구사항:**
- PR 제목: 최대 80자, 변경의 핵심을 명확하게 표현
- PR 본문: Why, What, How to Test 섹션으로 구성
- 각 섹션에 최소 1개 이상의 불릿 포함
- 한글로 작성

**변경 파일 목록:**
{status}

**변경 내용 (diff):**
{diff[:3000]}

**출력 형식:**
제목: [PR 제목]

본문:
## Why (변경 배경)
- [배경 설명 1]

## What (핵심 변경 사항)
- [변경 사항 1]
- [변경 사항 2]

## How to Test (테스트 방법)
- [테스트 방법 1]
"""
    
    def _parse_pr_result(self, result: str) -> Tuple[str, str]:
        """PR 결과에서 제목과 본문 분리"""
        lines = result.strip().split('\n')
        title = ""
        body_lines = []
        
        in_body = False
        for line in lines:
            if line.startswith("제목:"):
                title = line.replace("제목:", "").strip()
            elif line.startswith("본문:"):
                in_body = True
            elif in_body:
                body_lines.append(line)
        
        body = '\n'.join(body_lines).strip()
        
        # 제목 길이 검증 (80자 제한)
        if len(title) > 80:
            title = title[:77] + "..."
        
        return title, body
    
    def get_api_call_count(self) -> int:
        """API 호출 횟수 반환"""
        return self.api_call_count


def validate_commit_message(message: str) -> bool:
    """커밋 메시지 형식 검증"""
    lines = message.strip().split('\n')
    if not lines:
        return False
    
    title = lines[0].replace("제목:", "").strip()
    
    # 제목 길이 검증
    if len(title) > 72:
        print(f"           [경고] 커밋 제목 {len(title)}자 (권장: 50자 이내)")
    
    return True


def validate_pr_description(title: str, body: str) -> bool:
    """PR 설명 형식 검증"""
    # 제목 길이 검증
    if len(title) > 80:
        print(f"           [경고] PR 제목 {len(title)}자 (최대: 80자)")
    
    # 필수 섹션 검증
    required_sections = ["Why", "What", "How to Test"]
    missing_sections = []
    
    for section in required_sections:
        if section not in body and section.lower() not in body.lower():
            missing_sections.append(section)
    
    if missing_sections:
        print(f"           [경고] 누락된 섹션: {', '.join(missing_sections)}")
    
    return True


def print_section(title: str, content: str):
    """섹션 구분선과 함께 내용 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print(content)
    print("=" * 80)


def setup_and_validate(args):
    """Git 리포지토리 확인 및 API 설정"""
    # Git 리포지토리 확인
    if not GitHelper.check_git_repo():
        print("[오류] 현재 디렉토리가 Git 리포지토리가 아닙니다.")
        print("       Git 리포지토리 초기화: git init")
        sys.exit(1)
    
    # 변경 사항 확인
    if not GitHelper.has_changes():
        print("[정보] 변경 사항이 없습니다.")
        sys.exit(0)
    
    # API Key 확인
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("[오류] ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        print("       .env 파일을 생성하거나 다음 명령어를 실행하세요:")
        print("       export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)
    
    return api_key


def collect_git_changes(args):
    """Git 변경 사항 수집"""
    print("[단계 1/3] Git 변경 사항 수집 중...")
    status = GitHelper.get_status()
    diff = GitHelper.get_diff(
        safe_mode=args.safe_mode,
        max_files=args.max_files,
        max_lines=args.max_lines
    )
    
    if args.safe_mode:
        print("           안전 모드 활성화")
        print(f"           - 최대 파일 수: {args.max_files}개")
        print(f"           - 최대 줄 수: {args.max_lines}줄")
    
    file_count = len([line for line in status.strip().split('\n') if line])
    print(f"           변경된 파일: {file_count}개\n")
    
    return status, diff


def create_ai_helper(api_key, args):
    """AI Helper 초기화"""
    print(f"[단계 2/3] 생성 요청 중 (모델: {args.model}, temp: {args.temperature})...")
    
    return AIHelper(
        api_key=api_key,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )


def generate_commit(ai_helper, status, diff):
    """커밋 메시지 생성 및 출력"""
    commit_message = ai_helper.generate_commit_message(status, diff)
    print("[단계 3/3] 결과 검증 중...")
    validate_commit_message(commit_message)
    
    print_section("생성된 커밋 메시지", commit_message)
    print(f"\n[통계] API 호출: {ai_helper.get_api_call_count()}회")
    print("[안내] 위 메시지를 복사하여 git commit에 사용하세요.\n")


def generate_pr(ai_helper, status, diff):
    """PR 설명 생성 및 출력"""
    pr_title, pr_body = ai_helper.generate_pr_description(status, diff)
    print("[단계 3/3] 결과 검증 중...")
    validate_pr_description(pr_title, pr_body)
    
    print_section("생성된 PR 제목", pr_title)
    print_section("생성된 PR 본문", pr_body)
    print(f"\n[통계] API 호출: {ai_helper.get_api_call_count()}회")
    print("[안내] 위 내용을 GitHub PR 작성 시 사용하세요.\n")


def add_common_arguments(parser):
    """공통 CLI 인자 추가"""
    parser.add_argument('-m', '--model', default='claude-sonnet-4',
                       help='사용할 AI 모델 (기본: claude-sonnet-4)')
    parser.add_argument('-t', '--temperature', type=float, default=0.7,
                       help='Temperature 값 (0.0~1.0, 기본: 0.7)')
    parser.add_argument('--max-tokens', type=int, default=1024,
                       help='최대 토큰 수 (기본: 1024)')
    parser.add_argument('--safe-mode', action='store_true',
                       help='안전 모드 활성화 (민감정보 마스킹 및 diff 제한)')
    parser.add_argument('--max-files', type=int, default=10,
                       help='안전 모드: 최대 파일 수 (기본: 10)')
    parser.add_argument('--max-lines', type=int, default=200,
                       help='안전 모드: 최대 줄 수 (기본: 200)')


def main():
    parser = argparse.ArgumentParser(
        description="AI 기반 Git 커밋/PR 자동 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령')
    
    # commit 명령
    commit_parser = subparsers.add_parser('commit', help='커밋 메시지 생성')
    add_common_arguments(commit_parser)
    
    # pr 명령
    pr_parser = subparsers.add_parser('pr', help='Pull Request 설명 생성')
    add_common_arguments(pr_parser)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # 1. 설정 및 검증
        api_key = setup_and_validate(args)
        
        # 2. Git 변경 사항 수집
        status, diff = collect_git_changes(args)
        
        # 3. AI Helper 초기화
        ai_helper = create_ai_helper(api_key, args)
        
        # 4. 생성 및 출력
        if args.command == 'commit':
            generate_commit(ai_helper, status, diff)
        elif args.command == 'pr':
            generate_pr(ai_helper, status, diff)
    
    except Exception as e:
        print(f"\n[오류] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
