"""AI 서비스 모듈"""
import os
import time
from typing import List, Dict, Optional, Any
import openai
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# AI 요청 시간 추적을 위한 전역 변수
_ai_request_times = []


def get_ai_request_stats() -> Dict[str, Any]:
    """
    AI 요청 통계 반환
    
    Returns:
        통계 딕셔너리 (총 요청 수, 총 시간, 평균 시간, 최소/최대 시간 등)
    """
    if not _ai_request_times:
        return {
            'total_requests': 0,
            'total_time': 0.0,
            'average_time': 0.0,
            'min_time': 0.0,
            'max_time': 0.0,
            'requests': []
        }
    
    total_time = sum(_ai_request_times)
    return {
        'total_requests': len(_ai_request_times),
        'total_time': total_time,
        'average_time': total_time / len(_ai_request_times),
        'min_time': min(_ai_request_times),
        'max_time': max(_ai_request_times),
        'requests': _ai_request_times.copy()
    }


def reset_ai_request_stats():
    """AI 요청 통계 초기화"""
    global _ai_request_times
    _ai_request_times = []


def print_ai_request_stats():
    """AI 요청 통계 출력"""
    stats = get_ai_request_stats()
    if stats['total_requests'] == 0:
        print("\n📊 AI 요청 통계: 요청이 없습니다.")
        return
    
    print("\n" + "="*50)
    print("📊 AI 요청 시간 통계")
    print("="*50)
    print(f"총 요청 수: {stats['total_requests']}회")
    print(f"총 소요 시간: {stats['total_time']:.2f}초")
    print(f"평균 소요 시간: {stats['average_time']:.2f}초")
    print(f"최소 소요 시간: {stats['min_time']:.2f}초")
    print(f"최대 소요 시간: {stats['max_time']:.2f}초")
    
    # 각 요청별 시간 출력
    if len(stats['requests']) <= 10:
        print("\n각 요청별 소요 시간:")
        for i, req_time in enumerate(stats['requests'], 1):
            print(f"  요청 {i}: {req_time:.2f}초")
    else:
        print(f"\n각 요청별 소요 시간 (최근 10개):")
        for i, req_time in enumerate(stats['requests'][-10:], len(stats['requests'])-9):
            print(f"  요청 {i}: {req_time:.2f}초")
    
    print("="*50)


def call_ai_api(messages: List[Dict[str, str]], model: str = "gpt-5-mini", temperature: Optional[float] = None) -> str:
    """
    OpenAI API 호출
    
    Args:
        messages: 메시지 리스트 (role, content)
        model: 사용할 모델 (기본: gpt-4o-mini)
        temperature: 온도 설정 (None이면 API 호출에 포함하지 않음)
    
    Returns:
        AI 응답 텍스트
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일에 설정하거나 환경변수로 설정해주세요.")
    
    # httpx 0.28.1에서는 proxies 파라미터가 제거되었으므로 http_client를 직접 생성
    import httpx
    http_client = httpx.Client()
    client = openai.OpenAI(api_key=api_key, http_client=http_client)
    
    # 시간 측정 시작
    start_time = time.time()
    
    try:
        # temperature가 None이 아니면 포함, None이면 제외
        params = {
            "model": model,
            "messages": messages
        }
        if temperature is not None:
            params["temperature"] = temperature
        
        response = client.chat.completions.create(**params)
        elapsed_time = time.time() - start_time
        
        # 시간 기록
        _ai_request_times.append(elapsed_time)
        
        # 요청 정보 출력
        user_message_preview = messages[-1].get('content', '')[:50] if messages else ''
        print(f"  ⏱️  AI 요청 완료: {elapsed_time:.2f}초 (모델: {model})")
        
        return response.choices[0].message.content
    except Exception as e:
        # 시간 측정 종료 (에러 발생 시에도)
        elapsed_time = time.time() - start_time
        
        # temperature 관련 에러인 경우 temperature 없이 조용히 재시도
        error_str = str(e)
        if "temperature" in error_str.lower() and temperature is not None:
            try:
                # 재시도 시간 측정 시작
                retry_start_time = time.time()
                response = client.chat.completions.create(
                    model=model,
                    messages=messages
                )
                retry_elapsed_time = time.time() - retry_start_time
                
                # 재시도 시간 기록
                _ai_request_times.append(retry_elapsed_time)
                print(f"  ⏱️  AI 요청 완료 (재시도): {retry_elapsed_time:.2f}초 (모델: {model})")
                
                return response.choices[0].message.content
            except Exception as retry_error:
                print(f"❌ AI API 호출 실패: {retry_error}")
                raise
        else:
            print(f"❌ AI API 호출 실패: {e} (소요 시간: {elapsed_time:.2f}초)")
            raise

