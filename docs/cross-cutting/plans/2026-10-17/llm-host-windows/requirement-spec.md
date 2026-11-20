# requirement-spec — LLM 서버(.164)를 Windows(Docker Desktop + WSL2)로 이전

> 2026-10-17. 대상 = 호스트 `.164`(듀얼부팅 — nvme0 Windows / nvme1 Ubuntu) + `study-note-deploy-system-ci-cd`(Windows용 compose 덮어쓰기). llm repo는 무변경 재사용.
> 배경: `.164` Ubuntu의 컨테이너 4개가 2026-10-05 05:23Z containerd 재시작으로 종료(원인 미확정) + 10-09 NVIDIA 595.84→595.99 업그레이드 후 미재부팅으로 GPU 불가 → 12일째 LLM(챗·검색 재작성·llm 자동배포) 다운. 사용자가 `.164`를 **계속 Windows로** 쓰기로 결정 → 서버도 Windows에서 구동.

## ① 목표·대상
`.164`를 Windows로 부팅한 상태에서 **LLM 래퍼(:8000) + Ollama(qwen3:8b, GPU) + ci-cd agent(:15001)** 가 지금 Ubuntu 때와 같은 주소·같은 동작으로 돌아가게 한다. backend(.158)·master(.9) 설정은 **바꾸지 않는다**(주소 `<LAN>.164` 유지).

## ② 경계·불변식
- **주소 불변**: Windows도 `<LAN>.164`(고정 IP 또는 공유기 DHCP 예약). backend의 LLM URL·master의 `AGENT_URL_LLM` 무변경.
- **실행 방식**: Docker Desktop(WSL2 백엔드) + WSL Ubuntu 배포판. repo는 **WSL 안 `/home/jun/...`에 clone** → agent의 동일 경로 마운트(`${HOME}/...`) 그대로 유효. compose는 WSL 셸에서 실행.
- **llm repo 무변경**: 기존 compose 그대로(GPU 예약 = Docker Desktop WSL2 GPU).
- **ci-cd agent Windows 차이는 덮어쓰기 파일로만**: `docker-compose.windows.yml`(신설) — `network_mode: host` 대신 `ports: 15001:15001`, 배포 후 헬스 URL `host.docker.internal:8000`. 기존 Linux 호스트(.9·.158) 동작 무영향.
- **시크릿**: `.env`·`.env.agent` 값(DEPLOY_SECRET 등)은 **사용자가 입력**(메인이 파일시스템에서 찾지 않음). repo에 IP·시크릿 커밋 금지.
- **자동 복구**: Docker Desktop "로그인 시 시작" + 컨테이너 `unless-stopped`. 재부팅 후 자동 복구를 위해 Windows **자동 로그인**·**절전 해제**(사용자 결정 항목).
- **원격 운영**: Windows OpenSSH 서버(키 인증) — 메인이 진단·배포 확인용으로 접속.
- Ubuntu 쪽(nvme1)은 건드리지 않음(그대로 보존).

## ③ 기준소스
`study-note-deploy-system-llm/docker-compose.yml` · `study-note-deploy-system-ci-cd/docker-compose.yml`·`.env.example` · `project-deploy-data/servers/homelab-servers.md` · 실측(.164 lsblk·efibootmgr·docker inspect, 2026-10-17).

## ④ 금지영역
backend·front·llm 코드 변경 금지. Ubuntu 파티션 변경 금지. 부팅은 GRUB 메뉴 표시(10초)·기본값 Windows·os-prober만 허용(사용자 결정 10-17 — UEFI BootOrder 무변경). Linux 호스트용 ci-cd compose 동작 변경 금지(덮어쓰기 파일만 추가). 시크릿 값 기록·커밋 금지.

## ⑤ 검증 방법
- Windows 컨테이너: `docker ps`(llm-ollama·llm-wrapper·ci-cd-agent healthy) · ollama 컨테이너에서 GPU 인식(`nvidia-smi`) · `ollama ls`에 qwen3:8b.
- LAN 도달: .158에서 `curl <LAN>.164:8000/health` · .9 master → agent `:15001/health`.
- 기능: 라이브 검색에서 `rewrite_used=true` · 문서 챗 스트림 응답 · llm repo 빈 커밋 push → Actions → master → agent 배포 ok(실패 플래그 없는 워크플로 문제는 run 로그 http 코드로 직접 확인).
- 복구: Windows 재부팅 → 로그인 후 컨테이너 자동 기동 확인.
- 반증: Windows 방화벽이 8000/15001을 막나? WSL 메모리 상한으로 ollama OOM? Docker Desktop 업데이트 팝업이 기동을 막나?

## ⑥ stakes: 중간~높음
서버 이전(운영 인프라)·원격 실행 표면(agent docker.sock)·방화벽 개방. 데이터 삭제 없음, Ubuntu 보존으로 되돌리기 가능.

## 단계
- **0단계(사용자, 서버 앞에서)**: Windows 부팅 → IP .164 확인 → NVIDIA Windows 드라이버 → `wsl --install -d Ubuntu-24.04` → Docker Desktop(WSL 통합·로그인 시 시작) → OpenSSH 서버 + 공개키 등록 + 방화벽 22 → 절전 해제(·자동 로그인 결정)
- **1단계(메인, 원격)**: WSL에 repo clone · `.env` 틀 생성(값은 사용자) · llm `compose up` + qwen3:8b pull · 방화벽 8000/15001
- **2단계(메인)**: ci-cd `docker-compose.windows.yml`(이슈→PR) + agent 기동 · master 라우팅 확인 · 배포 E2E
- **3단계**: 라이브 검증 · `homelab-servers.md` 갱신(.164 = Windows) · 재부팅 복구 테스트

## 자율성
auto 제안(0단계는 사용자 수작업).

## load-bearing 가정 (착수 직후 실증)
1. Docker Desktop WSL2에서 llm compose의 nvidia GPU 예약이 그대로 동작 — 1단계 첫 기동에서 `nvidia-smi`로 확인.
2. Docker Desktop의 published port(8000·15001)가 Windows 호스트 IP로 LAN에 노출 — .158/.9에서 curl로 확인.
