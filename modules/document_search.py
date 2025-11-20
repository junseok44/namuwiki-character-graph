"""문서 검색 모듈"""
from typing import Optional, Tuple, List
from .namuwiki_dataset import normalize_title


def find_document_by_exact_title_indexed(title_to_indices: dict, data, title: str) -> Tuple[Optional[int], Optional[dict]]:
    """인덱스를 사용한 정확한 제목 검색"""
    normalized_title = normalize_title(title)
    if normalized_title in title_to_indices:
        idx = title_to_indices[normalized_title][0]
        return idx, data[idx]
    return None, None


def find_document_by_keyword_included(title_list: List[tuple], data, keyword: str, suffix: str = None) -> Tuple[Optional[int], Optional[dict]]:
    """
    keyword가 포함된 문서 검색
    
    Args:
        title_list: (idx, original_title, normalized_title) 리스트
        data: 데이터셋 데이터
        keyword: 검색할 키워드
        suffix: 제목 끝에 있어야 할 접미사 (예: "/등장인물")
    
    Returns:
        (인덱스, 문서) 튜플 또는 (None, None)
    """
    normalized_keyword = normalize_title(keyword)
    normalized_suffix = normalize_title(suffix) if suffix else None
    
    # keyword가 포함되고 suffix로 끝나는 문서 찾기
    for idx, original_title, normalized_title in title_list:
        if normalized_keyword in normalized_title:
            # suffix가 지정되어 있으면 suffix로 끝나는지 확인
            if normalized_suffix:
                if normalized_title.endswith(normalized_suffix):
                    return idx, data[idx]
            else:
                # suffix가 없으면 첫 번째로 매칭되는 문서 반환
                return idx, data[idx]
    
    return None, None


def search_document_by_title_indexed(title_to_indices: dict, data, character_name: str) -> Tuple[Optional[int], Optional[dict]]:
    """인덱스를 사용한 인물명 문서 검색"""
    normalized_name = normalize_title(character_name)
    
    # 정확히 일치하는 경우
    if normalized_name in title_to_indices:
        idx = title_to_indices[normalized_name][0]
        return idx, data[idx]
    
    return None, None

