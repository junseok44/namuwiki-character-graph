"""나무위키 데이터셋 로드 및 인덱스 관리 모듈"""
from datasets import load_dataset
import re
import time
import pickle
import os
from typing import List, Tuple
from collections import defaultdict

# 데이터셋 경로
DATASET_PATH = "./data"
INDEX_CACHE_FILE = "./title_index_cache.pkl"


def normalize_title(title: str) -> str:
    """
    제목 정규화: 소문자 변환 + 모든 공백 제거
    예: "유희왕 5D's" -> "유희왕5d's"
    """
    return re.sub(r'\s+', '', title.lower().strip())


def load_namuwiki_dataset(cache_dir: str = DATASET_PATH):
    """나무위키 데이터셋 로드"""
    print(f"데이터셋 로드 중: {cache_dir}")
    dataset = load_dataset(
        "heegyu/namuwiki",
        cache_dir=cache_dir
    )
    return dataset


def get_data_from_dataset(dataset):
    """데이터셋에서 실제 데이터 배열 추출"""
    if isinstance(dataset, dict):
        split = list(dataset.keys())[0]
        data = dataset[split]
        print(f"사용할 split: {split}")
    else:
        data = dataset
    return data


def build_title_index(data, cache_file: str = INDEX_CACHE_FILE, force_rebuild: bool = False) -> Tuple[dict, List[tuple]]:
    """
    전체 데이터셋을 한 번 순회하여 제목 인덱스 생성
    캐시 파일이 있으면 로드, 없으면 생성 후 저장
    """
    # 캐시 파일이 있고 force_rebuild가 False면 로드 시도
    if not force_rebuild and os.path.exists(cache_file):
        print(f"\n캐시된 인덱스 로드 중: {cache_file}")
        load_start = time.time()
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                title_to_indices = cached_data['title_to_indices']
                title_list = cached_data['title_list']
            
            elapsed = time.time() - load_start
            print(f"✅ 인덱스 로드 완료 (소요 시간: {elapsed:.2f}초)")
            print(f"   - 총 제목 수: {len(title_to_indices)}")
            print(f"   - 총 문서 수: {len(title_list)}")
            return title_to_indices, title_list
        except Exception as e:
            print(f"⚠️  캐시 로드 실패: {e}")
            print("   인덱스를 새로 생성합니다.")
    
    # 인덱스 생성
    print("\n인덱스 생성 중... (이 과정은 처음 한 번만 느립니다)")
    start_time = time.time()
    
    title_to_indices = defaultdict(list)
    title_list = []  # (idx, original_title, normalized_title) 매핑 (부분 검색용)
    
    for idx, item in enumerate(data):
        if 'title' in item:
            original_title = item['title'].strip()
            normalized_title = normalize_title(original_title)
            title_to_indices[normalized_title].append(idx)
            title_list.append((idx, original_title, normalized_title))
    
    elapsed = time.time() - start_time
    print(f"✅ 인덱스 생성 완료 (소요 시간: {elapsed:.2f}초)")
    print(f"   - 총 제목 수: {len(title_to_indices)}")
    print(f"   - 총 문서 수: {len(title_list)}")
    
    # 캐시 파일로 저장
    try:
        print(f"\n인덱스를 캐시 파일에 저장 중: {cache_file}")
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'title_to_indices': dict(title_to_indices),
                'title_list': title_list
            }, f)
        print(f"✅ 캐시 파일 저장 완료")
    except Exception as e:
        print(f"⚠️  캐시 파일 저장 실패: {e} (계속 진행합니다)")
    
    return title_to_indices, title_list

