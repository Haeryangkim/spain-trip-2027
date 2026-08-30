"""스페인 여행 계획 2027 — Streamlit Community Cloud 공유용 래퍼.

빌드된 단일 파일 웹사이트(index.html)를 static/ 으로 복사해 그대로 서빙하고,
전체 화면 링크와 일자 바로가기를 제공한다.
빌드: python3 build.py  (index.html 생성)
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
SRC = ROOT / "index.html"
STATIC_DIR = ROOT / "static"
STATIC_PAGE = STATIC_DIR / "index.html"
STATIC_URL = "app/static/index.html"          # Streamlit 정적 서빙 경로
REPO_URL = "https://github.com/Haeryangkim/spain-trip-2027"

st.set_page_config(
    page_title="스페인 여행 계획 2027",
    page_icon="🇪🇸",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource(show_spinner=False)
def publish_static() -> bool:
    """index.html 을 static/ 으로 복사해 브라우저가 직접 받아가게 한다."""
    if not SRC.exists():
        return False
    STATIC_DIR.mkdir(exist_ok=True)
    if (not STATIC_PAGE.exists()) or STATIC_PAGE.stat().st_mtime < SRC.stat().st_mtime:
        shutil.copy2(SRC, STATIC_PAGE)
    return True


@st.cache_data(show_spinner=False)
def load_days() -> list[dict]:
    path = ROOT / "data" / "itinerary.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "no": d["day_no"],
            "date": d["date"],
            "weekday": d.get("weekday_ko", ""),
            "title": d.get("title", ""),
        }
        for d in data.get("days", [])
    ]


if not publish_static():
    st.error(
        "index.html 을 찾지 못했습니다. 레포 루트에서 `python3 build.py` 를 실행해 "
        "페이지를 빌드한 뒤 다시 배포하세요."
    )
    st.stop()

days = load_days()

# --- 상단 바: 전체 화면 링크 + 일자 바로가기 -------------------------------
st.markdown(
    """
    <style>
      header[data-testid="stHeader"] {height: 0; visibility: hidden;}
      .block-container {padding: 0.6rem 1rem 0 1rem !important; max-width: 100% !important;}
      .stApp {background: #f4f3ee;}
      div[data-testid="stElementContainer"]:has(iframe) {line-height: 0;}
      iframe {border: 1px solid #d9d8cf !important; background: #fff;}
      .topbar {display:flex; flex-wrap:wrap; align-items:center; gap:10px; margin-bottom:8px;
               font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;}
      .topbar .ttl {font-weight:800; font-size:17px; color:#101828; margin-right:auto;}
      .topbar .ttl span {color:#c2410c;}
      .topbar a {display:inline-block; text-decoration:none; font-size:13px; font-weight:600;
                 padding:6px 13px; border:1px solid #d9d8cf; border-radius:999px; color:#1b2a4a; background:#fff;}
      .topbar a.pri {background:#1b2a4a; border-color:#1b2a4a; color:#fff;}
      .topbar a:hover {border-color:#d99a1e;}
      @media (prefers-color-scheme: dark) {
        .stApp {background:#0f1419;} .topbar .ttl {color:#e9eae4;}
        .topbar a {background:#171d26; border-color:#2a3340; color:#e9eae4;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)

day_labels = ["전체 보기"] + [
    f"Day {d['no']:02d} · {d['date'][5:].replace('-', '/')} {d['weekday']} · {d['title']}" for d in days
]
col_head, col_jump = st.columns([3, 2], vertical_alignment="center")
with col_head:
    st.markdown(
        f"""<div class="topbar">
              <div class="ttl">스페인 여행 계획 <span>2027</span> · 마드리드 → 마요르카 → 바르셀로나</div>
              <a class="pri" href="{STATIC_URL}" target="_blank" rel="noopener">전체 화면으로 열기 ↗</a>
              <a href="{REPO_URL}" target="_blank" rel="noopener">GitHub</a>
            </div>""",
        unsafe_allow_html=True,
    )
with col_jump:
    choice = st.selectbox(
        "일자 바로가기", day_labels, label_visibility="collapsed",
        help="선택한 날짜의 타임라인 위치로 페이지를 엽니다.",
    )

anchor = ""
if choice != "전체 보기":
    anchor = f"#day-{days[day_labels.index(choice) - 1]['no']}"

# components.v1.iframe 만 상대 URL 을 iframe src 로 넣어준다.
# (st.iframe 은 URL 이 아닌 문자열을 srcdoc(HTML)으로 취급해 페이지가 열리지 않음)
_legacy_iframe = getattr(getattr(st, "components", None), "v1", None)
if _legacy_iframe is not None and hasattr(_legacy_iframe, "iframe"):
    _legacy_iframe.iframe(STATIC_URL + anchor, height=880, scrolling=True)
else:  # 향후 API 가 제거된 경우: 링크만 제공
    st.warning("이 Streamlit 버전에서는 페이지를 embed 할 수 없습니다. 아래 링크로 열어주세요.")
    st.markdown(
        f'<a class="pri" href="{STATIC_URL + anchor}" target="_blank" rel="noopener">여행 계획 페이지 열기 ↗</a>',
        unsafe_allow_html=True,
    )

st.caption(
    "브라우저 창이 좁으면 위 ‘전체 화면으로 열기’ 를 눌러 원본 페이지에서 보세요. "
    "2027년 항공·열차 시간표와 입장료는 미공개 상태라 2025~2026년 운영 패턴 기준으로 작성했습니다."
)
