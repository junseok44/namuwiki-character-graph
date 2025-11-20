"""이미지 추출 모듈"""
import re
from typing import Optional, List, Dict


def extract_image_src(text: str) -> Optional[str]:
    """나무위키 문서에서 첫 번째 이미지 파일의 src 추출"""
    file_pattern = r'\[\[파일:([^\|\]]+)(?:\|[^\]]+)?\]\]'
    matches = re.findall(file_pattern, text)
    if matches:
        return matches[0].strip()
    return None


def extract_all_image_urls(text: str) -> List[Dict[str, str]]:
    """
    나무위키 문서 텍스트에서 모든 이미지 URL 추출
    
    Args:
        text: 나무위키 문서 텍스트
    
    Returns:
        이미지 URL 리스트 (각각 {'url': URL, 'alt': alt_text} 형태)
    """
    image_urls = []
    
    # 1. 실제 이미지 URL 패턴 찾기 (나무위키 이미지 서버)
    url_patterns = [
        r'https://i\.namu\.wiki/i/[^\s\)\]\>\"\'\n\r\t]+',
        r'https://w\.namu\.la/[^\s\)\]\>\"\'\n\r\t]+',
        r'https://[^/]*namu[^/]*/[^\s\)\]\>\"\'\n\r\t]+',
    ]
    
    for pattern in url_patterns:
        matches = re.findall(pattern, text)
        for url in matches:
            # 일반적인 이미지 확장자 확인
            if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                image_urls.append({'url': url.strip(), 'alt': ''})
            # 또는 webp 같은 확장자가 URL 중간에 있을 수도 있음
            elif '.webp' in url.lower() or '/i/' in url:
                image_urls.append({'url': url.strip(), 'alt': ''})
    
    # 2. 파일 링크 형식 찾기 ([[파일:...]])
    file_pattern = r'\[\[파일:([^\|\]]+)(?:\|[^\]]+)?\]\]'
    matches = re.findall(file_pattern, text)
    for match in matches:
        filename = match.strip()
        # 파일명을 URL로 변환하지 않고 그대로 저장 (AI가 참고용으로 사용)
        image_urls.append({'url': f'파일:{filename}', 'alt': filename})
    
    return image_urls

