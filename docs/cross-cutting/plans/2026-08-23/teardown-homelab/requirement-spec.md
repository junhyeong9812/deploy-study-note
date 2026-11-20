# 요구사항 명세 — 홈랩 3대 정리 (jun-bank 외 전부 제거)

| 칸 | 내용 |
|----|------|
| ① 목표·대상 | 집 서버 .9/.158/.164에서 **jun-bank 관련을 제외한 모든 가동 컨테이너·볼륨·호스트 프로세스·홈 디렉토리 잔재** 제거. 자원·포트(9000/10000/11000/12000 포워딩, 오라클 www/admin/mcp/readlog conf·인증서)는 재활용 위해 **유지** |
| ② 경계·불변식 | **유지**: jun-bank — `gateway-app-1`(13080) `core-green-app-1`(13002) `jun-deploy-mysql`(+`jun-deploy-mysql-data`) `settlement-app-1`(.158:13001) `ledger-app-1`(.164:13002) `jun-agent`(13000/13100) `~/jun-deploy` `~/jun-bank` `ghcr.io/jun-bank/*` 이미지. **재활용 유지**: .164 `llm-ollama` 컨테이너+`llm_ollama` 볼륨(모델만 삭제), .158 `embedding-embedding` 이미지+`embedding_hf-cache`(BGE-M3 가중치). 오라클·공유기·DNS **무접촉**. SSH 키 무접촉 |
| ③ 기준소스 | 2026-08-23 21:2x 실측 인벤토리(log.md 첨부) · `project-deploy-data/` |
| ④ 금지영역 | jun-bank 자원 일체 · `sudo` 필요 작업은 자동 실행 안 함(암호) → 사용자 터미널 안내 · 오라클 nginx/인증서 · `docker system prune -a`류 전역 명령(jun-bank 이미지 휩쓸림) |
| ⑤ 검증 방법 | 삭제 전 Readlog PG 최종 덤프(`~/readlog-backups/`) · 삭제 후 `docker ps -a`·`docker volume ls`·`ss -ltn`에 유지 목록만 남는지 대조 · jun-bank 컨테이너 healthy 유지 · jun-bank 포트(13000·13001·13002·13080·13100) 응답 확인 |
| ⑥ stakes | **높음**(불가역 데이터 삭제 — 볼륨 `core_es-data`·`core_pg-data`·`server_readlog-pgdata` 등) |

- 자율성: **auto** (단 실행 직전 본 명세 사용자 확인 1회)
- load-bearing 가정: (1) 사용자 "jun-bank 외 전부" = 다른 실험 잔재(orchestrator·crawlers·cache-split-lab·piston·mariadb·vllm 이미지)도 포함 (2) `docker compose down -v`는 해당 프로젝트 볼륨만 지운다

## 삭제 목록 (실측 기준)

### .9
- compose down -v: `admin` `api` `core`(es+pg) `mcp` `web` `server`(readlog app+pg)
- 볼륨: `core_es-data` `core_pg-data` `server_readlog-pgdata` `server_readlog-export` `crawlers_datahub-pgdata` `infra_orch-pgdata` `infra_orch-redis-data`
- 이미지: `api-api` `admin-admin` `web-web` `mcp-mcp` `core-elasticsearch` `readlog-server:local` `orchestrator-orchestrator` `postgres:16` `postgres:16-alpine` `grafana/k6` `eclipse-temurin:21-jre`(jun-bank 이미지 base면 보류) + dangling `ghcr.io/jun-bank/*:<none>` 구버전(롤백용일 수 있어 **보류**)
- 프로세스: `claude_bridge.py`(jun, :9099) kill · `metrics-agent`(systemd, **sudo**) · `intel-daily.timer`(systemd, **sudo**)
- 홈: `admin api core mcp web indexer intel intel-logs orchestrator projects projects-docs projects-logs projects-work readlog metrics-agent *.bak-20260806-1635 claude_bridge.* claude-bridge.service research-bridge.* start-research-bridge.sh cache-split-lab-k6` → 삭제 대신 `~/_trash-20260823/`로 이동(1주 후 삭제)
- 유지: `readlog-backups`(최종 덤프 포함) `jun-deploy` `jun-bank`

### .158
- compose down: `embedding`(컨테이너만 — 이미지·hf-cache 유지)
- 볼륨: `crawlers_datahub-pgdata` `infra_orch-*` `orchestration_orch-*` `mariadb_data` `piston-data`
- `metrics-agent`(systemd, sudo) · 홈 `metrics-agent*` `embedding.bak-*` → _trash

### .164
- `docker exec llm-ollama ollama rm qwen2.5:7b` · `llm_hf-cache`(5.6GB, vllm용) 삭제 · 이미지 `vllm/vllm-openai`(29.8GB) `cache-split-*` 13개 `redis` `nginx` `nvidia/cuda` 삭제 · dangling 볼륨 3개
- 호스트 `ollama serve`(root pid 1517, **sudo**) — 컨테이너와 중복, 사용자 판단
- `metrics-agent`(sudo) · 홈 `cache-split-lab` `work` `metrics-agent*` → _trash
