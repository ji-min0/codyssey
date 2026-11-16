# AI 기반 Git 커밋/PR 자동 생성기

Git 변경 사항을 분석하여 커밋 메시지와 Pull Request 설명을 자동으로 생성하는 CLI 도구입니다.

## 주요 기능

- **커밋 메시지 자동 생성**: Git diff를 분석하여 의미 있는 커밋 메시지 작성
- **PR 설명 자동 생성**: Why/What/How to Test 구조의 PR 템플릿 생성
- **안전 모드**: 민감정보 자동 마스킹 및 diff 크기 제한
- **커스터마이징**: AI 모델, temperature, max_tokens 등 파라미터 조정 가능

## 설치 방법

### 1. 필수 요구사항

- Python 3.10 이상
- Git이 설치되어 있어야 함
- Codyssey API Key (학습장에서 제공)

### 2. 의존성 설치

```bash
pip3 install -r requirements.txt
```

또는 직접 설치:

```bash
pip3 install anthropic python-dotenv
```

### 3. 환경변수 설정

#### .env 파일 사용 (권장)

프로젝트 루트에 `.env` 파일을 생성하고 Codyssey API Key를 입력하세요:

```bash
# .env 파일 내용
ANTHROPIC_API_KEY=your-codyssey-virtual-key-here
ANTHROPIC_BASE_URL=코디세이에서 공지한 base url
ANTHROPIC_MODEL=claude-haiku-4   # 선택: 기본 모델 (없으면 claude-sonnet-4, -m 옵션이 우선)
```

#### 사용 가능한 모델

| 모델 ID | 이름 | 차감 배수 | 권장 용도 |
|---------|------|-----------|----------|
| `claude-sonnet-4` | Claude Sonnet 4.6 | 1x | **기본 권장** - 균형잡힌 성능 |
| `claude-haiku-4` | Claude Haiku 4.5 | 0.5x | 빠르고 저렴한 생성 |
| `claude-opus-4-7` | Claude Opus 4.7 | 1.5x | 고품질 생성 |
| `gpt-5-mini` | GPT-5 Mini | 0.5x | OpenAI 모델 (저렴) |
| `gpt-5.4` | GPT-5.4 | 1x | OpenAI 모델 (균형) |

## 사용 방법

### 기본 사용법

프로그램을 실행 가능하게 만들기:

```bash
chmod +x ai_git_helper.py
```

Git 리포지토리 루트 디렉토리에서 실행:

```bash
# 커밋 메시지 생성
python3 ai_git_helper.py commit

# PR 설명 생성
python3 ai_git_helper.py pr
```


### 고급 옵션

#### 커밋 메시지 생성 옵션

```bash
# 기본 실행
python3 ai_git_helper.py commit

# 모델 변경 (Codyssey 제공 모델)
python3 ai_git_helper.py commit -m claude-haiku-4  # 빠르고 저렴
python3 ai_git_helper.py commit -m claude-opus-4-7  # 고품질

# Temperature 조정 (0.0 = 결정적, 1.0 = 창의적)
# ※ 현재 Codyssey API는 temperature를 지원하지 않아 400 오류가 납니다 (아래 참고)
python3 ai_git_helper.py commit -t 0.5

# 최대 토큰 수 조정
python3 ai_git_helper.py commit --max-tokens 2048

# 안전 모드 활성화
python3 ai_git_helper.py commit --safe-mode

# 안전 모드 세부 설정
python3 ai_git_helper.py commit --safe-mode --max-files 5 --max-lines 100
```

#### PR 설명 생성 옵션

```bash
# 기본 실행
python3 ai_git_helper.py pr

# 모든 옵션 조합
python3 ai_git_helper.py pr -m claude-sonnet-4 --max-tokens 1024 --safe-mode
```


### 파라미터 설명

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `-m, --model` | 사용할 AI 모델 (claude-sonnet-4, claude-haiku-4 등) | claude-sonnet-4 |
| `-t, --temperature` | 생성 다양성 (0.0~1.0). 지정했을 때만 전송 | 전송 안 함 |
| `--max-tokens` | 최대 생성 토큰 수 | 1024 |
| `--safe-mode` | 안전 모드 활성화 | False |
| `--max-files` | 안전 모드: 최대 파일 수 | 10 |
| `--max-lines` | 안전 모드: 최대 줄 수 | 200 |
| `--convention FILE` | 팀 컨벤션 JSON 파일 적용 | 없음 |
| `--dry-run` | API를 호출하지 않고 전송될 프롬프트만 출력 | False |

