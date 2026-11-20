# requirement-spec — .164 Ubuntu에서 LLM 서비스 복구

> 2026-10-18. 선행 작업 `2026-10-17/llm-host-windows`는 사용자 결정("그냥 164 우분투로 쓰자")으로 **중단** — Windows 이전 안 함.
> 재부팅으로 NVIDIA 드라이버 불일치 해소 확인(595.99.02 로드, RTX 2070 SUPER 인식, 2026-10-18 00:23 KST).

## ① 목표·대상
.164 Ubuntu의 정지된 컨테이너 `llm-ollama`·`llm-wrapper`·`ci-cd-agent`를 **기존 구성 그대로 재기동**해 문서 챗·검색 재작성·llm 자동배포를 복구.

## ② 경계·불변식
기존 컨테이너를 `docker start`로만 기동(재생성·재빌드·이미지 갱신 없음) · 주소·포트·설정 무변경 · 모델 볼륨 `study-note-deploy-system-llm_ollama-models` 재사용(재다운로드 없음).

## ③ 기준소스
.164 실측(docker ps -a·nvidia-smi) · llm/ci-cd `docker-compose.yml`.

## ④ 금지영역
코드·compose·.env 변경 금지 · `ledger-app-1` 손대지 않음(사용자 지시) · 부팅 설정 변경 없음(GRUB 변경 계획 철회).

## ⑤ 검증 방법
3개 컨테이너 healthy · ollama 컨테이너 `nvidia-smi`·`ollama ls`(qwen3:8b) · .158에서 `:8000/health` · .9에서 agent `:15001/health` · 라이브 검색 rewrite_used / 챗 응답.

## ⑥ stakes: 낮음
기존 컨테이너 재기동만, 데이터 변경 없음, 되돌리기 = docker stop.

## 자율성
auto (사용자 지시로 착수).

## load-bearing 가정
재부팅 후 ollama 컨테이너가 GPU를 잡는다 — 기동 직후 `nvidia-smi`로 확인.

## 후속(별도 작업 후보)
12일 전 종료 후 `unless-stopped`인데 자동 재기동되지 않은 원인 · 컨테이너 다운 알림 부재.
