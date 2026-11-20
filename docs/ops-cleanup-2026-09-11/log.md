# 502/504 조사·정리 (2026-09-11)

## 진단
- www.junproject.xyz(실서비스) 5xx = 0건. 컨테이너 3대 전부 healthy. 색인 최신(HEAD 일치).
- 502/504는 전부 죽은 도메인(admin:10000·mcp:9000·readlog:12000, 업스트림 "닫힘")에
  봇 스캐너(serverless.yml.bak·owa/auth/logon.aspx 등)가 긁을 때 발생.
- 원인: teardown(2026-08-23)에서 "오라클 conf 재활용 위해 유지"했으나 실제 재활용은
  www 하나뿐. admin·mcp·readlog conf가 죽은 채 남아 502 양산 + 봇 트래픽을 집으로 유입.

## 조치: 죽은 conf 제거 (admin·mcp·readlog), www·apex·00-map·deploy·bank 유지

## 결과
- 오라클: admin·mcp·readlog conf 제거(/tmp에 .removed 백업) → nginx -t 통과 → reload
- 로컬 사본(project-deploy-data/edge/nginx/conf.d) 동기화 · routing.md 갱신
- 검증: 죽은 도메인 3개 000(연결 거부), www 실서비스 전부 200
- 잔여(후속): 공유기 포워딩 9000·10000·12000 제거 · 죽은 도메인 인증서 갱신 중단
- study-note action은 정상 가동 확인(마지막 sync SHA = HEAD 일치) — 최신화 안 되는 것처럼 보인 건 502 화면 탓

## 2026-09-12 후속 — 능동 차단 추가
- rate limit(perip 10r/s·burst20) + 봇 UA 444 + 스캔경로 444를 01-security.conf·www conf에 적용
- "차단이 목표가 아니라 통로를 좁힌다"의 연장: 죽은 통로 제거(9/11) → 남은 통로에 문지기(9/12)
- 검증: 정상 브라우저 200 / 스캐너·민감경로 444. 로컬 사본·routing.md 동기화