#### temperature 지원 여부

| 파라미터 | 결과에 주는 영향 | Codyssey API |
|---------|-----------------|--------------|
| `temperature` | 낮을수록(0.0) 같은 입력에 같은 답, 높을수록(1.0) 표현이 다양해짐 | **미지원**: `temperature: Extra inputs are not permitted` (400) |
| `max_tokens` | 응답 최대 길이. 너무 작으면 본문이 잘림 | 지원 |
| `model` | 품질/속도/차감 배수 | 지원 |

최신 Anthropic API와 SDK 2.x에서 sampling 파라미터가 빠지면서, Codyssey 게이트웨이도 `temperature`를 거부합니다.
그래서 `-t`는 **직접 지정했을 때만** 요청에 넣고, 기본 실행에서는 보내지 않습니다.
temperature를 지원하는 API로 바꾸면 `-t`를 그대로 쓸 수 있습니다.

## 실행 예시

### 1. 커밋 메시지 생성

```bash
$ python3 ai_git_helper.py commit

[단계 1/3] Git 변경 사항 수집 중...
           변경된 파일: 3개

[단계 2/3] 생성 요청 중 (모델: claude-sonnet-4, temp: 기본)...
[단계 3/3] 결과 검증 및 다듬기 중...

──────────────────────────────────────────────────

[ 변경 파일 목록 (git status) ]

 M README.md
 M ai_git_helper.py
 M requirements.txt

──────────────────────────────────────────────────

[ 생성된 커밋 메시지 ]

AI 기반 커밋/PR 생성기 초기 구현

- ai_git_helper.py: Git 변경 분석 및 API 연동 로직 추가
- README.md: 설치 및 사용 가이드 작성
- requirements.txt: anthropic 패키지 의존성 추가

──────────────────────────────────────────────────

[통계] API 호출: 1회
[안내] 위 메시지를 복사하여 git commit에 사용하세요.
```

### 2. PR 설명 생성

```bash
$ python3 ai_git_helper.py pr

[단계 1/3] Git 변경 사항 수집 중...
           변경된 파일: 3개

[단계 2/3] 생성 요청 중 (모델: claude-sonnet-4, temp: 기본)...
[단계 3/3] 결과 검증 및 다듬기 중...

──────────────────────────────────────────────────

[ 변경 파일 목록 (git status) ]

 M README.md
 M ai_git_helper.py
 M requirements.txt

──────────────────────────────────────────────────

[ 생성된 PR 제목 ]

AI 기반 Git 커밋/PR 자동 생성 CLI 도구 구현

──────────────────────────────────────────────────

[ 생성된 PR 본문 ]

## Why (변경 배경)
- Git 변경 사항 분석 자동화 필요
- 문서화 작업 시간 단축 및 일관된 품질 유지

## What (핵심 변경 사항)
- Git status/diff 수집 및 분석 기능 구현
- AI API 연동 및 커밋 메시지 자동 생성
- PR 템플릿 자동 생성 (Why/What/How to Test)
- 안전 모드: 민감정보 마스킹 및 diff 크기 제한

## How to Test (테스트 방법)
- Git 리포지토리에서 파일 수정 후 실행
- 생성된 메시지가 변경 사항을 적절히 반영하는지 확인
- --safe-mode 옵션으로 민감정보 처리 확인

──────────────────────────────────────────────────

[통계] API 호출: 1회
[안내] 위 내용을 GitHub PR 작성 시 사용하세요.
```

### 3. 안전 모드 사용

```bash
$ python3 ai_git_helper.py commit --safe-mode --max-files 5 --max-lines 100

[단계 1/3] Git 변경 사항 수집 중...
           안전 모드 활성화
           - 최대 파일 수: 5개
           - 최대 줄 수: 100줄
           - 마스킹: 비밀값(.env) 1건, 이메일 2건
           변경된 파일: 8개
```

### 4. 전송 내용 미리 보기 (`--dry-run`)

API를 호출하지 않고 AI에 보낼 프롬프트를 그대로 출력합니다. API Key가 없어도 되고 토큰도 차감되지 않으므로,
안전 모드와 컨벤션이 제대로 적용됐는지 확인할 때 사용합니다.

```bash
python3 ai_git_helper.py commit --safe-mode --dry-run
```

## 주요 특징

### 1. 민감정보 보호 (안전 모드)

