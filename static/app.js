// 전역 변수
let currentCharacters = [];
let currentKeyword = '';
let isInitialized = false;

// DOM 요소 (초기화 함수로 이동)
let keywordInput, extractBtn, loadingDiv, loadingText, charactersSection, graphSection, graphContainer, errorDiv;
let sidebar, sidebarToggle, sidebarClose, sidebarOverlay, sidebarList, graphTitle, backToMainBtn;

// 초기화 함수
function initDOM() {
    keywordInput = document.getElementById('keyword');
    extractBtn = document.getElementById('extract-btn');
    loadingDiv = document.getElementById('loading');
    loadingText = document.getElementById('loading-text');
    charactersSection = document.getElementById('characters-section');
    graphSection = document.getElementById('graph-section');
    graphContainer = document.getElementById('graph-container');
    errorDiv = document.getElementById('error');
    sidebar = document.getElementById('sidebar');
    sidebarToggle = document.getElementById('sidebar-toggle');
    sidebarClose = document.getElementById('sidebar-close');
    sidebarOverlay = document.getElementById('sidebar-overlay');
    sidebarList = document.getElementById('sidebar-list');
    graphTitle = document.getElementById('graph-title');
    backToMainBtn = document.getElementById('back-to-main');
    
    // DOM 요소 확인
    if (!extractBtn) {
        console.error('extractBtn을 찾을 수 없습니다.');
        return false;
    }
    if (!keywordInput) {
        console.error('keywordInput을 찾을 수 없습니다.');
        return false;
    }
    
    return true;
}

// 이벤트 리스너 등록
function initEventListeners() {
    if (!extractBtn || !keywordInput) {
        console.error('DOM 요소가 초기화되지 않았습니다.');
        return;
    }
    
    extractBtn.addEventListener('click', handleGenerate);
    keywordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleGenerate();
        }
    });
    
    console.log('이벤트 리스너가 등록되었습니다.');
}

