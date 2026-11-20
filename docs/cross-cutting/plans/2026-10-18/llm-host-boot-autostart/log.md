# log — llm-host-boot-autostart

| 시각(KST) | 사건 | 결과 |
|-----------|------|------|
| 10-18 | 사용자 지시("우분투를 다시 키면 llm서비스가 다시켜질 수 있도록")로 명세 합의 · auto | set-state |
| 10-18 | .164 실측 | cron enabled · jun crontab 없음 · llm-boot.sh 없음 |
| 10-18 | 스크립트 작성(scratchpad) → scp 설치 시도 | **실패 — .164 ping·22 무응답**(Windows 전환 추정). 원격 변경 없음 |
| 10-20 09:19 | 사용자 재부팅 후 실측(up 8min) | 3개 컨테이너 unless-stopped로 자동 기동·healthy · 모델 미적재(ollama ps 비어 있음) · seatlab-* 3개도 09:18 기동(본 작업 무관) |
| 10-20 09:19 | `~/llm-boot.sh` 설치 + crontab `@reboot` 등록 | crontab -l = `@reboot /home/jun/llm-boot.sh` |
| 10-20 09:19 | 반증 테스트: 3개 stop 후 스크립트 실행 | 전부 started → 30s 후 wrapper healthy → 36s에 qwen3:8b 100% GPU 적재 · llm-boot.log 기록 확인 |
| 10-20 09:20 | /rewrite 2회(.158→.164) | success 1.61s·1.33s (콜드 timeout 재현 안 됨) |
| 10-20 09:20 | 라이브 문서 챗(엣지 경유) | http 200, 3.9s 스트림 답변 정상 |

## 생략한 검증
- (해소 11-19) 실제 재부팅 `@reboot` 실증 — `~/llm-boot.log` 2026-11-18 07:16 boot start→model preloaded→boot end 기록 확인