`--safe-mode` 옵션을 켜거나, 컨벤션 파일에서 `"safe_mode": {"enabled": true}`로 설정하면 적용됩니다.

#### 안전 모드 정책

| 항목 | 기준 | 처리 |
|------|------|------|
| 파일 수 | 최대 **10개** (`--max-files`) | 초과분은 `... (나머지 N개 파일 생략됨)` |
| 줄 수 | 최대 **200줄** (`--max-lines`) | 초과분은 `... (나머지 N줄 생략됨)` |
| 프롬프트 diff | 최대 **3,000자** | 안전 모드와 무관하게 항상 적용 |

설정 우선순위: **CLI 옵션 > 컨벤션 파일 `safe_mode` > 기본값**

#### 마스킹 규칙 (위에서부터 순서대로 적용)

| 대상 | 기준 | 치환 결과 |
|------|------|-----------|
| 개인키 | `-----BEGIN ... PRIVATE KEY-----` 블록 전체 | `***MASKED_PRIVATE_KEY***` |
| .env 비밀값 | 대문자 변수명에 PASSWORD/PASSWD/SECRET/TOKEN/API_KEY 포함 | `DB_PASSWORD=***MASKED***` |
| 코드 속 비밀값 | 위 단어가 들어간 변수에 문자열 대입 (`token = "..."`, `"api_key": "..."`) | `token = "***MASKED***"` |
| Bearer 토큰 | `Bearer` 뒤 10자 이상 | `Bearer ***MASKED***` |
| 이메일 | `xxx@xxx.xx` | `***MASKED_EMAIL***` |
| sk- API Key | `sk-` + 20자 이상 (Codyssey/OpenAI 키) | `***MASKED_API_KEY***` |
| AWS Access Key | `AKIA`/`ASIA` + 16자 | `***MASKED_AWS_KEY***` |
| 주민등록번호 | `6자리-[1-4]6자리` | `***MASKED_RRN***` |
| 휴대폰 번호 | `010-1234-5678`, `01012345678` | `***MASKED_PHONE***` |
| 긴 토큰 | **숫자와 영문이 섞인** 20자 이상 문자열 | `***MASKED_TOKEN***` |

- 긴 토큰 규칙은 숫자가 섞인 경우에만 적용되므로 `PermissionDeniedError` 같은 긴 코드 이름은 가려지지 않습니다.
- 팀 전용 규칙은 컨벤션 파일의 `safe_mode.extra_patterns`에 `[정규식, 치환값]`으로 추가하며, 기본 규칙보다 먼저 적용됩니다.
- 실행 로그에 규칙별 마스킹 건수가 표시됩니다.

#### 안전 모드 ON/OFF 비교 (`--dry-run`으로 실제 전송 내용 확인)

테스트용 변경 사항(`app.py`, `config.env`)을 만들어 전송될 diff를 비교한 결과입니다.

| 원본 (OFF) | 안전 모드 (ON, `.ai-gitgen.json` 정책) |
|-----------|----------------------------------------|
| `API_KEY = "sk-AbC123def456ghiJKLmnoPQRstu"` | `API_KEY = ***MASKED***` |
| `ADMIN_EMAIL = "admin@example.com"` | `ADMIN_EMAIL = "***MASKED_EMAIL***"` |
| `SERVER = "10.0.0.12"` | `SERVER = "***MASKED_IP***"` (사용자 정의 규칙) |
| `"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"` | `"Authorization": "Bearer ***MASKED***"` |
| `DB_PASSWORD=hunter2` | `DB_PASSWORD=***MASKED***` |

```
           안전 모드 활성화
           - 최대 파일 수: 8개
           - 최대 줄 수: 150줄
           - 마스킹: 사용자 정의 1건, 비밀값(.env) 2건, Bearer 토큰 1건, 이메일 1건
```

### 2. 팀 컨벤션 커스터마이징 (`--convention`)

JSON 파일로 팀의 커밋/PR 규칙을 정의하면 프롬프트, 결과 검증, 안전 모드 정책에 함께 반영됩니다.
예시 파일: [`.ai-gitgen.json`](.ai-gitgen.json)

```bash
python3 ai_git_helper.py commit --convention .ai-gitgen.json
```

#### 정의한 컨벤션 (기존 리포지토리 `ji-min0/codyssey` 커밋 30개 분석)

