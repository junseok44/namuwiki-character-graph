"""나무위키 웹 크롤링 모듈"""
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import time


def build_namuwiki_url(title: str) -> str:
    """
    나무위키 문서 URL 생성
    
    Args:
        title: 문서 제목 (예: "산(모노노케 히메)")
    
    Returns:
        나무위키 URL (예: "https://namu.wiki/w/%EC%82%B0(%EB%AA%A8%EB%85%B8%EB%85%B8%EC%BC%80%20%ED%9E%88%EB%A9%94)")
    """
    # URL 인코딩
    encoded_title = urllib.parse.quote(title, safe='')
    return f"https://namu.wiki/w/{encoded_title}"


def fetch_namuwiki_page(title: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    나무위키 페이지를 가져와서 파싱
    
    Args:
        title: 문서 제목
        timeout: 요청 타임아웃 (초)
    
    Returns:
        {'title': 제목, 'text': 텍스트 내용, 'image_src': 이미지 URL} 또는 None
    """
    url = build_namuwiki_url(title)
    
    try:
        # User-Agent 설정 (봇 차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"    🌐 웹에서 가져오는 중: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # HTML 파싱
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 제목 추출 (h1 태그에서 찾기, 클래스명이 해시되어 있으므로 태그만으로 찾기)
        title_elem = soup.find('h1')
        if title_elem:
            page_title = title_elem.get_text(strip=True)
        else:
            page_title = title
        
        # 본문 텍스트 추출 (id="app" div에서 찾기)
        content_elem = soup.find(id='app')
        if not content_elem:
            print(f"    ⚠️  본문을 찾을 수 없습니다.")
            return None
        
        # 스크립트와 스타일 제거
        for script in content_elem(["script", "style"]):
            script.decompose()
        
        # 텍스트 내용 추출
        text_content = content_elem.get_text(separator='\n', strip=True)
        
        # 이미지 URL 추출 (별도로 저장)
        image_urls = []
        img_tags = content_elem.find_all('img')
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if src:
                # 나무위키 이미지 서버 URL인지 확인
                if 'namu.wiki' in src or 'namu.la' in src or 'i.namu.wiki' in src:
                    # 상대 경로인 경우 절대 경로로 변환
                    if src.startswith('//'):
                        full_url = 'https:' + src
                    elif src.startswith('/'):
                        full_url = 'https://namu.wiki' + src
                    elif src.startswith('http://') or src.startswith('https://'):
                        full_url = src
                    else:
                        full_url = 'https://namu.wiki' + src
                    
                    # 로고나 아이콘 제외
                    if not any(exclude in full_url.lower() for exclude in ['logo', 'icon', 'button', 'spacer']):
                        alt_text = img.get('alt', '')
                        # img 태그 주변 텍스트 추출 (위치 정보)
                        parent = img.find_parent()
                        context_text = ""
                        if parent:
                            # 부모 요소의 텍스트 일부 추출
                            parent_text = parent.get_text(separator=' ', strip=True)
                            context_text = parent_text[:200]  # 최대 200자
                        
                        image_urls.append({
                            'url': full_url,
                            'alt': alt_text,
                            'context': context_text
                        })
        
        return {
            'title': page_title,
            'text': text_content,  # 텍스트만
            'image_urls': image_urls,  # 이미지 URL 리스트 별도 저장
            'image_src': image_urls[0]['url'] if image_urls else None,  # 하위 호환성
            'url': url
        }
        
    except requests.exceptions.RequestException as e:
        print(f"    ❌ 웹 요청 실패: {e}")
        return None
    except Exception as e:
        print(f"    ❌ 파싱 실패: {e}")
        return None


def fetch_character_documents(character_names: list, delay: float = 0.5) -> list:
    """
    여러 인물의 나무위키 문서를 웹에서 가져오기
    
    Args:
        character_names: 인물 이름 리스트
        delay: 요청 간 지연 시간 (초, 서버 부하 방지)
    
    Returns:
        문서 리스트 (각각 title, text, image_src 포함)
    """
    documents = []
    
    for i, character_name in enumerate(character_names, 1):
        print(f"  [{i}/{len(character_names)}] '{character_name}' 웹에서 가져오는 중...")
        
        doc = fetch_namuwiki_page(character_name)
        if doc:
            doc['type'] = 'character'
            documents.append(doc)
            print(f"    ✅ 문서 가져옴: '{doc['title']}'")
            if doc.get('image_src'):
                print(f"    📷 이미지: {doc['image_src'][:80]}...")
        else:
            print(f"    ⚠️  문서를 가져올 수 없습니다.")
        
        # 서버 부하 방지를 위한 지연
        if i < len(character_names):
            time.sleep(delay)
    
    return documents


def fetch_and_merge_character_documents(
    character_names: list,
    title_to_indices: dict,
    data,
    delay: float = 0.5
) -> list:
    """
    여러 인물의 나무위키 문서를 웹에서 우선 가져오고, 실패하면 데이터셋에서 가져오기
    
    Args:
        character_names: 인물 이름 리스트
        title_to_indices: 제목 인덱스 딕셔너리
        data: 데이터셋 데이터
        delay: 웹 요청 간 지연 시간 (초, 서버 부하 방지)
    
    Returns:
        문서 리스트 (각각 title, text, image_urls 포함)
        - 웹에서 성공하면 웹 문서만 사용
        - 웹에서 실패하면 데이터셋 문서 사용
        - 둘 다 실패하면 해당 인물은 제외
    """
    from .document_search import search_document_by_title_indexed
    from .image_extractor import extract_all_image_urls
    
    documents = []
    
    for i, character_name in enumerate(character_names, 1):
        print(f"  [{i}/{len(character_names)}] '{character_name}' 문서 수집 중...")
        
        # 1. 데이터셋에서 검색
        dataset_doc_idx, dataset_doc = search_document_by_title_indexed(
            title_to_indices, data, character_name
        )
        
        dataset_text = ""
        dataset_image_urls = []
        if dataset_doc:
            dataset_text = dataset_doc.get('text', '')
            dataset_image_urls = extract_all_image_urls(dataset_text)
            print(f"    📚 데이터셋에서 찾음: '{dataset_doc.get('title', '')}' ({len(dataset_text)}자, 이미지 {len(dataset_image_urls)}개)")
        else:
            print(f"    ⚠️  데이터셋에서 찾을 수 없음")
        
        # 2. 웹에서 가져오기 (우선 시도)
        web_doc = fetch_namuwiki_page(character_name)
        
        # 3. 웹에서 성공하면 웹 문서 사용, 실패하면 데이터셋 사용
        final_doc = None
        if web_doc:
            # 웹에서 성공한 경우
            web_text = web_doc.get('text', '')
            web_image_urls = web_doc.get('image_urls', [])
            web_title = web_doc.get('title', character_name)
            
            final_doc = {
                'title': web_title,
                'text': web_text,
                'image_urls': web_image_urls,
                'type': 'character',
                'source': 'web'
            }
            print(f"    ✅ 웹 문서 사용: '{web_title}' ({len(web_text)}자, 이미지 {len(web_image_urls)}개)")
        elif dataset_doc:
            # 웹에서 실패하고 데이터셋에 있는 경우
            dataset_title = dataset_doc.get('title', character_name)
            final_doc = {
                'title': dataset_title,
                'text': dataset_text,
                'image_urls': dataset_image_urls,
                'type': 'character',
                'source': 'dataset'
            }
            print(f"    ✅ 데이터셋 문서 사용: '{dataset_title}' ({len(dataset_text)}자, 이미지 {len(dataset_image_urls)}개)")
        
        if final_doc:
            documents.append(final_doc)
        else:
            print(f"    ❌ 문서를 가져올 수 없습니다.")
        
        # 서버 부하 방지를 위한 지연
        if i < len(character_names):
            time.sleep(delay)
    
    return documents