// 관계도 생성 (인물 추출 + 문서 크롤링 + 관계도 생성 통합)
async function handleGenerate() {
    // 초기화 확인
    if (!isInitialized) {
        console.warn('초기화가 완료되지 않았습니다. 잠시 후 다시 시도해주세요.');
        showError('페이지가 아직 로드 중입니다. 잠시 후 다시 시도해주세요.');
        return;
    }
    
    if (!keywordInput) {
        console.error('keywordInput이 초기화되지 않았습니다.');
        showError('페이지 초기화 오류가 발생했습니다. 페이지를 새로고침해주세요.');
        return;
    }
    
    const keyword = keywordInput.value.trim();
    
    if (!keyword) {
        showError('작품명을 입력해주세요.');
        return;
    }
    
    currentKeyword = keyword;
    
    // UI 업데이트
    setLoading(true, '인물 추출 중...');
    hideError();
    if (charactersSection) hideSection(charactersSection);
    if (graphSection) hideSection(graphSection);
    
    try {
        // 1. 인물 추출
        if (loadingText) {
            loadingText.textContent = '인물 추출 중...';
        }
        
        const extractResponse = await fetch('/api/extract-characters', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ keyword }),
        });
        
        const extractData = await extractResponse.json();
        
        if (!extractResponse.ok) {
            throw new Error(extractData.error || '인물 추출에 실패했습니다.');
        }
        
        currentCharacters = extractData.characters;
        console.log(`인물 추출 완료: ${currentCharacters.length}명`);
        
        // 2. 문서 크롤링
        if (loadingText) {
            loadingText.textContent = `문서 크롤링 중... (${currentCharacters.length}개)`;
        }
        
        const crawlResponse = await fetch('/api/crawl-documents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ character_names: currentCharacters }),
        });
        
        const crawlData = await crawlResponse.json();
        
        if (!crawlResponse.ok) {
            throw new Error(crawlData.error || '문서 크롤링에 실패했습니다.');
        }
        
        console.log(`크롤링 완료: ${crawlData.crawled_count}개 성공, ${crawlData.failed_count}개 실패`);
        
        // 3. 관계도 생성
        if (loadingText) {
            loadingText.textContent = '관계도 생성 중...';
        }
        
        const graphResponse = await fetch('/api/generate-graph', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: currentKeyword,
                character_names: currentCharacters,
                character_documents: crawlData.documents,
            }),
        });
        
        const graphData = await graphResponse.json();
        
        if (!graphResponse.ok) {
            throw new Error(graphData.error || '관계도 생성에 실패했습니다.');
        }
        
        console.log('API 응답:', graphData);
        console.log('그래프 데이터:', graphData.graph);
        
        // 4. 그래프 시각화
        if (!graphData.graph) {
            console.error('graphData.graph가 없습니다:', graphData);
            throw new Error('그래프 데이터 형식이 올바르지 않습니다.');
        }
        
        visualizeGraph(graphData.graph);
        
        // 5. 로컬스토리지에 저장
        saveGraphToLocalStorage(currentKeyword, graphData.graph, currentCharacters);
        
        // 6. 그래프 조회 페이지로 이동
        showGraphView(currentKeyword);
        
    } catch (error) {
        showError(`처리 실패: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

// 그래프 시각화
function visualizeGraph(graphData) {
    console.log('그래프 데이터:', graphData);
    graphContainer.innerHTML = '';
    
    if (!graphData || !graphData.characters || graphData.characters.length === 0) {
        console.error('그래프 데이터가 없거나 형식이 잘못되었습니다:', graphData);
        graphContainer.innerHTML = '<p style="padding: 20px; text-align: center;">그래프 데이터가 없습니다.</p>';
        return;
    }
    
    const width = graphContainer.clientWidth || 800;
    const height = graphContainer.clientHeight || 600;
    
    console.log(`그래프 컨테이너 크기: ${width}x${height}`);
    console.log(`인물 수: ${graphData.characters.length}, 관계 수: ${graphData.relationships?.length || 0}`);
    
    // SVG 생성 - 100% 너비로 설정하여 컨테이너 전체를 차지하도록
    const svg = d3.select('#graph-container')
        .append('svg')
        .attr('width', '100%')
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'none')
        .style('background', '#fff')
        .style('border', '1px solid #ddd');
    
    // 클리핑 경로 정의 (이미지 노드용) - svg에 직접 추가
    const defs = svg.append('defs');
    defs.append('clipPath')
        .attr('id', 'clip-circle')
        .append('circle')
        .attr('r', 25);
    
    const g = svg.append('g');
    
    // 줌 기능
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // 노드와 링크 데이터 준비
    const nodes = graphData.characters.map((char, i) => {
        const nodeId = char.name || char;
        return {
            id: nodeId,
            name: nodeId,
            label: nodeId,
            x: width / 2 + (Math.random() - 0.5) * 200,
            y: height / 2 + (Math.random() - 0.5) * 200,
            ...char
        };
    });
    
    // 노드 ID 맵 생성 (빠른 조회용)
    const nodeMap = new Map();
    nodes.forEach(node => {
        nodeMap.set(node.id, node);
    });
    
    // 링크 생성 및 양방향 링크 처리
    const linkMap = new Map(); // 양방향 링크 감지용
    const links = [];
    
    (graphData.relationships || []).forEach(rel => {
        const sourceNode = nodeMap.get(rel.from);
        const targetNode = nodeMap.get(rel.to);
        
        if (!sourceNode || !targetNode) {
            console.warn(`링크 매칭 실패: ${rel.from} -> ${rel.to}`, {
                sourceExists: !!sourceNode,
                targetExists: !!targetNode,
                availableNodes: Array.from(nodeMap.keys()).slice(0, 5)
            });
            return;
        }
        
        // 양방향 링크 감지: 반대 방향 링크가 이미 있는지 확인
        const reverseKey = `${rel.to}-${rel.from}`;
        const forwardKey = `${rel.from}-${rel.to}`;
        
        if (linkMap.has(reverseKey)) {
            // 양방향 링크 발견 - 기존 링크를 업데이트하여 양방향으로 표시
            const existingLink = linkMap.get(reverseKey);
            existingLink.isBidirectional = true;
            existingLink.reverseRelationship = rel.relationship || rel.type || rel.relation || '';
            // 양방향 링크는 하나만 추가
            return;
        }
        
        const link = {
            source: sourceNode,
            target: targetNode,
            relationship: rel.relationship || rel.type || rel.relation || '',
            strength: rel.strength || 1,
            isBidirectional: false,
            reverseRelationship: ''
        };
        
        linkMap.set(forwardKey, link);
        links.push(link);
    });
    
    console.log('노드 수:', nodes.length);
    console.log('링크 수:', links.length);
    console.log('샘플 노드:', nodes[0]);
    console.log('샘플 링크:', links[0]);
    console.log('노드 ID 목록:', Array.from(nodeMap.keys()).slice(0, 10));
    
    if (links.length === 0) {
        console.warn('관계 링크가 없습니다. 그래프를 그릴 수 없습니다.');
        graphContainer.innerHTML = '<p style="padding: 20px; text-align: center;">관계 데이터가 없습니다.</p>';
        return;
    }
    
    // 시뮬레이션 설정
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(250))
        .force('charge', d3.forceManyBody().strength(-1000))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(60))
        .alpha(1)
        .restart();
    
    // 리사이즈 이벤트 처리
    let resizeTimeout;
    const resizeObserver = new ResizeObserver(() => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            const newWidth = graphContainer.clientWidth;
            if (newWidth > 0 && newWidth !== width) {
                svg.attr('viewBox', `0 0 ${newWidth} ${height}`);
                // 시뮬레이션의 center force 업데이트
                simulation.force('center', d3.forceCenter(newWidth / 2, height / 2));
                simulation.alpha(0.3).restart();
            }
        }, 100);
    });
    
    resizeObserver.observe(graphContainer);
    
    // 링크 그리기
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(links)
        .enter()
        .append('line')
        .attr('class', 'link')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.strength) * 2);
    
    // 링크 레이블 - 양방향 링크 처리
    const linkLabelGroup = g.append('g').attr('class', 'link-labels');
    
    // 링크 레이블 데이터 준비 (각 레이블에 링크 정보 저장)
    const linkLabelData = [];
    links.forEach(link => {
        if (link.isBidirectional) {
            // 양방향 링크: 두 개의 레이블 데이터 생성
            linkLabelData.push({
                link: link,
                text: link.relationship,
                isReverse: false
            });
            linkLabelData.push({
                link: link,
                text: link.reverseRelationship,
                isReverse: true
            });
        } else {
            // 단방향 링크: 하나의 레이블 데이터
            linkLabelData.push({
                link: link,
                text: link.relationship,
                isReverse: false
            });
        }
    });
    
    const linkLabel = linkLabelGroup
        .selectAll('text')
        .data(linkLabelData)
        .enter()
        .append('text')
        .attr('class', 'link-label')
        .text(d => d.text)
        .style('font-size', '10px')
        .style('fill', '#666')
        .style('text-anchor', 'middle')
        .style('pointer-events', 'none');
    
    // 노드 그룹
    const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .enter()
        .append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // 노드 원 (이미지가 있으면 이미지, 없으면 원)
    node.each(function(d) {
        const nodeGroup = d3.select(this);
        
        if (d.image_src && d.image_src.startsWith('http')) {
            // 이미지 노드 - 원형 배경
            nodeGroup.append('circle')
                .attr('r', 25)
                .style('fill', '#fff')
                .style('stroke', '#667eea')
                .style('stroke-width', '2px');
            
            // 이미지
            nodeGroup.append('image')
                .attr('xlink:href', d.image_src)
                .attr('x', -25)
                .attr('y', -25)
                .attr('width', 50)
                .attr('height', 50)
                .attr('clip-path', 'url(#clip-circle)')
                .style('cursor', 'pointer');
        } else {
            // 일반 원형 노드
            nodeGroup.append('circle')
                .attr('r', 20)
                .style('fill', '#667eea')
                .style('stroke', '#fff')
                .style('stroke-width', '2px')
                .style('cursor', 'pointer');
        }
        
        // 노드 레이블
        nodeGroup.append('text')
            .text(d => d.label)
            .attr('dy', d.image_src && d.image_src.startsWith('http') ? 40 : 35)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('fill', '#333')
            .style('pointer-events', 'none')
            .style('font-weight', '600');
    });
    
    // 시뮬레이션 틱
    simulation.on('tick', () => {
        link
            .attr('x1', d => {
                const x = d.source.x;
                if (isNaN(x) || x === undefined) {
                    console.warn('링크 source.x가 유효하지 않음:', d);
                    return 0;
                }
                return x;
            })
            .attr('y1', d => {
                const y = d.source.y;
                if (isNaN(y) || y === undefined) {
                    return 0;
                }
                return y;
            })
            .attr('x2', d => {
                const x = d.target.x;
                if (isNaN(x) || x === undefined) {
                    console.warn('링크 target.x가 유효하지 않음:', d);
                    return 0;
                }
                return x;
            })
            .attr('y2', d => {
                const y = d.target.y;
                if (isNaN(y) || y === undefined) {
                    return 0;
                }
                return y;
            });
        
        // 링크 레이블 위치 업데이트
        linkLabel.attr('x', d => {
            const link = d.link;
            const midX = (link.source.x + link.target.x) / 2;
            
            if (link.isBidirectional) {
                // 양방향 링크: 수직 방향으로 오프셋
                const dx = link.target.x - link.source.x;
                const dy = link.target.y - link.source.y;
                const length = Math.sqrt(dx * dx + dy * dy);
                if (length > 0) {
                    const perpX = -dy / length * 20;
                    return midX + (d.isReverse ? -perpX : perpX);
                }
            }
            return midX;
        })
        .attr('y', d => {
            const link = d.link;
            const midY = (link.source.y + link.target.y) / 2;
            
            if (link.isBidirectional) {
                // 양방향 링크: 수직 방향으로 오프셋
                const dx = link.target.x - link.source.x;
                const dy = link.target.y - link.source.y;
                const length = Math.sqrt(dx * dx + dy * dy);
                if (length > 0) {
                    const perpY = dx / length * 20;
                    return midY + (d.isReverse ? -perpY : perpY);
                }
            }
            return midY;
        });
        
        node.attr('transform', d => {
            const x = d.x || 0;
            const y = d.y || 0;
            if (isNaN(x) || isNaN(y)) {
                console.warn('노드 위치가 유효하지 않음:', d);
                return `translate(0, 0)`;
            }
            return `translate(${x},${y})`;
        });
    });
    
    // 시뮬레이션 완료 시 로그
    simulation.on('end', () => {
        console.log('시뮬레이션 완료');
        console.log('노드 위치 샘플:', nodes.slice(0, 3).map(n => ({ id: n.id, x: n.x, y: n.y })));
    });
    
    // 초기 렌더링 강제 실행 (시뮬레이션이 시작되기 전에)
    setTimeout(() => {
        simulation.tick();
        console.log('초기 렌더링 완료');
    }, 100);
    
    // 드래그 함수
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

// 유틸리티 함수
function setLoading(show, text = '처리 중...') {
    if (show) {
        if (loadingText) loadingText.textContent = text;
        if (loadingDiv) loadingDiv.classList.remove('hidden');
        if (extractBtn) extractBtn.disabled = true;
    } else {
        if (loadingDiv) loadingDiv.classList.add('hidden');
        if (extractBtn) extractBtn.disabled = false;
    }
}

function showSection(section) {
    if (section) {
        section.classList.remove('hidden');
    }
}

function hideSection(section) {
    if (section) {
        section.classList.add('hidden');
    }
}

function showError(message) {
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    } else {
        console.error('Error:', message);
    }
}

function hideError() {
    if (errorDiv) {
        errorDiv.classList.add('hidden');
    }
}

// 로컬스토리지 관련 함수
function saveGraphToLocalStorage(keyword, graphData, characters) {
    try {
        const savedGraphs = getSavedGraphs();
        const graphEntry = {
            id: Date.now().toString(),
            keyword: keyword,
            createdAt: new Date().toISOString(),
            graphData: graphData,
            characters: characters,
            characterCount: characters.length,
            relationshipCount: graphData.relationships?.length || 0
        };
        
        savedGraphs.unshift(graphEntry); // 최신 항목을 맨 앞에 추가
        
        // 최대 50개까지만 저장
        if (savedGraphs.length > 50) {
            savedGraphs.pop();
        }
        
        localStorage.setItem('savedGraphs', JSON.stringify(savedGraphs));
        console.log('관계도가 로컬스토리지에 저장되었습니다.');
        
        // 목록 업데이트
        updateSavedGraphsList();
    } catch (error) {
        console.error('로컬스토리지 저장 실패:', error);
    }
}

function getSavedGraphs() {
    try {
        const saved = localStorage.getItem('savedGraphs');
        return saved ? JSON.parse(saved) : [];
    } catch (error) {
        console.error('로컬스토리지 읽기 실패:', error);
        return [];
    }
}

function loadGraphFromLocalStorage(graphId) {
    try {
        const savedGraphs = getSavedGraphs();
        const graph = savedGraphs.find(g => g.id === graphId);
        
        if (graph) {
            currentKeyword = graph.keyword;
            currentCharacters = graph.characters;
            keywordInput.value = graph.keyword;
            
            visualizeGraph(graph.graphData);
            showGraphView(graph.keyword);
            hideError();
            
            console.log('저장된 관계도를 불러왔습니다:', graph.keyword);
            return true;
        }
        return false;
    } catch (error) {
        console.error('로컬스토리지에서 불러오기 실패:', error);
        return false;
    }
}

function deleteGraphFromLocalStorage(graphId) {
    try {
        const savedGraphs = getSavedGraphs();
        const filtered = savedGraphs.filter(g => g.id !== graphId);
        localStorage.setItem('savedGraphs', JSON.stringify(filtered));
        updateSavedGraphsList();
        console.log('관계도가 삭제되었습니다.');
    } catch (error) {
        console.error('로컬스토리지 삭제 실패:', error);
    }
}

function updateSavedGraphsList() {
    if (!sidebarList) return;
    
    const savedGraphs = getSavedGraphs();
    
    if (savedGraphs.length === 0) {
        sidebarList.innerHTML = '<p class="sidebar-empty">저장된 관계도가 없습니다.</p>';
        return;
    }
    
    sidebarList.innerHTML = savedGraphs.map(graph => {
        const date = new Date(graph.createdAt);
        const dateStr = date.toLocaleDateString('ko-KR', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="sidebar-item" onclick="loadSavedGraph('${graph.id}')">
                <div class="sidebar-item-info">
                    <h3>${graph.keyword}</h3>
                    <p class="sidebar-item-meta">
                        인물: ${graph.characterCount}명 | 관계: ${graph.relationshipCount}개
                    </p>
                    <p class="sidebar-item-date">${dateStr}</p>
                </div>
                <button class="sidebar-item-delete" onclick="event.stopPropagation(); deleteSavedGraph('${graph.id}')">삭제</button>
            </div>
        `;
    }).join('');
}

