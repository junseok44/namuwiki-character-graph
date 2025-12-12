"""등장인물 관계 그래프 웹 서버"""
import os
import sys
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# 현재 프로젝트 폴더의 데이터 경로
BASE_DIR = os.path.dirname(__file__)
DATASET_PATH = os.path.join(BASE_DIR, 'data')
INDEX_CACHE_FILE = os.path.join(BASE_DIR, 'title_index_cache.pkl')

# 현재 프로젝트의 modules 사용
from modules.namuwiki_dataset import (
    load_namuwiki_dataset,
    get_data_from_dataset,
    build_title_index,
)
from modules.document_search import (
    find_document_by_exact_title_indexed,
    find_document_by_keyword_included,
    find_most_similar_document,
)
from modules.image_extractor import extract_all_image_urls
from modules.character_extractor import extract_character_names_with_ai
from modules.graph_generator import extract_character_relationships_with_ai
from modules.ai_service import reset_ai_request_stats
from modules.namuwiki_web import fetch_namuwiki_page

app = Flask(__name__)
CORS(app)

# 전역 변수: 서버 시작 시 로드된 데이터셋과 인덱스
dataset = None
data = None
title_to_indices = None
title_list = None


def load_dataset_and_index():
    """서버 시작 시 데이터셋과 인덱스를 메모리에 로드"""
    global dataset, data, title_to_indices, title_list
    
    print(f"데이터셋 경로: {DATASET_PATH}")
    print(f"인덱스 캐시 파일: {INDEX_CACHE_FILE}")
    
    # 절대 경로로 변환하여 전달
    dataset_abs_path = os.path.abspath(DATASET_PATH)
    dataset = load_namuwiki_dataset(dataset_abs_path)
    data = get_data_from_dataset(dataset)
    print(f"총 문서 수: {len(data)}")
    
    print("인덱스 생성 중...")
    index_cache_abs_path = os.path.abspath(INDEX_CACHE_FILE)
    title_to_indices, title_list = build_title_index(
        data, cache_file=index_cache_abs_path, force_rebuild=False
    )
    print("데이터셋 및 인덱스 로드 완료!")


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/extract-characters', methods=['POST'])
def extract_characters():
    """작품명을 받아서 인물명 추출"""
    try:
        req_data = request.get_json()
        keyword = req_data.get('keyword')
        
        if not keyword:
            return jsonify({'error': 'keyword가 필요합니다.'}), 400
        
        print(f"\n[인물 추출] 키워드: {keyword}")
        
        # AI 요청 통계 초기화
        reset_ai_request_stats()
        
        # 1. 두 개의 독립적인 프로세스로 가장 유사한 문서 찾기
        
        # 프로세스 1: keyword와 가장 유사한 메인 문서 찾기
        main_doc_idx, main_doc, matched_main_title, main_similarity = find_most_similar_document(
            title_list, title_to_indices, data, keyword, suffix=None, verbose=False
        )
        
        if main_doc_idx is None:
            return jsonify({'error': f"'{keyword}' 관련 문서를 찾을 수 없습니다."}), 404
        
        # 프로세스 2: keyword와 가장 유사한 등장인물 문서 찾기
        char_doc_idx, char_doc, matched_char_title, char_similarity = find_most_similar_document(
            title_list, title_to_indices, data, keyword, suffix="/등장인물", verbose=False
        )
        
        if char_doc_idx is None:
            char_doc = {'title': '', 'text': ''}
            matched_char_title = None
            char_similarity = 0.0
        
        # 2. AI에게 두 문서 내용 보내서 인물 리스트 추출 (최대 20명)
        main_doc_text = main_doc.get('text', '')
        char_list_doc_text = char_doc.get('text', '')
        
        character_names = extract_character_names_with_ai(
            keyword, main_doc_text, char_list_doc_text, max_characters=20
        )
        
        if not character_names:
            return jsonify({'error': '추출된 인물이 없습니다.'}), 404
        
        print(f"✅ 추출된 인물 ({len(character_names)}명): {character_names}")
        
        return jsonify({
            'success': True,
            'characters': character_names,
            'main_document': {
                'title': main_doc.get('title', ''),
                'index': main_doc_idx
            },
            'character_list_document': {
                'title': char_doc.get('title', ''),
                'index': char_doc_idx if char_doc_idx else None
            }
        })
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/crawl-documents', methods=['POST'])
def crawl_documents():
    """인물명 리스트를 받아서 나무위키에서 문서 크롤링"""
    try:
        req_data = request.get_json()
        character_names = req_data.get('character_names', [])
        
        if not character_names:
            return jsonify({'error': 'character_names가 필요합니다.'}), 400
        
        # 최대 20명으로 제한
        max_characters = 20
        if len(character_names) > max_characters:
            character_names = character_names[:max_characters]
            print(f"⚠️  인물 수가 {max_characters}명을 초과하여 {max_characters}명으로 제한했습니다.")
        
        print(f"\n[문서 크롤링] 인물 수: {len(character_names)}")
        
        documents = []
        for i, char_name in enumerate(character_names, 1):
            print(f"  [{i}/{len(character_names)}] '{char_name}' 크롤링 중...")
            doc = fetch_namuwiki_page(char_name)
            if doc:
                doc['type'] = 'character'
                doc['source'] = 'web'
                documents.append(doc)
                print(f"    ✅ 크롤링 성공: '{doc['title']}'")
            else:
                print(f"    ⚠️  크롤링 실패: '{char_name}'")
        
        return jsonify({
            'success': True,
            'documents': documents,
            'crawled_count': len(documents),
            'failed_count': len(character_names) - len(documents)
        })
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-graph', methods=['POST'])
def generate_graph():
    """문서들을 받아서 관계도 생성"""
    try:
        req_data = request.get_json()
        keyword = req_data.get('keyword')
        character_documents = req_data.get('character_documents', [])  # 클라이언트에서 크롤링한 문서들
        character_names = req_data.get('character_names', [])
        
        if not keyword:
            return jsonify({'error': 'keyword가 필요합니다.'}), 400
        
        print(f"\n[관계도 생성] 키워드: {keyword}, 문서 수: {len(character_documents)}")
        
        # AI 요청 통계 초기화
        reset_ai_request_stats()
        
        all_documents = []
        
        # 메인 문서와 등장인물 목록 문서 찾기 (유사도 기반)
        # 프로세스 1: 메인 문서 찾기
        main_doc_idx, main_doc, matched_main_title, main_similarity = find_most_similar_document(
            title_list, title_to_indices, data, keyword, suffix=None, verbose=False
        )
        
        if main_doc:
            main_doc_text = main_doc.get('text', '')
            main_image_urls = extract_all_image_urls(main_doc_text)
            all_documents.append({
                'title': main_doc.get('title', ''),
                'text': main_doc_text,
                'image_urls': main_image_urls,
                'type': 'main'
            })
        else:
            print(f"⚠️  메인 문서를 찾을 수 없습니다.")
        
        # 프로세스 2: 등장인물 목록 문서 찾기
        char_doc_idx, char_list_doc, matched_char_title, char_similarity = find_most_similar_document(
            title_list, title_to_indices, data, keyword, suffix="/등장인물", verbose=False
        )
        
        if char_list_doc and char_list_doc.get('text'):
            char_list_doc_text = char_list_doc.get('text', '')
            char_list_image_urls = extract_all_image_urls(char_list_doc_text)
            all_documents.append({
                'title': char_list_doc.get('title', ''),
                'text': char_list_doc_text,
                'image_urls': char_list_image_urls,
                'type': 'character_list'
            })
        
        # 클라이언트에서 크롤링한 문서들 추가
        found_characters = []
        for doc in character_documents:
            all_documents.append(doc)
            found_characters.append(doc.get('title', ''))
        
        # 웹 크롤링 실패한 인물 문서를 데이터셋에서 찾기
        crawled_titles = {doc.get('title', '') for doc in character_documents}
        missing_characters = [name for name in character_names if name not in crawled_titles]
        
        if missing_characters:
            print(f"⚠️  웹 크롤링 실패한 인물 ({len(missing_characters)}명): {missing_characters}")
            print("데이터셋에서 찾는 중...")
            
            for char_name in missing_characters:
                char_doc_idx, char_doc = find_document_by_exact_title_indexed(
                    title_to_indices, data, char_name
                )
                
                if char_doc_idx is not None and char_doc:
                    char_doc_text = char_doc.get('text', '')
                    char_image_urls = extract_all_image_urls(char_doc_text)
                    all_documents.append({
                        'title': char_doc.get('title', ''),
                        'text': char_doc_text,
                        'image_urls': char_image_urls,
                        'type': 'character',
                        'source': 'dataset'
                    })
                    found_characters.append(char_doc.get('title', ''))
                    print(f"✅ 데이터셋에서 찾음: {char_doc.get('title', '')}")
        
        print(f"\n✅ 총 {len(all_documents)}개의 문서를 수집했습니다.")
        
        # 4. 모든 문서 합쳐서 AI에게 관계 그래프 요청
        print("AI를 사용한 관계 그래프 생성 중...")
        graph_data = extract_character_relationships_with_ai(keyword, all_documents)
        
        return jsonify({
            'success': True,
            'graph': graph_data,
            'found_characters': found_characters,
            'total_documents': len(all_documents)
        })
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # 서버 시작 시 데이터셋과 인덱스 로드
    load_dataset_and_index()
    
    # Flask 서버 실행
    app.run(debug=True, host='0.0.0.0', port=5000)

