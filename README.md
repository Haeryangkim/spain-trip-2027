# 스페인 여행 계획 2027 · 마드리드 → 마요르카 → 바르셀로나

**2027-04-25 (일) 울산 출발 → 2027-05-07 (금) 울산 도착 · 12박 13일**

일자별 타임라인, 도시별 동선 지도(Leaflet + OpenStreetMap), 구글 평점 3.5 이상 맛집, 안전 가이드, 예약 체크리스트를 담은 단일 파일 웹사이트입니다.

## 보기
- `index.html` 을 브라우저에서 열면 됩니다 (인터넷 연결 시 OSM 실시간 타일, 오프라인이어도 내장 베이스맵으로 지도 표시).
- 로컬 서버: `python3 -m http.server 8765` → http://127.0.0.1:8765/

## 구조
| 경로 | 설명 |
|---|---|
| `index.html` | 빌드 결과물 (자체 완결형, 이 파일만 있으면 동작) |
| `data/itinerary.json` | 일정·맛집·안전·예약 데이터 (원본) |
| `data/research.json` | 조사 원자료 (명소·맛집·교통·항공·안전) |
| `site/template.html` | 페이지 템플릿 (HTML/CSS/JS) |
| `assets/` | 도시별 내장 베이스맵(OSM 타일 합성), Leaflet CSS |
| `build.py` | `data/itinerary.json` + 템플릿 + 에셋 → `index.html` |

## 다시 빌드
```bash
python3 build.py            # data/itinerary.json 사용
python3 build.py other.json # 다른 데이터 파일 사용
```

## 주의
- 2027년 항공·열차 시간표와 입장료는 미공개 상태라 2025~2026년 운영 패턴을 기준으로 작성했습니다. 출발 2~3개월 전 공식 사이트에서 재확인하세요.
- 구글 평점은 조사 시점(2026-08) 기준입니다.
- 숙소는 계획 확정 후 별도로 예약 (추천 동네는 안전 가이드 참고).

지도 데이터 © OpenStreetMap contributors.