// 전역 함수로 등록 (HTML에서 호출하기 위해)
window.loadSavedGraph = function(graphId) {
    if (loadGraphFromLocalStorage(graphId)) {
        // 사이드바 닫기
        sidebar.classList.remove('active');
        sidebarOverlay.classList.add('hidden');
    } else {
        showError('관계도를 불러올 수 없습니다.');
    }
};

function showGraphView(keyword) {
    if (charactersSection) hideSection(charactersSection);
    if (graphSection) showSection(graphSection);
    if (graphTitle) graphTitle.textContent = `${keyword} - 관계 그래프`;
    if (backToMainBtn) backToMainBtn.classList.remove('hidden');
}

function showMainPage() {
    if (graphSection) hideSection(graphSection);
    if (charactersSection) hideSection(charactersSection);
    if (backToMainBtn) backToMainBtn.classList.add('hidden');
    if (keywordInput) keywordInput.value = '';
    currentKeyword = '';
    currentCharacters = [];
}

window.deleteSavedGraph = function(graphId) {
    if (confirm('정말 이 관계도를 삭제하시겠습니까?')) {
        deleteGraphFromLocalStorage(graphId);
    }
};

// 페이지 로드 시 초기화
function init() {
    if (!initDOM()) {
        console.error('DOM 초기화 실패');
        return;
    }
    
    initEventListeners();
    
    // 사이드바 이벤트 리스너
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.add('active');
            sidebarOverlay.classList.remove('hidden');
        });
    }
    
    if (sidebarClose) {
        sidebarClose.addEventListener('click', () => {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.add('hidden');
        });
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.add('hidden');
        });
    }
    
    // 메인으로 돌아가기
    if (backToMainBtn) {
        backToMainBtn.addEventListener('click', () => {
            hideSection(graphSection);
            showMainPage();
        });
    }
    
    // 저장된 관계도 목록 표시
    updateSavedGraphsList();
    
    // 초기화 완료 플래그 설정
    isInitialized = true;
    
    console.log('초기화 완료');
}

// DOM 로드 완료 시 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}


