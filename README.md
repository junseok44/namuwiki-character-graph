# 등장인물 관계 그래프 제작 서비스

나무위키의 방대한 데이터를 활용하여 복잡한 작품 속 등장인물들의 관계를 자동으로 분석하고 시각화하는 프로젝트입니다.

## 1. 프로젝트 개요 및 제작 의도

> "복잡하게 얽힌 스토리 속에서 '누가 누구와 어떤 관계인지'를 한눈에 파악하는 것은 콘텐츠 감상의 핵심 재미 요소입니다."

많은 팬들이 작품 이해를 위해 직접 관계도를 그리거나 공유하지만, 텍스트로 흩어진 정보를 수집하고 도식화하는 과정은 높은 진입장벽을 가집니다. 본 프로젝트는 나무위키에 축적된 풍부한 데이터를 활용해 이 과정을 자동화함으로써, 사용자가 콘텐츠의 본질적인 재미에 집중할 수 있도록 돕습니다.

배포 URL: https://namuwiki-graph-server-13726561528.asia-northeast3.run.app/
(과제전 이후 호스팅 종료 예정입니다.)

## 2. 시스템 아키텍처 및 기술 스택

### 기술 스택
* **Web Server**: Flask (Python)
* **LLM**: OpenAI API (GPT-4o-mini, GPT-5)
* **Data Source**:
    * HuggingFace `heegyu/namuwiki` (2022년 덤프 데이터)
    * 실시간 나무위키 웹 크롤링
* **Frontend**: HTML5, CSS3, Vanilla JS, D3.js (시각화)
* **Infrastructure**: Docker, Cloud Run (Hosting)

## 3. 핵심 알고리즘 Flow (구현 방법)

사용자가 키워드(작품명)를 입력하면 총 5단계의 파이프라인을 거쳐 그래프를 생성합니다.

### Step 1. 데이터 전처리 및 인덱싱 (Data Preprocessing)
서버 구동 시 `modules/namuwiki_dataset.py`가 실행되며 고속 검색 환경을 구축합니다.
* **데이터 로드**: HuggingFace에서 약 82만 개의 나무위키 문서를 로드합니다.
* **인덱스 생성**: 모든 문서 제목에 대해 공백·특수문자를 제거하고 소문자로 변환(`normalize_title`)하여 인덱싱합니다.
    * **Title Map**: `defaultdict(list)`를 사용해 O(1) 시간 복잡도로 정확한 문서를 찾을 수 있는 해시 맵을 구축합니다.
    * **Title List**: 유사도 검색을 위한 제목 리스트를 메모리에 캐싱합니다.
* **최적화**: 최초 실행 시 생성된 인덱스는 `pickle` 파일로 저장되어, 재실행 시 로딩 시간을 단축합니다.

### Step 2. 키워드 기반 문서 검색 (Document Search)
사용자가 입력한 키워드를 바탕으로 `find_most_similar_document` 함수가 두 가지 핵심 문서를 찾습니다.
* **메인 문서**: 키워드와 정확히 일치하거나 가장 유사한 문서 (예: "나루토")
* **등장인물 목록 문서**: 키워드 뒤에 `/등장인물` 접미사가 붙은 문서 (예: "나루토/등장인물")

### Step 3. 인물 목록 추출 (Character Extraction)
`extract_character_names_with_ai` 모듈이 수행됩니다.
* **Input**: Step 2에서 찾은 '메인 문서'와 '등장인물 목록 문서'의 본문 텍스트.
* **Processing**: LLM(GPT-4o-mini)에게 두 텍스트를 제공하여, 지역/기술명 등을 제외한 **순수 등장인물 이름(최대 20명)**만 JSON 리스트로 추출하도록 요청합니다.

### Step 4. 인물 문서 데이터 수집 (Data Collection: Hybrid Approach)
추출된 인물 리스트를 바탕으로 상세 정보를 수집합니다. 정확도와 속도를 위해 하이브리드 방식을 사용합니다.
* **Web Crawling (우선)**: 최신 정보를 얻기 위해 `fetch_namuwiki_page` 함수가 나무위키 웹페이지를 실시간으로 크롤링합니다. 이때 각 문서 내의 이미지 URL(`extract_all_image_urls`)을 함께 수집하여 시각화에 활용합니다.
* **Dataset Fallback (보완)**: 크롤링이 실패하거나 차단될 경우, 로컬에 로드된 덤프 데이터셋에서 해당 인물 문서를 검색(`find_document_by_exact_title_indexed`)하여 내용을 가져옵니다.


