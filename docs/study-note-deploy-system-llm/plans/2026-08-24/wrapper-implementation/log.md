# log — wrapper-implementation
| 시각 | 사건 | 결과 |
|---|---|---|
| 2026-08-24 | 명세 승인(AskUserQuestion) | 머지까지 위임 · CD는 후속(Go 배포 서버 공동 설계 예약) |
| 2026-08-24 | 구현+단위테스트 8건 green(docker) | base 1bb73ce → b25d168, packet 생성·보안스캔 0건 |
| 2026-08-24 | 사용자 피드백: 축약 변수명 금지 | 전 파일 반영(48db825) + 메모리 저장, 테스트 8건 green 유지 |
| 2026-08-24 | 듀얼 리뷰 ① 병렬 시작 | packet=1bb73ce..b25d168(+48db825은 재점검 대상) · Opus 워커 + codex(medium) |
| 2026-08-24 | ② 종합 + ③ codex 감사 | 채택 L1~L9(상세: scratchpad synthesis.md → 아래 ledger) · 감사 6건 중: extra=forbid·response_model 채택 / L5 이의 **실측 기각**(conftest 제거 시 collection error 재현) / L8은 D2에 상한 명문화로 채택 / env 노브는 D3에 "실측 조정용" 명문화 / content 손상→422 경로는 기구현 확인 |
| 2026-08-24 | 사용자 절차 지시 | 추가 요구(requestId·로깅=#2, src 미러 구조=#3)는 이슈 분리 — 진행 브랜치에서 해당 스코프 제거(scratchpad 보관) |
| 2026-08-24 | ④ 수정 커밋 f9c613c | 테스트 12건 green(`pytest` 원명령으로 검증) |

## 리뷰 ledger (듀얼 1패스)
| id | source | disposition | status |
|---|---|---|---|
| L1 계약 불일치(filters) | codex+opus | 채택(high) | fixed f9c613c |
| L2 총예산 타임아웃 | codex+opus | 채택 | fixed |
| L3 health 503 | codex+opus | 채택 | fixed |
| L4 업스트림 정규화 | codex+opus | 채택 | fixed |
| L5 conftest | opus | 채택(감사 이의 실측 기각) | fixed |
| L6 로깅 | opus+사용자 | 채택→**#2 이슈로 이관** | deferred(#2) |
| L7 digest 계약 모델 | codex | 채택 | fixed |
| L8 query 상한 | opus | 채택(D2 명문화) | fixed |
| L9 502→503 통일 | opus | 채택 | fixed |
| 감사: extra=forbid·response_model | codex감사 | 채택 | fixed |
| 2026-08-24 | post-fix 재점검(codex) | 신규 1건: 오류 계약 문장 과일반화(/digest 501 충돌) → 문서 정정 커밋. 그 외 clean |
| 2026-08-24 | .164 스모크 1단계 | compose 기동 · health 503 model_missing 실증(L3) · 11434 비노출 확인 · qwen3:8b pull 진행 |
| 2026-08-24 | #2 로깅 브랜치 | request_id 필수·logger.py(XADD, 실패무해)·규약 docs/logging.md·Redis 6379 예약 — 13건 green |
| 2026-08-24 | #3 src 미러 브랜치 | src/app ↔ src/test 미러, 모듈 테스트 분리 — 25건 green |
| 2026-08-24 | .164 스모크 중 실결함 발견 | `/no_think` 소프트 스위치 무효 → thinking 폭주 31k+ 토큰(GPU 점유 지속, 클라이언트 절단 무시). fix: API think:false + num_predict 512 |
| 2026-08-24 | 최종 스모크 (측정) | 콜드 3.56s·웜 1.33s(200, filters 정상) · 동시 3발: 503 7.7ms/200 1.3s/200 2.6s · 로그 규약 포맷 확인. [구현 검증] #1·#5 1차 실측치 확보 |
| 2026-08-24 | 이슈·PR 일괄 처리 | 이슈 #1~#3 · PR #4(#1)·#5(#2)·#6(#3) 생성→순차 머지. main = 2bcc8c4 |

## 완료 요약
- **산출물**: study-note-deploy-system-llm main — compose(ollama 내부전용+wrapper:8000) + FastAPI(src/app ↔ src/test 미러, 테스트 25건)
- **계약**: /rewrite {request_id, query} → {intent, keywords, expanded, filters{topic,doc_kind}} · 오류 503(busy|upstream|upstream_timeout)/422 · /digest 계약 예약(501) · /health 모델 존재 확인
- **핵심 diff (실파일 wrapper/src/app/usecase/rewrite.py)**:
  before: `"options": {"temperature": 0},`  (+프롬프트 "/no_think")
  after:  `"think": False, ... "options": {"temperature": 0, "num_predict": 512},`
- **실측**: 콜드 3.56s · 웜 1.33s · 동시 3발 503(7.7ms)/200(1.3s)/200(2.6s) · 폭주 재발 없음
- **배포**: .164 가동 중(healthy). 리뷰: 듀얼 1패스 + 감사 + post-fix 재점검(ledger 상기)
