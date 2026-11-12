# 세상을 읽는 시간

매주 금요일, 중요한 뉴스 15개를 다섯 분야의 배경·인과관계·질문으로 읽는 한국어 학습형 뉴스 브리핑입니다.

- [공개 홈페이지](https://kohyuji.github.io/daily-news-briefing/)
- [연도·월별 아카이브](https://kohyuji.github.io/daily-news-briefing/archive/)
- 원본: `_posts/YYYY-MM-DD-briefing.md`
- 운영 규칙: [docs/EDITORIAL_RULES.md](docs/EDITORIAL_RULES.md)
- 회차 절차: [docs/RUNBOOK.md](docs/RUNBOOK.md)

## 구조

Work/Codex가 독립 회차에서 뉴스를 조사하고 Markdown을 저장합니다. GitHub Actions는 Python의 작은 정적 빌더로 이 본문을 HTML로 변환하고 GitHub Pages에 배포합니다. 홈페이지·연도·월 목록은 발행일 메타데이터에서 자동 생성됩니다. 사이트 방문 시 AI나 외부 데이터 API를 호출하지 않습니다. 별도 AI API·유료 서비스는 사용하지 않습니다.

```text
_posts/                         회차별 Markdown 원본
assets/images/YYYY/MM/DATE/      재게시 조건을 확인한 실제 이미지
templates/                      고정 화면·기사 구조
scripts/                        빌드·링크검사·공개검증·실행잠금
.ops/                           성공 상태·최근 이슈·출처 메모 (배포 제외)
docs/                           고정 편집 규칙·실행 절차 (배포 제외)
```

JSON 형식의 front matter는 YAML의 부분집합입니다. 날짜는 `+09:00`으로 명시합니다. 배포 디렉터리는 허용한 공개 콘텐츠만 포함하여 운영 파일·출처 작업 메모가 홈페이지·사이트맵에 나타나지 않습니다. 저장소 자체는 공개이므로 비밀정보를 저장하지 않습니다.

## 빌드와 발행 확인

```sh
python -m pip install -r requirements.txt
python scripts/build.py
python scripts/verify_public.py --date YYYY-MM-DD
```

배포 성공과 공개 검증 후에만 `--mark-success`를 붙여 성공 기준과 최근 이슈 요약을 갱신합니다. 기존 회차는 보존하며 같은 날짜는 같은 문서를 갱신합니다. 정상 발행 알림은 공개 회차 링크 한 줄입니다.

## 이용조건

각 기사 출처의 원문 권리는 해당 권리자에게 있습니다. 이미지는 각 캡션에 표시한 이용조건을 따릅니다. 저장소에 포함되었다는 이유로 외부 이미지·원문에 새로운 자유이용 허락을 부여하지 않습니다.
