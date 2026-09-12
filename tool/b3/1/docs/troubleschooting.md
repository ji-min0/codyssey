# 트러블슈팅 보고서

| 항목 | 내용 |
|---|---|
| 과제 | Codyssey B3-1 · AWS VPC 기반 웹 서비스 인프라 구축 |
| 발생 단계 | SSH 키페어 생성 (스택 배포 전) |
| 발생 일자 | 2026-09-11 |

---

## #1 · AWS CLI 프로필 미적용으로 인한 `NoRegion` 에러

| 항목 | 내용 |
|---|---|
| **증상** | 새 터미널에서 `aws ec2 create-key-pair`를 실행하자 `An error occurred (NoRegion): You must specify a region.` 에러가 발생했다. 또한 명령이 실패했음에도 출력 리다이렉트(`> ~/.ssh/cloud-mission.pem`) 때문에 크기 0의 빈 키 파일이 생성되어, 재실행 시 `chmod 400`으로 잠긴 파일을 덮어쓰지 못하는 문제까지 이어질 수 있었다. |
| **원인 가설** | 리전은 `aws configure --profile codyssey`로 **codyssey 프로필에만** 설정했고, 프로필 지정은 `export AWS_PROFILE=codyssey` 환경변수로 하고 있었다. 환경변수는 셸 세션 단위이므로, 새 터미널에서는 설정이 풀려 리전 정보가 없는 `default` 프로필로 실행된 것으로 추정했다. |
| **검증 방법** | ① 셸 프롬프트에서 프로필을 표시하던 `AWS: codyssey` 세그먼트가 사라진 것을 확인했다.<br>② `aws configure list`로 실제 적용 중인 프로필과 리전 값을 확인했다.<br>③ `ls -l ~/.ssh/cloud-mission.pem`으로 생성된 파일 크기가 0임을 확인해, 키 발급 자체가 이뤄지지 않았음을 확인했다. |
| **조치 내용** | ① 잘못 생성된 빈 키 파일을 삭제(`rm -f ~/.ssh/cloud-mission.pem`)했다.<br>② `export AWS_PROFILE=codyssey`로 프로필을 다시 지정했다.<br>③ `aws sts get-caller-identity`로 호출 주체가 `arn:aws:iam::***:user/codyssey`임을 확인한 뒤 키페어 생성 명령을 재실행했다. |
| **결과** | 키페어가 정상 생성되었고, `aws ec2 describe-key-pairs --key-names cloud-mission`으로 AWS에 등록된 것을 확인했다(`ed25519`, 지문 일치). 로컬 개인키도 정상 크기로 저장되어 이후 EC2 SSH 접속에 사용했다. |
| **재발 방지** | ① AWS 명령을 실행하기 전에 셸 프롬프트의 프로필 표시를 확인하고, 불확실하면 `aws sts get-caller-identity`로 호출 주체와 리전을 먼저 점검한다.<br>② 출력 리다이렉트로 파일을 생성하는 명령은 실패해도 빈 파일이 남으므로, 실행 직후 `ls -l`로 파일 크기를 확인하는 절차를 둔다.<br>③ 키페어는 생성 시점에만 개인키를 내려받을 수 있으므로, 재발급이 불가능하다는 전제로 생성 결과를 반드시 검증한다. |

### 참고: 프로필을 환경변수로 관리한 이유

`~/.zshrc`에 `export AWS_PROFILE=codyssey`를 등록하면 새 터미널에서도 자동으로 적용되지만, 이번 과제에서는 적용하지 않았다. 실습이 끝나면 해당 IAM 사용자와 액세스 키를 삭제할 예정이라 셸 설정에 영구적으로 남기는 것이 적절하지 않다고 판단했고, 매번 명시적으로 프로필을 지정하는 편이 **어떤 주체로 AWS를 호출하는지 의식하게 되어** 루트 계정 미사용·최소권한 원칙을 지키는 데 오히려 도움이 된다고 보았다.

---

## 부록: 참고한 진단 수단

이번 과제에서 문제 원인을 로그·상태로 확인하기 위해 사용한 명령들이다.

| 대상 | 명령 | 확인 내용 |
|---|---|---|
| CLI 자격 증명 | `aws configure list`, `aws sts get-caller-identity` | 적용 중인 프로필, 리전, 호출 주체 |
| IAM 권한 | 에러 메시지의 `not authorized to perform: <액션>` | 정책에 없는 액션이 거부되는지 |
| CloudFormation | `describe-stack-events` | 리소스별 생성·수정 상태와 실패 사유 |
| EC2 부팅 스크립트 | `/var/log/cloud-init-output.log` | UserData 실행 로그 (`set -x`로 명령 단위 출력) |
| Nginx | `nginx -t`, `systemctl status nginx` | 설정 문법 오류, 서비스 실행 상태 |
| 응답 경로 | `curl -i`의 `Server`, `X-Served-By` 헤더 | 호스트 Nginx / 컨테이너 중 어디서 응답했는지 |