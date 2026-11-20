# log — llm-host-windows

| 시각(KST) | 사건 | 결과 |
|-----------|------|------|
| 2026-10-17 | 명세 합의 · 모드 auto · 자동 로그인 켬(사용자) | set-state spec-approved / mode auto |
| 2026-10-17 | .164 efibootmgr 조회 | BootOrder 0005(Ubuntu),0000(Windows),… · Timeout 1s · GRUB 메뉴 숨김(timeout 0) → Windows 재부팅 시 Ubuntu로 돌아옴. 부팅 순서 변경은 명세 ④ 금지 항목이라 사용자 결정 요청 |
| 2026-10-17 | 사용자 요청: 부팅 시 OS 선택 가능하게 | 명세 ④ 수정 — GRUB 메뉴 10초+os-prober+기본 Windows(saved) 허용, UEFI 순서 무변경. 명령은 사용자가 .164에서 직접 실행 |
| 2026-10-18 | 사용자: .164 Windows 부팅 완료 · 배치 검토(.158 GPU 6GB 중 4.9GB 임베딩 점유 → qwen3:8b 불가) 후 A안(.164 Windows 유지) 확정 | 0단계 사용자 진행 대기 |
| 2026-10-18 | LAN 탐침 | .164 ping 무응답·22 닫힘 — Windows 방화벽 기본(ICMP 차단)·sshd 미설치 상태로 추정 |

| 2026-10-18 | 사용자: "그냥 164 우분투로 쓰자" | **작업 중단** — Windows 이전 안 함. 후속 = `2026-10-18/llm-host-ubuntu-restore` |

## 생략한 검증

(없음)
