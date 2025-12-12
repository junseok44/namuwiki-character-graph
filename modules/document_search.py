"""문서 검색 모듈"""
from typing import Optional, Tuple, List
from difflib import SequenceMatcher
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


def is_redirect_or_disambiguation(doc_text: str) -> bool:
    """
    리다이렉트나 동음이의어 문서인지 확인
    
    Args:
        doc_text: 문서 텍스트
    
    Returns:
        리다이렉트나 동음이의어 문서면 True
    """
    if not doc_text:
        return True
    
    normalized_text = doc_text.strip()
    
    # 리다이렉트 감지
    if normalized_text.startswith('#redirect') or normalized_text.startswith('#REDIRECT'):
        return True
    
    # 동음이의어 감지
    if '동음이의어' in doc_text or '동음이의' in doc_text:
        # 텍스트가 짧고 여러 항목만 나열하는 경우
        if len(doc_text) < 500 and ('==' in doc_text or '[include' in doc_text):
            return True
    
    # 텍스트가 너무 짧은 경우 (리다이렉트 가능성)
    if len(doc_text) < 100:
        return True
    
    return False


def calculate_title_similarity(keyword: str, title: str) -> float:
    """
    제목 검색에 최적화된 유사도 계산
    
    Args:
        keyword: 검색 키워드
        title: 비교할 제목
    
    Returns:
        유사도 (0.0 ~ 1.0)
    """
    normalized_keyword = normalize_title(keyword)
    normalized_title = normalize_title(title)
    
    # 정확한 매칭
    if normalized_keyword == normalized_title:
        return 1.0
    
    # keyword가 title에 포함되어 있는지
    if normalized_keyword in normalized_title:
        # 시작 부분에 있으면 가중치
        if normalized_title.startswith(normalized_keyword):
            base_similarity = SequenceMatcher(None, normalized_keyword, normalized_title).ratio()
            return min(1.0, base_similarity * 1.2)  # 20% 가중치
        else:
            return SequenceMatcher(None, normalized_keyword, normalized_title).ratio()
    
    # 포함되지 않으면 일반 유사도
    return SequenceMatcher(None, normalized_keyword, normalized_title).ratio()


def find_all_candidates_by_keyword(
    title_list: List[tuple], 
    keyword: str, 
    suffix: str = None,
    verbose: bool = True
) -> List[Tuple[int, str, str, float]]:
    """
    keyword가 포함된 모든 후보 문서 수집 (유사도 포함)
    
    Args:
        title_list: (idx, original_title, normalized_title) 리스트
        keyword: 검색할 키워드
        suffix: 제목 끝에 있어야 할 접미사 (예: "/등장인물")
        verbose: 로그 출력 여부
    
    Returns:
        [(idx, original_title, normalized_title, similarity), ...] 리스트
        유사도 순으로 정렬되지 않음 (나중에 정렬)
    """
    normalized_keyword = normalize_title(keyword)
    normalized_suffix = normalize_title(suffix) if suffix else None
    
    candidates = []
    
    for idx, original_title, normalized_title in title_list:
        # keyword가 포함되어 있는지 확인
        if normalized_keyword in normalized_title:
            # suffix가 지정되어 있으면 suffix로 끝나는지 확인
            if normalized_suffix:
                if not normalized_title.endswith(normalized_suffix):
                    continue
            
            # 유사도 계산
            similarity = calculate_title_similarity(keyword, normalized_title)
            candidates.append((idx, original_title, normalized_title, similarity))
    
    return candidates


def find_most_similar_document(
    title_list: List[tuple],
    title_to_indices: dict,
    data,
    keyword: str,
    suffix: str = None,
    verbose: bool = True
) -> Tuple[Optional[int], Optional[dict], Optional[str], float]:
    """
    keyword와 가장 유사한 문서 찾기
    
    Args:
        title_list: (idx, original_title, normalized_title) 리스트
        title_to_indices: 정규화된 제목 -> 인덱스 리스트 딕셔너리
        data: 데이터셋 데이터
        keyword: 검색할 키워드
        suffix: 제목 끝에 있어야 할 접미사 (예: "/등장인물")
        verbose: 로그 출력 여부
    
    Returns:
        (인덱스, 문서, 매칭된_제목, 유사도) 튜플 또는 (None, None, None, 0.0)
    """
    normalized_keyword = normalize_title(keyword)
    
    # 1. 정확한 매칭 먼저 확인 (내용 검증 포함)
    if suffix is None:
        if normalized_keyword in title_to_indices:
            idx = title_to_indices[normalized_keyword][0]
            doc = data[idx]
            doc_text = doc.get('text', '')
            
            # 리다이렉트나 동음이의어 문서인지 확인
            if is_redirect_or_disambiguation(doc_text):
                # 후보 검색으로 넘어감
                pass
            else:
                return idx, doc, normalized_keyword, 1.0
    else:
        normalized_suffix = normalize_title(suffix)
        exact_title = normalized_keyword + normalized_suffix
        if exact_title in title_to_indices:
            idx = title_to_indices[exact_title][0]
            doc = data[idx]
            doc_text = doc.get('text', '')
            
            # 리다이렉트나 동음이의어 문서인지 확인
            if is_redirect_or_disambiguation(doc_text):
                # 후보 검색으로 넘어감
                pass
            else:
                return idx, doc, exact_title, 1.0
    
    # 2. 모든 후보 수집
    candidates = find_all_candidates_by_keyword(title_list, keyword, suffix, verbose=False)
    
    if not candidates:
        return None, None, None, 0.0
    
    # 3. 후보들을 평가하여 최선의 문서 선택
    # - 리다이렉트/동음이의어 문서는 점수 감점
    # - 텍스트 길이도 고려
    scored_candidates = []
    for idx, original_title, normalized_title, similarity in candidates:
        doc = data[idx]
        doc_text = doc.get('text', '')
        
        # 리다이렉트/동음이의어 문서인지 확인
        is_redirect = is_redirect_or_disambiguation(doc_text)
        
        # 점수 계산: 유사도 + 내용 품질 보너스
        score = similarity
        
        if not is_redirect:
            # 실제 내용이 있는 문서는 보너스
            # 텍스트 길이에 따라 보너스 (최대 0.1)
            text_length_bonus = min(0.1, len(doc_text) / 10000.0)
            score += text_length_bonus
        else:
            # 리다이렉트/동음이의어 문서는 감점
            score -= 0.2
        
        scored_candidates.append((idx, original_title, normalized_title, similarity, score, is_redirect, len(doc_text)))
    
    # 점수 순으로 정렬
    scored_candidates.sort(key=lambda x: x[4], reverse=True)  # score 내림차순
    
    best_idx, best_original_title, best_normalized_title, best_similarity, best_score, is_redirect, text_len = scored_candidates[0]
    
    return best_idx, data[best_idx], best_normalized_title, best_similarity

