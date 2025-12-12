"""관계 그래프 생성 모듈"""
import json
import time
from typing import List, Dict, Any
from .ai_service import call_ai_api


def extract_character_relationships_with_ai(keyword: str, all_documents: List[Dict[str, Any]], model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    AI를 사용하여 모든 문서에서 인물 관계 그래프 추출
    
    Args:
        keyword: 검색 키워드
        all_documents: 모든 문서 리스트 (각각 title, text, image_src 포함)
        model: 사용할 AI 모델 (gpt-4o-mini 또는 gpt-5)
    
    Returns:
        관계 그래프 데이터 (JSON 형태)
    """
    print("\n🤖 AI에게 관계 그래프 생성 요청 중...")
    start_time = time.time()
    
    # 인물명 -> 이미지 URL 매핑 생성 (fallback용)
    character_to_image_urls = {}
    for doc in all_documents:
        title = doc.get('title', '')
        image_urls = doc.get('image_urls', [])
        if title and image_urls:
            # 제목에서 괄호나 슬래시 제거한 버전도 매핑
            clean_title = title.split('(')[0].split('/')[0].strip()
            # 실제 URL만 필터링 (파일명 형식 제외)
            real_urls = [img.get('url') if isinstance(img, dict) else img for img in image_urls if (img.get('url') if isinstance(img, dict) else img).startswith('http')]
            if real_urls:
                character_to_image_urls[clean_title] = real_urls
                character_to_image_urls[title] = real_urls
    
    # 모든 문서 텍스트와 이미지 목록 합치기 (최적화: 텍스트 길이 제한)
    combined_text = ""
    for doc in all_documents:
        title = doc.get('title', 'Unknown')
        text = doc.get('text', '')[:3000]  # 각 문서당 최대 3000자로 단축 (5000 -> 3000)
        image_urls = doc.get('image_urls', [])
        
        combined_text += f"\n\n=== {title} ===\n"
        
        # 이미지 URL 목록 추가 (AI가 인물과 관련된 이미지를 선택하도록)
        if image_urls:
            combined_text += f"\n[이 문서의 이미지 목록 - 인물 '{title}'와 관련된 이미지]\n"
            # 실제 URL만 우선 표시
            real_urls = [img for img in image_urls if (img.get('url') if isinstance(img, dict) else img).startswith('http')]
            
            for idx, img_info in enumerate(real_urls[:3], 1):  # 최대 3개로 단축 (5 -> 3)
                if isinstance(img_info, dict):
                    url = img_info.get('url', '')
                    alt = img_info.get('alt', '')
                else:
                    url = img_info
                    alt = ''
                
                img_text = f"{idx}. {url}"
                if alt:
                    img_text += f" (alt: {alt})"
                combined_text += img_text + "\n"
            
            if len(real_urls) > 3:
                combined_text += f"... 외 {len(real_urls) - 3}개 이미지 더 있음\n"
            combined_text += "\n"
        
        combined_text += text
    
    # 인물 문서 제목 추출 (AI에게 명시적으로 전달)
    character_doc_titles = []
    for doc in all_documents:
        if doc.get('type') == 'character':
            title = doc.get('title', '')
            if title:
                character_doc_titles.append(title)
    
    # 전체 텍스트가 너무 길면 잘라내기 (15000자로 단축)
    if len(combined_text) > 15000:
        combined_text = combined_text[:15000] + "\n\n... (내용이 길어 일부 생략) ..."
    
    character_list_text = ""
    if character_doc_titles:
        character_list_text = f"\n\n중요: 위 문서들 중 다음 {len(character_doc_titles)}명의 인물들의 문서가 포함되어 있습니다:\n"
        for i, title in enumerate(character_doc_titles, 1):
            character_list_text += f"{i}. {title}\n"
        character_list_text += f"\n이 {len(character_doc_titles)}명의 인물들은 반드시 그래프에 포함되어야 합니다. 또한 문서에서 언급된 다른 주요 인물들도 추가하여 최소 {len(character_doc_titles) + 5}명 이상의 인물을 포함해주세요.\n"
    
    prompt = f"""다음은 "{keyword}"에 대한 나무위키 문서들의 내용입니다.

{combined_text}{character_list_text}

위 문서들을 분석하여 등장하는 인물들의 관계를 그래프 형태로 정리해주세요.

요구사항:
1. 각 인물의 이름, 이미지 src (있으면), 기본 설명을 포함
   - 각 문서의 [이 문서의 이미지 목록] 섹션을 참고하여, 해당 인물과 가장 관련이 있는 이미지의 src를 선택해주세요
   - 주변 텍스트를 참고하여 인물과 관련된 이미지를 판단하세요
   - 인물의 얼굴이나 전체 모습을 보여주는 이미지를 우선 선택하세요
   - 로고, 아이콘, 배경 이미지 등은 제외하세요
   - 반드시 https://로 시작하는 실제 이미지 URL만 선택하세요
   - 해당 인물 문서에 이미지가 없으면 null로 설정하세요
2. 인물 간의 관계를 간선(edge)으로 표현
   - 제공된 인물 문서의 인물들 간의 관계를 우선적으로 포함하세요
   - 문서에서 언급된 다른 주요 인물들도 추가하고 관계를 설정하세요
3. 각 간선에는 관계 설명을 상세하게 포함 (최소 10자 이상, 최대 30자 정도)
   - 단순히 "친구", "적" 같은 한 단어가 아닌 구체적인 설명
   - 예: "짝사랑함" → "짝사랑하는 관계", "친구" → "절친한 친구 관계", "적" → "적대적인 관계", "형제" → "혈연 관계인 형제"
   - 가능하면 관계의 맥락이나 배경을 포함 (예: "과거 동료였던 적대 관계", "서로를 존경하는 라이벌 관계")
4. 방향성이 있는 관계는 화살표로 표현 (A -> B: A가 B에게 관계)
5. 제공된 인물 문서의 인물들을 모두 포함하고, 문서에서 언급된 다른 주요 인물들도 추가하여 최소한 제공된 인물 수보다 더 많은 인물을 포함하세요
6. JSON 형태로 응답해주세요

응답 형식:
{{
  "characters": [
    {{
      "name": "인물명",
      "image_src": "이미지경로 또는 null",
      "description": "기본 설명"
    }}
  ],
  "relationships": [
    {{
      "from": "인물A",
      "to": "인물B",
      "relation": "관계 설명"
    }}
  ]
}}

설명이나 다른 텍스트는 포함하지 말고 JSON만 응답해주세요."""

    messages = [
        {"role": "system", "content": "당신은 나무위키 문서에서 인물 관계를 분석하는 전문가입니다. JSON 형태로만 응답합니다."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = call_ai_api(messages, model=model, temperature=0.5)
        # JSON 파싱
        response = response.strip()
        
        # 마크다운 코드 블록 제거
        if response.startswith("```json"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
        elif response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
        
        # JSON 객체 찾기 (중괄호로 시작하는 부분)
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            response = response[json_start:json_end]
        
        graph_data = json.loads(response)
        
        # AI 응답 후 이미지 URL 보정 및 fallback
        fixed_count = 0
        fallback_count = 0
        for char_node in graph_data.get('characters', []):
            name = char_node.get('name', '')
            ai_selected_image = char_node.get('image_src')
            
            if name:
                # 1. AI가 선택한 이미지가 파일명 형식이면 null로 설정
                if ai_selected_image and not ai_selected_image.startswith('http'):
                    char_node['image_src'] = None
                
                # 2. AI가 null이거나 선택하지 못한 경우, 실제 문서에서 가져온 이미지 사용 (fallback)
                if not char_node.get('image_src') or char_node.get('image_src') == 'null' or char_node.get('image_src') == '':
                    if name in character_to_image_urls:
                        image_list = character_to_image_urls[name]
                        # 첫 번째 이미지 선택
                        char_node['image_src'] = image_list[0] if image_list else None
                        if image_list:
                            fallback_count += 1
                    else:
                        clean_name = name.split('(')[0].split('/')[0].strip()
                        if clean_name in character_to_image_urls:
                            image_list = character_to_image_urls[clean_name]
                            # 첫 번째 이미지 선택
                            char_node['image_src'] = image_list[0] if image_list else None
                            if image_list:
                                fallback_count += 1
                        else:
                            char_node['image_src'] = None
        
        if fallback_count > 0:
            print(f"   - 이미지 fallback: {fallback_count}개 인물에 이미지 추가")
        
        elapsed_time = time.time() - start_time
        print(f"✅ AI가 관계 그래프를 생성했습니다. (전체 소요 시간: {elapsed_time:.2f}초)")
        print(f"   - 인물 수: {len(graph_data.get('characters', []))}")
        print(f"   - 관계 수: {len(graph_data.get('relationships', []))}")
        
        # 이미지가 있는 인물 수 출력
        characters_with_image = sum(1 for char in graph_data.get('characters', []) if char.get('image_src'))
        print(f"   - 이미지 있는 인물: {characters_with_image}명")
        
        return graph_data
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON 파싱 실패: {e}")
        print(f"응답 내용: {response[:1000]}")
        raise
    except Exception as e:
        print(f"❌ 관계 그래프 생성 실패: {e}")
        raise

