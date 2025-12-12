"""인물 추출 모듈"""
import json
import re
import time
from typing import List
from .ai_service import call_ai_api


def extract_character_names_with_ai(keyword: str, main_doc_text: str, character_list_doc_text: str, max_characters: int = 20) -> List[str]:
    """
    AI를 사용하여 두 문서에서 keyword에 속할만한 인물 이름 추출
    
    Args:
        keyword: 검색 키워드
        main_doc_text: 메인 문서 텍스트
        character_list_doc_text: 등장인물 목록 문서 텍스트
        max_characters: 최대 추출할 인물 수 (기본값: 20)
    
    Returns:
        인물 이름 리스트 (최대 max_characters개)
    """
    print("\n🤖 AI에게 인물 추출 요청 중...")
    start_time = time.time()
    
    prompt = f"""다음은 "{keyword}"에 대한 나무위키 문서 두 개입니다.

[메인 문서]
{main_doc_text[:8000]}

[등장인물 목록 문서]
{character_list_doc_text[:8000]}

위 두 문서에서 "{keyword}"에 정확히 속하는 등장인물의 이름만 추출해주세요.
- 지역명, 기관명, 팀명 등은 제외하고 실제 인물 이름만 추출
- 문서에 링크로 등장하는 인물명을 우선적으로 추출
- 최대 {max_characters}명까지만 추출해주세요
- JSON 배열 형태로만 응답해주세요 (예: ["인물1", "인물2", "인물3"])
- 설명이나 다른 텍스트는 포함하지 마세요."""

    messages = [
        {"role": "system", "content": "당신은 나무위키 문서에서 등장인물 이름을 정확히 추출하는 전문가입니다. JSON 배열 형태로만 응답합니다."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = call_ai_api(messages)
        # JSON 배열 파싱
        response = response.strip()
        
        # 마크다운 코드 블록 제거
        if response.startswith("```json"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
        elif response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
        
        # JSON 배열 찾기 (대괄호로 시작하는 부분)
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        if json_start != -1 and json_end > json_start:
            response = response[json_start:json_end]
        
        # JSON 파싱
        character_names = json.loads(response)
        if isinstance(character_names, list):
            # 최대 인물 수로 제한
            if len(character_names) > max_characters:
                character_names = character_names[:max_characters]
                print(f"⚠️  추출된 인물이 {max_characters}명을 초과하여 {max_characters}명으로 제한했습니다.")
            elapsed_time = time.time() - start_time
            print(f"✅ AI가 {len(character_names)}명의 인물을 추출했습니다. (전체 소요 시간: {elapsed_time:.2f}초)")
            return character_names
        else:
            print(f"⚠️  AI 응답이 리스트가 아닙니다.")
            return []
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON 파싱 실패: {e}")
        print(f"응답 내용: {response[:500]}")
        # 응답에서 따옴표로 감싸진 이름들 추출 시도
        names = re.findall(r'["\']([^"\']+)["\']', response)
        if names:
            print(f"대체 방법으로 {len(names)}개의 이름을 추출했습니다.")
            return names
        return []
    except Exception as e:
        print(f"❌ 인물 추출 실패: {e}")
        return []