| 항목 | 규칙 | 실제 예 |
|------|------|---------|
| 제목 형식 | `<타입>: <한글 설명>`, 스코프 표기 없음 | `fix: 상단 navbar 사라지는 오류` |
| 타입 | `feat` 기능, `fix` 버그, `docs` 문서/스크린샷, `refac` 리팩토링, `chore` 파일 이동/설정, `init` 초기 업로드 | `chore: 과제 폴더 안으로 옮김` |
| 어미 | 마침표 없이 명사형 (`~추가`, `~수정`, `~작성`) | `docs: 리드미 작성` |
| PR | 커밋과 같은 제목 형식, Why/What/How to Test + Checklist 섹션 | |

#### 설정 항목

| 위치 | 키 | 역할 |
|------|----|------|
| `commit` / `pr` | `extra_rules` | 프롬프트 요구사항에 추가할 규칙 목록 |
| | `title_pattern` | 제목이 따라야 할 정규식. 맞지 않으면 경고 |
| | `title_limit`, `title_recommended` | 제목 최대/권장 글자 수 |
| | `required_sections` | PR 본문 필수 섹션. 없으면 자동 추가 |
| `safe_mode` | `enabled` | `true`면 `--safe-mode` 없이도 항상 안전 모드 |
| | `max_files`, `max_lines` | diff 전송 제한 |
| | `extra_patterns` | `[정규식, 치환값]` 추가 마스킹 규칙 |

알 수 없는 키나 잘못된 정규식이 있으면 실행 전에 오류로 알려줍니다.

#### 컨벤션 적용 전/후 비교

같은 변경(README 추가 커밋의 staged diff)으로 두 번 생성한 실제 결과입니다. (모델: `claude-sonnet-4`)

```bash
python3 ai_git_helper.py commit                               # 적용 전
python3 ai_git_helper.py commit --convention .ai-gitgen.json  # 적용 후
```

**적용 전**

```
AI 기반 Git 커밋/PR 자동 생성기 README 추가

- AI 기반 Git 커밋 메시지 및 PR 설명 자동 생성 CLI 도구 문서 추가
- 설치 방법 및 환경변수(.env) 설정 가이드 작성
- 사용 가능한 AI 모델 목록 및 차감 배수 정보 포함
- 커밋/PR 생성 기본 사용법 및 고급 옵션 예제 작성
- 안전 모드, temperature 등 주요 파라미터 설명 추가
```

**적용 후**

```
[설정] 컨벤션 파일 적용: .ai-gitgen.json
           안전 모드 활성화
           - 마스킹: 사용자 정의 1건, 비밀값(.env) 1건, 비밀값(문자열) 5건, Bearer 토큰 1건, 이메일 2건, 전화번호 2건

docs: AI 기반 Git 커밋/PR 자동 생성기 README 작성

- AI 기반 Git 커밋 메시지 및 PR 설명 자동 생성 CLI 도구 문서 추가
- 설치 방법, 환경변수 설정, 사용 가능한 모델 목록 작성
- 기본 사용법 및 고급 옵션(모델 변경, temperature, 안전 모드 등) 설명 추가
- 파라미터 설명 및 temperature 지원 여부 안내 포함
```

| 항목 | 적용 전 | 적용 후 |
|------|---------|---------|
| 제목 형식 | 타입 없음 | `docs:` 타입 prefix (`title_pattern` 검사 통과) |
| 어미 | `~추가` | 팀 규칙대로 `~작성` |
| 안전 모드 | 꺼짐 (diff 원문 전송) | `safe_mode.enabled`로 자동 적용, README 예시 속 키/이메일 등 13건 마스킹 |
| 본문 | 불릿 5개 | 불릿 4개, 내용은 동일 수준 |

### 3. 출력 형식 검증 및 후처리

AI 응답은 그대로 출력하지 않고, 아래 규칙으로 검증한 뒤 **후처리**합니다.
재생성 대신 후처리를 택해 1회 실행당 API 호출은 항상 1회입니다.

| 대상 | 규칙 | 위반 시 처리 |
|------|------|-------------|
| 커밋 제목 | 50자 이내 권장 | 경고만 표시 |
| 커밋 제목 | 최대 72자 | 69자 + `...`로 자름 |
| 커밋 본문 | 불릿 요약 포함 | 경고 표시 |
| PR 제목 | 최대 80자 | 77자 + `...`로 자름 |
| PR 본문 | Why/What/How to Test 섹션 필수 | 없는 섹션을 `- (작성 필요)`와 함께 추가 |
| PR 본문 | 각 섹션 불릿 1개 이상 | 해당 섹션에 `- (작성 필요)` 추가 |
| 공통 | 모델이 `제목:` 형식을 안 지킴 | 응답 첫 줄을 제목으로 사용 |

