# requirement-spec — .164 Linux 부팅 시 LLM 서버 자동 기동

> 2026-10-18. 사용자가 Windows ↔ Ubuntu를 오가므로, Ubuntu로 켤 때마다 LLM 서버가 손 안 대고 살아나야 한다.

## 실측 (10-18 00:3x)
- `docker`·`docker.socket`·`containerd` = enabled(부팅 시 자동 시작) · nvidia runtime 등록됨
- llm-ollama·llm-wrapper·ci-cd-agent = restart `unless-stopped`, running
- 공백: ①한 번 멈춘(stop/정상 종료) 컨테이너는 `unless-stopped`라 부팅해도 안 살아남(10-05 사고 형태) ②부팅 직후 모델 미적재 → 첫 재작성 몇 건 5s timeout(오늘 실측)

## ① 목표·대상
.164 Ubuntu 부팅마다 ①3개 컨테이너 기동 보장 ②qwen3:8b GPU 선적재. 대상 = .164 `jun` crontab `@reboot` + 스크립트 `~/llm-boot.sh`(sudo 불필요).

## ② 경계·불변식
스크립트는 기존 컨테이너 `docker start`만(재생성·빌드·pull 없음) · docker 준비까지 대기(최대 120s) 후 실행 · 선적재는 wrapper 컨테이너 경유 ollama `/api/generate`(빈 프롬프트) · 결과는 `~/llm-boot.log`에 시각과 함께 기록(실패 가시화) · 이미 떠 있으면 무해(idempotent).

## ③ 기준소스
.164 실측 · llm/ci-cd `docker-compose.yml`(컨테이너명).

## ④ 금지영역
llm·ci-cd repo 변경 없음 · compose·.env·restart 정책 변경 없음 · systemd/sudo 설정 변경 없음 · ledger-app-1 제외.

## ⑤ 검증 방법
①스크립트 수동 실행(running 상태에서 무해 확인) ②사용자 재부팅 → 로그인 없이 3개 healthy · `ollama ps` 100% GPU · `~/llm-boot.log` 기록 · 첫 /rewrite success ③반증: 컨테이너를 stop한 상태로 재부팅해도 살아나는가(①에서 stop→스크립트 실행으로 대체 확인).

## ⑥ stakes: 낮음
사용자 crontab 1줄+스크립트, 삭제로 원복.

## 자율성
auto.

## load-bearing 가정
cron `@reboot`가 jun 계정으로 부팅 시 실행되고 docker 그룹 권한으로 `docker start` 가능 — 재부팅 1회로 실증.
