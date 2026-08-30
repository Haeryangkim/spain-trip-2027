# 스페인 여행 계획 2027 · 마드리드 → 마요르카 → 바르셀로나

**2027-04-25 (일) 울산 출발 → 2027-05-07 (금) 인천 도착 · 12박 13일**
항공: 에미레이트 두바이 경유 서울–마드리드 왕복 (EK323 4/25 23:55 → 4/26 13:30 MAD · EK142 5/6 15:25 MAD → 5/7 17:00 ICN) · 마지막 밤은 마드리드로 복귀

일자별 타임라인, 도시별 동선 지도(Leaflet + OpenStreetMap), 구글 평점 3.5 이상 맛집, 안전 가이드, 예약 체크리스트를 담은 단일 파일 웹사이트입니다.

## 공유 링크 (Streamlit Community Cloud)

| | 주소 |
|---|---|
| **여행 계획 앱** | **https://spain-trip-2027.streamlit.app** |
| 페이지 원본 (전체 화면) | https://spain-trip-2027.streamlit.app/app/static/index.html |

> ⚠️ 위 주소는 **최초 1회 배포를 마친 뒤부터** 열립니다. 배포 방법은 아래 [Streamlit 배포](#streamlit-배포-최초-1회) 참고.

## 보기
- **온라인**: 위 공유 링크 (배포 후)
- **로컬 파일**: `index.html` 을 브라우저에서 열기 (인터넷 연결 시 OSM 실시간 타일, 오프라인이어도 내장 베이스맵으로 지도 표시)
- **로컬 서버**: `python3 -m http.server 8765` → http://127.0.0.1:8765/
- **로컬 Streamlit**: `pip install -r requirements.txt && streamlit run streamlit_app.py`

## Streamlit 배포 (최초 1회)

Streamlit Community Cloud 는 GitHub 로그인이 필요해 웹에서 직접 눌러야 합니다.

1. https://share.streamlit.io 접속 → **Continue with GitHub** 로 로그인 (계정 `Haeryangkim`)
2. **Create app → Deploy a public app from GitHub** 선택 후 아래 값 입력
   (또는 이 링크로 바로 이동: <https://share.streamlit.io/deploy?repository=Haeryangkim%2Fspain-trip-2027&branch=main&mainModule=streamlit_app.py>)
   | 항목 | 값 |
   |---|---|
   | Repository | `Haeryangkim/spain-trip-2027` |
   | Branch | `main` |
   | Main file path | `streamlit_app.py` |
   | App URL (Custom subdomain) | `spain-trip-2027` |
3. **Deploy** → 1~3분 뒤 https://spain-trip-2027.streamlit.app 활성화
4. 이후 `main` 에 push 하면 자동으로 재배포됩니다.

**저장소 공개 여부**
- 이 저장소는 현재 **private** 입니다. Community Cloud 무료 플랜은 private 저장소로 만든 앱을 **1개**만 허용하고, 앱을 볼 사람을 이메일로 초대해야 합니다.
- 링크만 있으면 누구나 볼 수 있게 하려면 저장소를 공개로 바꾸는 편이 간단합니다 (여행 일정이라 민감 정보는 없습니다):
  ```bash
  gh repo edit Haeryangkim/spain-trip-2027 --visibility public --accept-visibility-change-consequences
  ```
- `spain-trip-2027` 서브도메인이 이미 사용 중이면 다른 이름(예: `spain-2027-haeryang`)으로 만들고 위 표의 주소를 그에 맞게 고쳐주세요.

## 구조
| 경로 | 설명 |
|---|---|
| `index.html` | 빌드 결과물 (자체 완결형, 이 파일만 있으면 동작) |
| `data/itinerary.json` | 일정·맛집·안전·예약 데이터 (원본) |
| `data/research.json` | 조사 원자료 (명소·맛집·교통·항공·안전) |
| `site/template.html` | 페이지 템플릿 (HTML/CSS/JS) |
| `data/image_map.json` | 명소·맛집 → 사진 슬러그 매핑 |
| `assets/base_*.jpg` | 도시별 내장 베이스맵 (OSM 타일 합성) |
| `assets/img/*.jpg` | 명소·요리 대표 사진 (위키미디어 커먼즈) |
| `assets/image_credits.json` | 사진 저작자·라이선스 (페이지 하단에 표기) |
| `build.py` | `data/itinerary.json` + 템플릿 + 에셋 → `index.html` (+ `static/index.html` 사본) |
| `streamlit_app.py` | Streamlit Community Cloud 공유용 래퍼 (페이지 임베드 + 일자 바로가기) |
| `.streamlit/config.toml` | 정적 서빙(`app/static/…`) 및 테마 설정 |
| `requirements.txt` | Streamlit 배포용 의존성 |
| `static/index.html` | 브라우저가 직접 받아가는 페이지 사본 (build.py 가 자동 생성) |
| `fetch_images.py` | 위키피디아/커먼즈에서 사진 수집 → `assets/img/` |
| `validate.py` | 일정 데이터 점검 (날짜·시간 겹침·좌표·평점) |

## 다시 빌드
```bash
python3 validate.py         # 일정 데이터 점검
python3 build.py            # data/itinerary.json 사용
python3 build.py other.json # 다른 데이터 파일 사용

python3 fetch_images.py             # 사진 전체 재수집
python3 fetch_images.py sagrada-familia park-guell   # 일부만 재수집
```
사진을 추가하려면 `fetch_images.py`의 `SIGHTS`/`DISHES`에 `슬러그: (위키 언어, 정확한 문서 제목)`을 넣거나 `("commons", "File:....jpg")`로 커먼즈 파일을 직접 지정한 뒤, `data/image_map.json`에서 명소/맛집과 연결합니다.

## 주의
- 2027년 항공·열차 시간표와 입장료는 미공개 상태라 2025~2026년 운영 패턴을 기준으로 작성했습니다. 출발 2~3개월 전 공식 사이트에서 재확인하세요.
- 구글 평점은 조사 시점(2026-08) 기준입니다.
- 명소 사진은 위키미디어 커먼즈에서 가져왔고, 음식 사진은 **해당 요리의 일반 사진**입니다(그 식당에서 촬영한 사진이 아닙니다). 저작자·라이선스는 페이지 하단 '사진 출처'에 표기됩니다.
- 숙소는 계획 확정 후 별도로 예약 (추천 동네는 안전 가이드 참고).

지도 데이터 © OpenStreetMap contributors.