후처리한 항목은 `[경고]`로 표시되므로, `(작성 필요)` 부분은 직접 채운 뒤 사용하세요.

### 4. API 오류 처리

API 호출이 실패하면 원인과 확인할 부분을 함께 출력합니다.

| 상황 | 출력 메시지 |
|------|-------------|
| 잘못된 API Key (401) | 인증 실패: ANTHROPIC_API_KEY를 확인하세요 |
| 권한 없음 / 잔여 토큰 부족 (403) | 권한 없음: API Key의 사용 권한/잔여 토큰을 확인하세요 |
| 없는 모델 ID (404) | 모델 또는 엔드포인트 없음: -m 모델 ID와 ANTHROPIC_BASE_URL을 확인하세요 |
| 요청 한도 초과 (429) | 요청 한도 초과: 잠시 후 다시 시도하세요 |
| 네트워크 끊김 / 잘못된 URL | 네트워크 오류: 인터넷 연결과 ANTHROPIC_BASE_URL을 확인하세요 |
| 잘못된 파라미터 (400) | 잘못된 요청: -t(0.0~1.0), --max-tokens 값을 확인하세요 |

```bash
[오류] AI API 호출 실패 - 인증 실패: ANTHROPIC_API_KEY를 확인하세요
       상세: Error code: 401 - {... 'authentication_error' ...}
```

### 5. 비용 최적화

- 1회 실행 = 1회 API 호출
- 각 실행 후 API 호출 횟수 표시
- Max tokens 제한으로 비용 관리
- **Codyssey 제공 모델 사용**: 차감 배수에 따라 비용이 다릅니다
  - `claude-haiku-4`: 0.5x (가장 저렴)
  - `claude-sonnet-4`: 1x (기본, 권장)
  - `claude-opus-4-7`: 1.5x (고품질)

## 운영 시 고려사항

### 비용 관리

- **API 호출 비용**: Codyssey API는 학습장에서 제공하는 크레딧을 사용합니다
- **차감 배수**: 모델마다 다릅니다 (haiku: 0.5x, sonnet: 1x, opus: 1.5x)
- **권장 사용법**: 
  - 큰 변경사항이 있을 때만 사용
  - `claude-haiku-4` 모델로 비용 절감 (차감 배수 0.5x)
  - `--safe-mode`로 전송 데이터 크기 제한

### 보안 주의사항

1. **API Key 관리**
   - 절대 코드에 하드코딩하지 않기
   - 환경변수로만 관리
   - `.gitignore`에 `.env` 파일 추가

2. **민감정보 검토**
   - AI 생성 결과물을 반드시 직접 검토 후 사용
   - `--safe-mode` 사용 권장
   - Diff에 민감정보가 포함되지 않도록 주의

3. **생성 결과 검증**
   - 생성된 커밋/PR 메시지는 초안입니다
   - 기술적 정확성은 직접 확인 필요
   - 팀 컨벤션에 맞게 수정 후 사용

### 제한사항

- Git push, GitHub PR 자동 생성은 지원하지 않음 (수동 작업 필요)
- 터미널에 텍스트 출력만 제공 (복사 후 사용)
- Staged/Unstaged 변경사항 모두 분석

## 문제 해결

### "변경 사항이 없습니다" 메시지가 나올 때

```bash
# Git 상태 확인
git status

# 파일을 수정했는지 확인
git diff

# Staged 파일이 있는지 확인
git diff --staged
```

### "ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다" 오류

#### 방법 1: .env 파일 사용
```bash
# .env 파일을 생성하고 API Key 입력
# ANTHROPIC_API_KEY=your-key-here
# ANTHROPIC_BASE_URL=코디세이에서 공지한 base url 사용
```

#### 방법 2: 환경변수 직접 확인
```bash
# 환경변수 확인
echo $ANTHROPIC_API_KEY

# 설정되지 않았다면
export ANTHROPIC_API_KEY='your-api-key'
```

### "anthropic 패키지가 설치되지 않았습니다" 오류

```bash
# 모든 패키지 설치 (권장)
pip3 install -r requirements.txt

# 또는 개별 설치
pip3 install anthropic python-dotenv
```

### "현재 디렉토리가 Git 리포지토리가 아닙니다" 오류

```bash
# Git 리포지토리 초기화
git init

# 또는 기존 리포지토리 루트로 이동
cd /path/to/your/repo
```