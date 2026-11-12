# 데일리 뉴스 브리핑

매 실행에서 `docs/EDITORIAL_RULES.md`, `docs/RUNBOOK.md`, `.ops/state.json`, `.ops/recent-issues.json`만 먼저 읽는다. 저장소나 과거 본문 전체를 읽지 않는다. 필요한 이전 기사만 선택적으로 확인한다.

- 독립된 Work/Codex 회차에서 조사·집필한다. AI API·유료 서비스·Actions의 뉴스 생성 금지. 요청 없는 하위 에이전트와 중복 조사 금지.
- 고정 구조는 유지한다. 회차 Markdown 1개, 확보한 이미지, 회차의 출처 메모, 최근 이슈 요약만 변경한다. 템플릿·스타일·빌드는 기능 변경 또는 오류 수정 때만 수정한다.
- 5개 분야 각 3개, 총 15개. 정확성·배경·학습 가치 우선. 이미지는 한 차례 확인하고 재탐색하지 않는다. 미확보는 정상 상태다.
- 기존 발행본을 보존한다. 날짜가 같은 재실행은 같은 `_posts/YYYY-MM-DD-briefing.md`를 갱신한다.
- `python scripts/build.py`를 실행한다. 웹은 이 Markdown의 본문에서만 생성된다.
- 실제 배포와 공개 회차·연도·월 목록·이미지를 검증한 뒤에만 `python scripts/verify_public.py --date YYYY-MM-DD --mark-success`로 성공 기준 시각을 갱신한다.
- 성공 상태와 이슈 요약을 Git에 반영한 뒤 정상 알림은 회차 홈페이지 링크 한 줄만 보낸다. 실패는 이유를 짧게 보고하며 성공이라 하지 않는다.
- 예약: 금요일 11:00 Asia/Seoul, 독립 프로젝트 작업. 실제 모델 gpt-6.1-sol / reasoning medium / Standard. 프롬프트로 설정을 대신하지 않는다.