### Step 5. 관계 그래프 생성 (Graph Generation)
수집된 모든 데이터(메인 문서 + 등장인물 문서들)를 통합하여 `extract_character_relationships_with_ai` 함수가 최종 그래프를 생성합니다.
* **Prompting**: 수집된 텍스트와 이미지 URL을 LLM(GPT-4o-mini 또는 GPT-5)에 한 번에 입력합니다.
* **Structuring**: LLM은 텍스트를 분석하여 다음 정보를 포함한 JSON을 생성합니다.
    * **Nodes (인물)**: 이름, 대표 이미지, 인물 속성 요약.
    * **Edges (간선)**: 인물 간의 관계 (예: "적대적 관계", "짝사랑" 등 구체적 서술).
* **Visualization**: 프론트엔드에서 D3.js를 사용해 노드-링크 다이어그램으로 시각화합니다.

## 4. 모델별 성능 비교 (Performance)

사용자는 속도와 정확도 사이에서 모델을 선택할 수 있습니다.

| 모델 | 노드/간선 복잡도 | 소요 시간 | 특징 |
| :--- | :--- | :--- | :--- |
| **GPT-4o-mini** | 노드 20개, 간선 약 15개 | 약 30초 | 빠르고 비용 효율적, 핵심 관계 위주 파악 |
| **Gemini-Pro** | 노드 20개, 간선 약 20~36개 | 약 60~80초 | 균형 잡힌 성능 |
| **GPT-5** | 노드 20개, 간선 약 68개 | 약 3분 | 매우 상세하고 복잡한 관계까지 심층 분석 |

## 5. 설치 및 실행 방법

### 5-1. 필수 요구 사항
* Python 3.8+
* OpenAI API Key (환경 변수 설정 필요)

루트 디렉토리에 .env 파일을 생성하고 OpenAI API Key를 설정해주세요
```
OPENAI_API_KEY=
```

### 5-2. 가상환경 생성 및 라이브러리 설치

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 5-3. 서버 실행

```bash
(venv) python3 app.py
```

> **주의:** 최초 실행 시 약 3GB의 데이터셋 다운로드 및 인덱싱 과정으로 인해 부팅에 수 분이 소요될 수 있습니다. 이후 실행부터는 캐시(`title_index_cache.pkl`)를 사용하여 빠르게 시작됩니다.

### 5-4. 접속
브라우저에서 `http://127.0.0.1:5000` 으로 접속합니다.

## 6. 데이터셋 관리 및 용량
이 프로젝트는 Hugging Face의 `heegyu/namuwiki` 데이터셋을 로컬(`./data`)에 캐싱하여 사용합니다.

* **디스크 공간**: 원활한 구동을 위해 최소 **10~11GB**의 여유 공간(다운로드 캐시 + 압축 해제된 Arrow 데이터 + 인덱스 파일)을 권장합니다.

## 📂 디렉토리 구조

```
.
├── app.py                      # Flask 애플리케이션 진입점
├── data/                       # 데이터셋 및 인덱스 저장소
├── modules/                    # 핵심 기능 모듈
│   ├── __init__.py
│   ├── ai_service.py           # AI API 연동 서비스
│   ├── character_extractor.py  # 등장인물 추출 로직
│   ├── document_search.py      # 문서 검색 알고리즘
│   ├── graph_generator.py      # 관계 그래프 데이터 생성
│   ├── graph_visualizer.py     # 시각화 데이터 처리
│   ├── image_extractor.py      # 이미지 URL 추출
│   ├── namuwiki_dataset.py     # 데이터셋 로드 및 인덱싱
│   └── namuwiki_web.py         # 나무위키 웹 크롤링
├── static/                     # 정적 파일 (Frontend)
│   ├── app.js
│   └── style.css
└── templates/                  # HTML 템플릿
    └── index.html
```

---

### 제작자
장준석 (정문 21)