# 회차 실행 절차

개인 브라우저 제어 금지. 인증·권한 부족 시 구체적인 필요한 권한과 이유를 알리고, 브라우저 제어로 자동 전환하지 않는다. 연결 도구·웹 검색·승인된 Git 명령과 공개 HTTP 검증을 우선한다.

## 고정 경로

- 저장소: https://github.com/kohyuji/daily-news-briefing (public, main)
- 홈페이지: https://kohyuji.github.io/daily-news-briefing/
- 원본: `_posts/YYYY-MM-DD-briefing.md` (UTF-8, JSON 형식의 YAML front matter)
- 이미지: `assets/images/YYYY/MM/YYYY-MM-DD/`
- 규칙: `docs/EDITORIAL_RULES.md`
- 성공 상태: `.ops/state.json`, 최근 요약: `.ops/recent-issues.json`
- 회차 출처 메모: `.ops/research/YYYY-MM-DD.json`, 검증 결과: `.ops/runs/YYYY-MM-DD.json`

## 실행

1. 독립 회차에서 규칙·이 문서·성공 상태·최근 요약만 읽는다. 실제 KST 현재 시각으로 조사 기준을 정한다. 금요일 11:00은 시작 시각이며 발행은 검증 완료 시점이다.
2. `git status --short`, `git fetch origin main`, `git merge --ff-only origin/main`. 변경이 있으면 보존하고 충돌을 확인한다. 강제 push·reset 금지. GitHub 연결 도구가 새 저장소에 403을 내면 기존 Git Credential Manager 인증의 `git push`를 사용한다. 토큰을 출력하거나 저장하지 않는다. 인증을 우회하거나 새 자격증명을 만들지 않는다.
3. `python scripts/run_guard.py acquire --run-id <독립실행식별자>`. 기존 lock이 있으면 다른 실행·미완료 여부를 확인하고 중복 작업을 시작하지 않는다. 종료된 이전 실행의 lock만 소유 ID를 확인하여 해제한다.
4. 마지막 성공 cutoff 다음부터 조사한다. 첫 회차만 4일. 필요한 분야에 한해 7일 이내 보충. 새 사건과 이어지는 사건을 최근 요약으로 구분한다. 실제 읽은 원문과 날짜·수치·불확실성·이미지 첫 확인 결과를 짧게 기록한다.
5. `templates/issue.md` 구조를 재사용해 날짜당 Markdown 1개를 완성한다. 메타데이터의 `news_at`은 확인된 새 보도/발표의 날짜이며 시각 미확인 시 날짜의 시작을 정규화 값으로 사용하되 `news_time_precision: date`로 기록한다. 이것을 실제 발표 시각처럼 본문에 제시하지 않는다. 경계일의 시각이 필요하면 원문을 더 확인하거나 제외한다.
6. `python -m pip install -r requirements.txt` (로컬 격리 설치는 `--target .vendor`). `python scripts/build.py`. 수작업 검토: 15개 모두 유사 깊이, 분야별 3개, 중복 사건 없음, 원문 교차 확인, 사건·게시일 분리, 과학 한계, 출처 정확성, 캡션·권리. 빌드는 형식과 링크를 검증할 뿐 사실 검증을 대신하지 않는다.
7. Markdown·확보 이미지·해당 출처 메모만 commit하고 main에 push한다. `_site`는 올리지 않는다. GitHub Actions의 `Build and deploy archive`가 정적 사이트를 빌드·배포한다. 뉴스 생성·AI 호출·예약 cron은 Actions에 넣지 않는다.
8. 동일 커밋의 Actions 배포 성공을 확인한다. 60초 이내 간격으로 필요할 때 확인하며 작업을 끝까지 추적한다. 연결 도구는 commit workflow run 조회, 불가능하면 GitHub 공개 API/Actions 화면을 사용한다. 별도 감시 예약을 만들지 않는다.
9. `python scripts/verify_public.py --date YYYY-MM-DD`로 공개 원본 해시, 회차 15개 앵커·출처·목차, 홈·아카이브·연도·월 목록, CSS·확보 이미지를 확인한다. 새 기능/오류가 있을 때만 PC·휴대전화 화면 QA를 추가한다. 개인 브라우저를 사용하지 않고 검증할 수 없으면 시각적 검증의 한계를 기록한다. 첫 회차는 개인 브라우저 중단 지시에 따라 공개 HTML·CSS·이미지 응답을 확인했으며 회차의 PC·휴대전화 렌더링 화면 검사는 수행하지 않았다. 이미지가 실제 표시 안 되면 제거+미확보 후 재배포한다.
10. 전부 성공하면 `python scripts/verify_public.py --date YYYY-MM-DD --mark-success`. 이 단계 전에는 성공 상태를 수정하지 않는다. 이 스크립트가 최근 이슈를 30개로 제한하여 갱신한다. 요약은 짧게 쓰며 약 2,000토큰을 목표로 유지한다. 상태·요약·검증결과를 별도 commit/push한다. 운영 파일 변경만으로는 재배포하지 않는다.
11. lock을 본인 ID로 해제한다. 정상 최종 응답은 회차 홈페이지 링크 한 줄만. 실패 시 짧은 이유와 실패 상태만 알리고 성공 기준을 보존한다. 예약 알림은 Codex Scheduled의 알림 경로를 쓴다. 메일·메신저 전송은 추가하지 않는다.

## 환경과 예약

예약은 이 프로젝트의 독립 로컬 작업으로 매주 금요일 11:00 Asia/Seoul에 수행한다. 로컬 파일을 쓰므로 컴퓨터가 켜져 있고 앱이 실행 중이며 프로젝트와 Git 인증에 접근 가능해야 한다. 첫 회차의 공개 검증을 통과한 후에만 반복 예약을 활성화한다. 기존 예약은 `$CODEX_HOME/automations/*/automation.toml`에서 목적·프로젝트를 대조하여 재사용하고 중복을 만들지 않는다. 모델·Medium·Standard의 실제 지원과 저장된 값을 확인하여 `.ops/automation.json`에 기록한다. 지원하지 않는 필드를 설정됐다고 보고하지 않는다.

현재 예약 ID는 `automation`이다. 실제 예약 필드에 `model = gpt-6.1-sol`, `reasoning_effort = medium`이 저장되어 있다. 예약 도구에는 독립된 속도 필드가 없으므로 `.codex/config.toml`의 `service_tier = default`로 Standard 기본값을 저장했다. 예약 실행에서의 실제 속도 적용과 OS 알림 수신은 첫 예약 실행 전에는 확인할 수 없다. 이 제한을 모델·추론의 저장 확인과 구분한다. 시스템 시간대는 Korea Standard Time(Asia/Seoul)이며 시간대를 변경하면 예약 시각도 다시 점검한다.

## 참고 문서

- [OpenAI Docs: Scheduled tasks](https://learn.chatgpt.com/docs/automations?surface=app)
- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
