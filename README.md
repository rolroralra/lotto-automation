# Lotto Automation AWS Lambda

AWS Lambda를 이용한 로또 자동 구매 시스템

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                               │
│                                                                 │
│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐ │
│  │  EventBridge │────>│  Lambda Function │────>│  dhlottery   │ │
│  │  (Scheduler) │     │  (lotto-auto)    │     │  .co.kr      │ │
│  │  Mon 15:00   │     └────────┬─────────┘     └──────────────┘ │
│  └──────────────┘              │                                │
│                                │                                │
│                     ┌──────────┴──────────┐                     │
│                     │                     │                     │
│                     v                     v                     │
│             ┌──────────────┐      ┌──────────────┐              │
│             │   Secrets    │      │     SNS      │              │
│             │   Manager    │      │   (알림)      │              │
│             │  (계정정보)    │      └──────┬───────┘              │
│             └──────────────┘             │                      │
│                                          v                      │
│                     ┌──────────────┐  ┌──────────┐              │
│                     │     SQS      │  │  Email   │              │
│                     │    (DLQ)     │  │  알림     │              │
│                     └──────────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- 매주 월요일 15:00 KST 자동 실행
- 복수 계정 지원 (단일 Secret에서 관리)
- 실패 시 이메일 알림
- Terraform으로 인프라 코드화

---

## Quick Start

### 1. AWS 환경 설정

```bash
# AWS CLI 설정 확인
aws sts get-caller-identity

# Terraform Backend 생성 (S3 + DynamoDB)
./scripts/setup-aws.sh
```

### 2. Terraform 배포

```bash
cd terraform

# terraform.tfvars 설정 (선택사항 - 기본값 사용 가능)
cp terraform.tfvars.example terraform.tfvars

# 초기화 및 배포
terraform init
terraform plan
terraform apply
```

### 3. Secrets Manager에 자격 증명 등록

```bash
aws secretsmanager put-secret-value \
  --secret-id lotto-automation/credentials \
  --secret-string '{"accounts":[{"username":"아이디1","password":"비밀번호1"},{"username":"아이디2","password":"비밀번호2"}]}'
```

### 4. SNS 이메일 구독 확인

배포 후 알림 이메일로 구독 확인 메일이 발송됩니다. **Confirm subscription** 클릭 필요.

---

## Project Structure

```
lotto-project/
├── PRD.md                          # 요구사항 문서
├── README.md                       # 이 문서
├── .gitignore
│
├── terraform/
│   ├── main.tf                     # 루트 모듈
│   ├── variables.tf                # 변수 정의
│   ├── outputs.tf                  # 출력값
│   ├── versions.tf                 # Provider 버전
│   ├── backend.tf                  # S3 Backend 설정
│   ├── terraform.tfvars.example    # 설정 예제
│   └── modules/
│       ├── secrets/                # Secrets Manager (단일 Secret)
│       ├── lambda/                 # Lambda 함수 + IAM
│       ├── eventbridge/            # 스케줄러
│       └── notifications/          # SNS Topic + SQS DLQ
│
├── lambda/
│   ├── src/
│   │   ├── handler.py              # Lambda 핸들러 (진입점)
│   │   ├── lotto.py                # 로또 구매 로직
│   │   └── secrets_manager.py      # AWS Secrets 유틸
│   ├── requirements.txt            # Python 의존성
│   └── build.sh                    # 배포 패키지 빌드
│
└── scripts/
    ├── setup-aws.sh                # AWS 초기 설정 (S3, DynamoDB)
    └── deploy.sh                   # 배포 자동화
```

---

## Secrets Manager 형식

단일 Secret (`lotto-automation/credentials`)에 `accounts` 배열로 저장:

```json
{
  "accounts": [
    {"username": "아이디1", "password": "비밀번호1"},
    {"username": "아이디2", "password": "비밀번호2"}
  ]
}
```

계정 추가/수정:
```bash
aws secretsmanager put-secret-value \
  --secret-id lotto-automation/credentials \
  --secret-string '{"accounts":[{"username":"id1","password":"pw1"},{"username":"id2","password":"pw2"}]}'
```

---

## Manual Testing

```bash
# Lambda 수동 실행 (로또 구매)
aws lambda invoke \
  --function-name lotto-automation-prod \
  --payload '{"action":"buy_ticket"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json

# 잔액 확인만 실행
aws lambda invoke \
  --function-name lotto-automation-prod \
  --payload '{"action":"check_balance"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

# 당첨 결과 확인
aws lambda invoke \
  --function-name lotto-automation-prod \
  --payload '{"action":"check_result"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

# 로그 확인
aws logs tail /aws/lambda/lotto-automation-prod --follow
```

---

## Configuration

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `aws_region` | AWS 리전 | `ap-northeast-2` |
| `environment` | 환경 이름 | `prod` |
| `project_name` | 프로젝트 이름 | `lotto-automation` |
| `notification_email` | 알림 이메일 | `rolroralra@gmail.com` |
| `schedule_expression` | 실행 스케줄 | `cron(0 6 ? * MON *)` (월 15:00 KST) |
| `lambda_timeout` | 타임아웃 | `300`초 |
| `lambda_memory_size` | 메모리 | `1024`MB |

---

## Lambda Actions

| Action | 설명 |
|--------|------|
| `buy_ticket` | 로또 구매 + 잔액 확인 (기본값) |
| `check_balance` | 잔액 확인만 |
| `check_result` | 당첨 결과 확인 |

---

## Cost Estimate (월간)

| 서비스 | 사용량 | 예상 비용 |
|--------|--------|----------|
| Lambda | ~4회/월, 5분/회 | ~$0.05 |
| Secrets Manager | 1개 시크릿 | ~$0.40 |
| EventBridge | 4회 스케줄 | 무료 |
| SNS | 이메일 알림 | 무료 |
| SQS (DLQ) | 최소 | 무료 |
| CloudWatch Logs | ~1GB | ~$0.50 |
| **합계** | | **~$0.95/월** |

---

## Troubleshooting

### Lambda 실행 실패
```bash
# 최근 로그 확인
aws logs tail /aws/lambda/lotto-automation-prod --since 1h

# Secret 값 확인
aws secretsmanager get-secret-value \
  --secret-id lotto-automation/credentials \
  --query SecretString --output text
```

### DLQ 메시지 확인
```bash
aws sqs receive-message \
  --queue-url https://sqs.ap-northeast-2.amazonaws.com/{account-id}/lotto-automation-dlq-prod
```

### Terraform State 문제
```bash
# State lock 강제 해제
terraform force-unlock {lock-id}
```
