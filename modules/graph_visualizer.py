"""그래프 시각화 모듈 (HTML/JavaScript)"""
import json
from typing import Dict, Any, Optional


def generate_html_visualization(graph_data: Dict[str, Any], output_file: str, keyword: str = "인물 관계"):
    """
    HTML/JavaScript를 사용한 관계 그래프 시각화 생성
    
    Args:
        graph_data: AI가 생성한 그래프 데이터
        output_file: 저장할 HTML 파일 경로
        keyword: 키워드 (제목에 사용)
    """
    print(f"\n📊 HTML 관계 그래프 생성 중...")
    
    characters = graph_data.get('characters', [])
    relationships = graph_data.get('relationships', [])
    
    if len(characters) == 0:
        print("⚠️  그래프에 노드가 없습니다.")
        return
    
    # vis.js Network를 위한 데이터 변환
    nodes = []
    edges = []
    
    # 노드 생성
    for char in characters:
        name = char.get('name', '')
        if name:
            node = {
                'id': name,
                'label': name,
                'title': f"{name}\n{char.get('description', '')}"
            }
            image_src = char.get('image_src')
            if image_src:
                # 이미지 URL이면 그대로 사용
                if image_src.startswith('http://') or image_src.startswith('https://'):
                    node['image'] = image_src
                    node['shape'] = 'image'
                    node['size'] = 50  # 이미지 노드는 조금 더 크게
                else:
                    # 파일명 형식인 경우 (일반적으로는 URL이어야 함)
                    node['image'] = image_src
                    node['shape'] = 'image'
                    node['size'] = 50
            nodes.append(node)
    
    # 간선 생성
    for rel in relationships:
        from_char = rel.get('from', '')
        to_char = rel.get('to', '')
        relation = rel.get('relation', '')
        if from_char and to_char:
            edges.append({
                'from': from_char,
                'to': to_char,
                'label': relation,
                'arrows': 'to'
            })
    
    # JSON 데이터를 JavaScript 변수로 변환
    nodes_json = json.dumps(nodes, ensure_ascii=False, indent=2)
    edges_json = json.dumps(edges, ensure_ascii=False, indent=2)
    
    # HTML 템플릿
    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{keyword} - 인물 관계 그래프</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .info {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        .info-item {{
            text-align: center;
            margin: 10px;
        }}
        .info-item .number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .info-item .label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 5px;
        }}
        #network {{
            width: 100%;
            height: 800px;
            border: 1px solid #dee2e6;
            background: #fafafa;
        }}
        .controls {{
            padding: 20px;
            background: white;
            border-top: 1px solid #dee2e6;
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        button {{
            padding: 10px 20px;
            font-size: 1em;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            background: #667eea;
            color: white;
            transition: all 0.3s;
        }}
        button:hover {{
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .legend {{
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
        }}
        .legend h3 {{
            margin-top: 0;
            color: #495057;
        }}
        .legend-item {{
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .legend-item strong {{
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{keyword}</h1>
            <p>인물 관계 그래프</p>
        </div>
        <div class="info">
            <div class="info-item">
                <div class="number">{len(characters)}</div>
                <div class="label">인물 수</div>
            </div>
            <div class="info-item">
                <div class="number">{len(relationships)}</div>
                <div class="label">관계 수</div>
            </div>
        </div>
        <div id="network"></div>
        <div class="controls">
            <button onclick="fitNetwork()">전체 보기</button>
            <button onclick="resetZoom()">확대/축소 초기화</button>
            <button onclick="exportImage()">이미지 저장</button>
        </div>
        <div class="legend">
            <h3>사용 방법</h3>
            <div class="legend-item">
                <strong>노드 클릭:</strong> 인물 정보 확인
            </div>
            <div class="legend-item">
                <strong>드래그:</strong> 노드 이동
            </div>
            <div class="legend-item">
                <strong>마우스 휠:</strong> 확대/축소
            </div>
            <div class="legend-item">
                <strong>간선:</strong> 화살표 방향으로 관계 표시 (예: A → B = A가 B에게 관계)
            </div>
        </div>
    </div>

    <script type="text/javascript">
        // 데이터
        const nodes = new vis.DataSet({nodes_json});
        const edges = new vis.DataSet({edges_json});

        // 네트워크 옵션
        const nodeCount = {len(nodes)};
        // 노드 수에 따라 거리 조정
        const baseSpringLength = Math.max(300, nodeCount * 20);
        
        const options = {{
            nodes: {{
                shape: 'dot',
                size: 40,
                font: {{
                    size: 16,
                    face: 'Apple SD Gothic Neo, Malgun Gothic, sans-serif',
                    bold: true
                }},
                borderWidth: 3,
                shadow: {{
                    enabled: true,
                    size: 10,
                    x: 2,
                    y: 2
                }},
                color: {{
                    border: '#667eea',
                    background: '#ffffff',
                    highlight: {{
                        border: '#764ba2',
                        background: '#f0f0f0'
                    }}
                }},
                margin: 10
            }},
            edges: {{
                width: 2.5,
                color: {{
                    color: '#848484',
                    highlight: '#764ba2',
                    opacity: 0.8
                }},
                smooth: {{
                    type: 'dynamic',
                    roundness: 0.5,
                    forceDirection: 'none'
                }},
                font: {{
                    size: 13,
                    face: 'Apple SD Gothic Neo, Malgun Gothic, sans-serif',
                    align: 'middle',
                    color: '#333',
                    strokeWidth: 3,
                    strokeColor: '#ffffff'
                }},
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 1.5,
                        length: 15
                    }}
                }},
                labelHighlightBold: false,
                selectionWidth: 3
            }},
            physics: {{
                enabled: true,
                stabilization: {{
                    enabled: true,
                    iterations: 500,
                    updateInterval: 25
                }},
                barnesHut: {{
                    gravitationalConstant: -4000,
                    centralGravity: 0.1,
                    springLength: baseSpringLength,
                    springConstant: 0.02,
                    damping: 0.15,
                    avoidOverlap: 1.0
                }},
                repulsion: {{
                    nodeDistance: baseSpringLength * 1.5,
                    centralGravity: 0.1,
                    springLength: baseSpringLength,
                    springConstant: 0.02,
                    damping: 0.15
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100,
                zoomView: true,
                dragView: true,
                zoomSpeed: 0.5,
                dragNodes: true
            }},
            layout: {{
                improvedLayout: true,
                hierarchical: {{
                    enabled: false
                }}
            }}
        }};

        // 네트워크 생성
        const container = document.getElementById('network');
        const data = {{ nodes: nodes, edges: edges }};
        const network = new vis.Network(container, data, options);

        // 이벤트 핸들러
        network.on("click", function (params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                if (node) {{
                    alert(`인물: ${{node.label}}\\n\\n설명: ${{node.title || '설명 없음'}}`);
                }}
            }}
        }});

        // 컨트롤 함수
        function fitNetwork() {{
            network.fit();
        }}

        function resetZoom() {{
            network.moveTo({{ scale: 1 }});
        }}

        function exportImage() {{
            const canvas = network.getCanvas();
            const dataURL = canvas.toDataURL('image/png');
            const link = document.createElement('a');
            link.download = "{keyword}_graph.png";
            link.href = dataURL;
            link.click();
        }}
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"✅ HTML 그래프가 '{output_file}'에 저장되었습니다.")
    print(f"   - 노드 수: {len(nodes)}")
    print(f"   - 간선 수: {len(edges)}")

