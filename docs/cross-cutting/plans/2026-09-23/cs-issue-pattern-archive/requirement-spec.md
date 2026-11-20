# requirement-spec — 작업2: 배포 이슈 → CS 패턴 아카이브 (cs/issue/)

> 작업 폴더 생성: 2026-09-23. 대상 = **study-note** (git·배포 위키). 처리 기록 = deploy-study-note/docs.
> 입력: 워커 digest(34개 이슈 원문 분석, 2026-09-23) — backend12·front11·llm6·ci-cd5.

## ① 목표·대상
study-note-deploy-system을 만들며 겪은 34개 이슈를 **재사용 가능한 CS 패턴**으로 추상화해 `study-note/cs/issue/` 아카이브로 정리한다. 프로젝트 특수사정이 아니라 "프로젝트 밖에서도 통하는 원리"로 카드화하고, 각 카드는 이번 사례(project/study-note-deploy-system/<repo>/issueN)를 링크한다.

- **단위**: 패턴 단위(묶음). 같은 패턴을 공유하는 여러 이슈를 한 카드가 링크(예: silent-failure 1장이 7개 이슈 링크). 1:1 아님.
- **포맷**: cs 1/2/3 인출퀴즈형(`1-question.md`/`2-summary.md`/`3-answer.md`) — 기존 cs 리프 컨벤션·헤더 준수, Claude 초안 표시.

## ② 경계·불변식
- **최상위 = 언어별, 프레임워크는 언어 하위 중첩**(사용자 결정). cross-cutting은 시스템·네트워크 계층별 세분화.
- 제안 트리:
```
cs/issue/
  README.md            — 아카이브 안내 + 전체 인덱스(패턴·소속·메타태그 표)
  kotlin/              — backend (Kotlin/Spring). 프레임워크는 spring/ 중첩
    spring/
  typescript/          — front. react/ · next/ 중첩
    react/
    next/
  python/              — llm. fastapi/ 중첩
    fastapi/
  cross-cutting/       — 언어 무관 시스템·네트워크 (계층별 세분화)
    network/           — tcp·http·프로토콜·터널
    infra/             — docker/compose·git·nginx·배포동기화
    reliability/       — silent-failure·자원상한 (축을 가로지르는 메타 패턴)
    security/          — 시크릿·최소권한
```
- **기존 cs 트리 훼손 금지**: cs/issue/는 신설. 기존 systems·ops-patterns 등 미변경.
- **시크릿 0**: 카드에 시크릿 값·내부 IP·자격증명 없음(개념·사례 링크만).
- **project/ 이슈 문서는 정본 유지**: 아카이브는 그것을 링크·추상화만, 원문 수정·이동 없음.
- **위키 트리**: cs/issue/ 신설은 cs 하위 새 주제로 자동 노출(코드 변경 없음 — 작업1 가정①과 동일).

## ③ 기준소스
- 이슈 내용: `study-note/project/study-note-deploy-system/<repo>/issueN/README.md`(실파일).
- 패턴의 코드 기준소스: 각 서비스 repo 실코드(deploy-study-note/study-note-deploy-system-*).
- cs 1/2/3 포맷 기준: `cs/systems/lsm-tree/`, `cs/ops-patterns/01-retry-backoff/`(실파일).

## ④ 금지영역
- 기존 cs 리프·project 이슈 문서·서비스 코드 repo 변경 금지.
- 이슈2(BFF·쿠키 3금기 결정문서 신규 작성)는 **별도 작업** — 본 작업은 "겪은 이슈의 패턴화"만. (통합 여부는 사용자 확인.)
- 시크릿·내부 IP 유입 금지.

## ⑤ 검증 방법
- **스모크**: 생성 후 트리 구조·각 카드 3파일·헤더·사례 링크 유효성(링크 경로 존재) 확인.
- **매핑 검증**: 각 이슈가 최소 1개 카드에 링크됐는지(34개 커버리지) 대조표.
- **시크릿 재스캔**: 생성물 전체 grep(IP·시크릿 패턴).
- **반증**: 패턴이 프로젝트 특수사정으로 좁혀지지 않았나(재사용성)? 링크가 실제 이슈를 가리키나? 1/2/3 상호참조 링크가 깨지지 않나?
- **커밋**: 제가 `cs/issue/`만 선택 스테이징 → 커밋. ⚠️ 사용자 react WIP 동시 커밋 중이므로 **모든 파일 생성 후 마지막에 1회 커밋**(인터리브 최소화), 스테이징 경로 재확인. push는 사용자 몫.

## ⑥ stakes: 중간
근거: 배포 위키 콘텐츠 대량 신설 + 동시성 있는 저장소 커밋. 단 git 복구 가능·기존 훼손 없음. 산출물 유형 = study 문서(실행물 아님) → 셀프+스모크 비례, codex 듀얼 부적용.

## 자율성: auto

## 제안 패턴 목록 (digest 기반 — 확정 대상)
**cross-cutting/reliability**: ①silent-failure(성공≠산출물: be2·10·front3·llm1·3·cc2·3) ②자원상한=유일방어선(be5·12·llm1·cc)
**cross-cutting/security**: ③시크릿 단일소유·최소권한·정본(be10·front4·cc3)
**cross-cutting/network**: ④chunked vs Content-Length(be12·cc4) ⑤HTTP스트리밍 헤더후 status불변(llm6) ⑥bind loopback vs LAN·헬스체크 정합(be1·9·cc3) ⑦프록시 passthrough 버퍼링·쿠키왕복(front3·11) ⑧역터널/NAT traversal(cc4)
**cross-cutting/infra**: ⑨compose 변수 해석시점(cc1·2) ⑩상태 드리프트: 삭제전파·설정채널(be6·cc2) ⑪git 함정: dubious-ownership·빈디렉토리·quotepath(cc2·front3·be2) ⑫nginx 광역방어 아군오사(cc5)
**kotlin(/spring)**: ⑬직렬화 계약 누출(be7) ⑭DIP·포트소유·응집(be8) ⑮문자인코딩·JVM기본값(be2)
**typescript(react/next)**: ⑯BFF envelope 단일창구(front1·4) ⑰절대경로 모듈정책·리졸버(front6·7) ⑱CSS 음수마진 overflow(front8) ⑲XSS 이스케이프후조립(front9·be11) ⑳관심사분리·SSOT(front2·10)
**python(fastapi)**: ㉑응답정규화 프레임워크밖응답(llm4) ㉒PYTHONPATH 우연한통과(llm3) ㉓YAGNI dead-contract(llm5)

→ 약 23패턴 × 1/2/3 = ~69파일. 대량이라 **범위/단계 확인 필요**(전량 일괄 vs 단계 vs 부분).

## load-bearing 가정
1. cs/issue/ 신설은 코드 변경 없이 위키 트리에 자동 노출(작업1 실증과 동일 로직).
2. 패턴 authoring은 독립 버킷별 병렬 워커 위임 가능(§5) — 메인이 패턴목록·매핑·최종조립·커밋 소유. 워커는 실파일(이슈+코드) 읽기 강제.
