from flask import Flask, request, jsonify, render_template_string
import json
from datetime import datetime

app = Flask(__name__)

# 💡 시연을 위한 완벽한 모의 데이터(Mock Data)
reports_db = {
    "202-603": {"building": "202", "unit": "603", "avgNoise": 45, "maxNoise": 60, "status": "주의", "color": "#ffd60a", "totalEvents": 3, "noiseTypes": {"일반소음": 3}},
    "202-503": {"building": "202", "unit": "503", "avgNoise": 55, "maxNoise": 66, "status": "심각", "color": "#ff453a", "totalEvents": 12, "noiseTypes": {"발망치": 10, "가구끄는소리": 2}},
    "202-502": {"building": "202", "unit": "502", "avgNoise": 52, "maxNoise": 55, "status": "심각", "color": "#ff453a", "totalEvents": 5, "noiseTypes": {"일반소음": 5}},
    "202-103": {"building": "202", "unit": "103", "avgNoise": 30, "maxNoise": 35, "status": "양호", "color": "#32d74b", "totalEvents": 0, "noiseTypes": {}},
    "202-203": {"building": "202", "unit": "203", "avgNoise": 28, "maxNoise": 33, "status": "양호", "color": "#32d74b", "totalEvents": 0, "noiseTypes": {}},
}

@app.route('/api/report', methods=['POST'])
def receive_report():
    data = request.json
    building = data.get('building', '미상')
    unit = data.get('unit', '미상')
    
    avg_noise = data.get('avgNoise', 0)
    if avg_noise >= 50:
        status, color = "심각", "#ff453a"
    elif avg_noise >= 40:
        status, color = "주의", "#ffd60a"
    else:
        status, color = "양호", "#32d74b"
        
    data['status'] = status
    data['color'] = color
    data['time'] = datetime.now().strftime("%H:%M:%S")
    
    if 'noiseTypes' not in data:
        data['noiseTypes'] = {}
        
    key = f"{building}-{unit}"
    reports_db[key] = data
    return jsonify({"status": "success"})

@app.route('/')
def dashboard():
    html_template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Harmony Watcher 관제 시스템</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #09090b; margin: 0; padding: 15px; color: #ffffff; overflow: hidden; }
            .header { background: #1c1c1e; padding: 15px 30px; border-radius: 12px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
            h2 { color: #ffffff; margin: 0; font-size: 18px; }
            
            /* 💡 스크롤 방지를 위해 전체 높이를 화면에 딱 맞게 동적 계산 (100vh - 헤더 및 패딩) */
            .layout { display: flex; gap: 15px; height: calc(100vh - 90px); min-height: 600px; }
            
            /* 좌측 패널 */
            .left-panel { flex: 3.5; background: #1c1c1e; border-radius: 12px; padding: 20px; overflow-y: auto; border: 1px solid #333; }
            .section-label { font-size: 13px; color: #8e8e93; margin-bottom: 8px; font-weight: bold; }
            
            .building-select { width: 100%; background: #2c2c2e; color: #ff9f0a; border: 1px solid #ff9f0a; border-radius: 8px; padding: 10px; font-size: 15px; font-weight: bold; margin-bottom: 15px; outline: none; appearance: none; cursor: pointer; }
            
            .line-filters { display: flex; gap: 8px; margin-bottom: 15px; overflow-x: auto; padding-bottom: 5px; }
            .line-btn { flex: 1; min-width: 70px; background: #2c2c2e; color: #8e8e93; border: 1px solid #3a3a3c; padding: 8px 4px; border-radius: 8px; font-size: 12px; font-weight: bold; cursor: pointer; text-align: center; white-space: nowrap; transition: 0.2s; }
            .line-btn.active { background: rgba(255, 159, 10, 0.2); color: #ff9f0a; border-color: #ff9f0a; }
            
            .grid-container { display: flex; flex-direction: column; gap: 8px; width: 100%; }
            .floor-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; width: 100%; justify-content: center; }
            
            .unit-box { padding: 12px 5px; text-align: center; border-radius: 8px; font-size: 13px; font-weight: bold; cursor: pointer; transition: 0.2s; border: 1px solid #333; line-height: 1.4; }
            .status-none { background: #2c2c2e; color: #8e8e93; }
            .status-good { background: rgba(50, 215, 75, 0.15); color: #32d74b; border-color: rgba(50, 215, 75, 0.4); }
            .status-warn { background: rgba(255, 214, 10, 0.15); color: #ffd60a; border-color: rgba(255, 214, 10, 0.4); }
            .status-danger { background: rgba(255, 69, 58, 0.15); color: #ff453a; border-color: rgba(255, 69, 58, 0.4); }
            
            /* 우측 패널 */
            /* 💡 padding을 줄이고 세로 넘침(overflow)을 제한하여 공간 확보 */
            .right-panel { flex: 6.5; background: #1c1c1e; border-radius: 12px; padding: 15px 20px; border: 1px solid #333; position: relative; overflow: hidden; }
            
            .dashboard-view { display: flex; flex-direction: column; gap: 15px; height: 100%; }
            .top-row { display: flex; gap: 15px; height: 35%; }
            
            .chart-box { flex: 1; background: #2c2c2e; border: 1px solid #333; border-radius: 12px; padding: 12px; display: flex; flex-direction: column; }
            .chart-title { margin: 0 0 8px 0; color: #fff; font-size: 14px; font-weight: bold; }
            
            .alert-card { background: rgba(255, 69, 58, 0.1); border: 1px solid rgba(255, 69, 58, 0.5); border-radius: 12px; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; transition: 0.2s; }
            .alert-card:hover { background: rgba(255, 69, 58, 0.15); border-color: #ff453a; transform: translateY(-2px); }
            .alert-icon { font-size: 24px; margin-right: 15px; }
            .alert-text h4 { margin: 0 0 5px 0; color: #ff453a; font-size: 15px; }
            .alert-text p { margin: 0; color: #e5e5ea; font-size: 12px; }
            .alert-arrow { color: #ff453a; font-weight: bold; font-size: 16px; }
            
            .bottom-row { flex: 1; display: flex; flex-direction: column; background: #2c2c2e; border-radius: 12px; border: 1px solid #333; padding: 12px; min-height: 0; }
            .chart-canvas-container { position: relative; flex: 1; min-height: 0; width: 100%; }
            
            /* 💡 주기성 분석 뷰 압축 (여백과 gap 최소화) */
            .periodicity-view { display: none; height: 100%; flex-direction: column; gap: 8px; animation: fadeIn 0.3s; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            
            .back-btn { padding: 0 0 2px 0; background: transparent; color: #8e8e93; border: none; cursor: pointer; font-weight: bold; font-size: 12px; text-align: left; }
            .back-btn:hover { color: #fff; }
            
            .p-header { display: flex; align-items: center; gap: 12px; margin-bottom: 2px; }
            .p-header h3 { margin: 0; color: #fff; font-size: 18px; }
            .p-badge { background: rgba(255, 69, 58, 0.15); color: #ff453a; padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(255, 69, 58, 0.4); font-size: 12px; font-weight: bold; }
            
            /* 💡 차트 박스 내부 여백 축소 및 동적 높이 꽉 채움 설정 */
            .p-chart-box { background: #2c2c2e; border-radius: 12px; padding: 10px 15px; flex: 1; display: flex; flex-direction: column; border: 1px solid #333; min-height: 0; }
            
            .action-box { background: rgba(10, 132, 255, 0.1); padding: 12px 18px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(10, 132, 255, 0.3); margin-top: 2px; }
            .action-text { color: #fff; font-size: 13px; line-height: 1.4; flex: 1; padding-right: 20px; }
            .action-btn { background: #0a84ff; color: #fff; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; font-size: 13px; cursor: pointer; transition: 0.2s; white-space: nowrap; }
            .action-btn:hover { background: #0070f3; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🏢 Harmony Watcher - 실시간 단지 관제 센터</h2>
            <span style="color: #8e8e93;">관리자 님</span>
        </div>
        
        <div class="layout">
            <!-- 좌측 패널 -->
            <div class="left-panel">
                <div class="section-label">동 선택</div>
                <select class="building-select" id="bldgSelect" onchange="changeBuilding()">
                    <option value="202">🏢 202동 (의심 2건)</option>
                    <option value="201">🏢 201동 (양호)</option>
                    <option value="101">🏢 101동 (의심 1건)</option>
                </select>
                
                <div class="section-label">라인 필터</div>
                <div class="line-filters" id="lineFilters">
                    <button class="line-btn" onclick="changeLine('1')">1호 라인 (양호)</button>
                    <button class="line-btn" onclick="changeLine('2')">2호 라인 (양호)</button>
                    <button class="line-btn active" onclick="changeLine('3')">3호 라인 (의심 2건) ◀</button>
                    <button class="line-btn" onclick="changeLine('4')">4호 라인 (양호)</button>
                </div>
                
                <div class="section-label" id="gridTitle" style="margin-top: 15px;">202동 3호 라인 전용 표시 중</div>
                <div class="grid-container" id="unitGrid"></div>
            </div>
            
            <!-- 우측 패널 -->
            <div class="right-panel">
                <!-- 1. 대시보드 뷰 -->
                <div id="dashboardView" class="dashboard-view">
                    <div class="top-row">
                        <div class="chart-box">
                            <h4 class="chart-title">단지 소음 유형 통계</h4>
                            <div class="chart-canvas-container"><canvas id="typeChart"></canvas></div>
                        </div>
                        <div class="chart-box">
                            <h4 class="chart-title">세대별 평균/최고 소음 비교</h4>
                            <div class="chart-canvas-container"><canvas id="barChart"></canvas></div>
                        </div>
                    </div>
                    
                    <div class="alert-card" onclick="showPeriodicityView()">
                        <div style="display: flex; align-items: center;">
                            <div class="alert-icon">🚨</div>
                            <div class="alert-text">
                                <h4>[실시간 심층 리포트] 202동 503호 야간 층간소음 주기성 감지</h4>
                                <p>발망치 패턴 일치도 95% (상세 분석 및 조치하기)</p>
                            </div>
                        </div>
                        <div class="alert-arrow">➔</div>
                    </div>
                    
                    <div class="bottom-row">
                        <h4 class="chart-title">단지 시간대별 발생 통계</h4>
                        <div class="chart-canvas-container"><canvas id="timeChart"></canvas></div>
                    </div>
                </div>
                
                <!-- 2. 주기성 분석 뷰 -->
                <div id="periodicityView" class="periodicity-view">
                    <button class="back-btn" onclick="hidePeriodicityView()">◀ 대시보드 전체보기로 돌아가기</button>
                    
                    <div class="p-header">
                        <h3>503호 야간 층간소음 주기성 분석</h3>
                        <div class="p-badge">유사 사건 연속 감지 (발망치 패턴 일치도 95%)</div>
                    </div>
                    
                    <div class="p-chart-box">
                        <div class="chart-title" style="color: #32d74b;">아랫층(503호) 실내 소음 (dB) - 공기 전달음</div>
                        <div class="chart-canvas-container"><canvas id="noiseDbChart"></canvas></div>
                    </div>
                    
                    <div class="p-chart-box">
                        <div class="chart-title" style="color: #0a84ff;">아랫층(503호) 미세진동 (g) - 구조 전달음 (스파이크 일치)</div>
                        <div class="chart-canvas-container"><canvas id="vibChart"></canvas></div>
                    </div>
                    
                    <div class="action-box">
                        <div class="action-text">
                            <span style="color: #ff9f0a; font-weight: bold; font-size: 12px;">자동 중재 대상 : 위층(603호) 추정</span><br>
                            "[하모니워처] 10월 26일 23:32경 기준치(52dB)를 초과하는 반복적 바닥 충격이 아랫층(503호)에 지속 전달되었습니다. 야간 시간대 이웃을 위해 주의를 부탁드립니다."
                        </div>
                        <button class="action-btn" onclick="alert('603호로 모바일 안내문 발송이 완료되었습니다.')">✉️ 603호 안내문 발송</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            Chart.defaults.color = '#8e8e93';
            Chart.defaults.scale.grid.color = '#3a3a3c';
            Chart.defaults.font.size = 11; // 차트 기본 폰트 크기 축소

            const reports = {{ reports_json|safe }};
            let currentBuilding = '202';
            let currentLine = '3';
            
            let typeChartInst = null;
            let timeChartInst = null;
            let barChartInst = null;
            let vibChartInst = null;
            let noiseDbChartInst = null;

            function changeBuilding() {
                currentBuilding = document.getElementById('bldgSelect').value;
                renderGrid();
            }
            
            function changeLine(line) {
                currentLine = line;
                document.querySelectorAll('.line-btn').forEach(btn => {
                    if(btn.innerText.includes(line + '호 라인')) {
                        btn.classList.add('active');
                        btn.innerText = btn.innerText.replace(' ◀', '') + ' ◀';
                    } else {
                        btn.classList.remove('active');
                        btn.innerText = btn.innerText.replace(' ◀', '');
                    }
                });
                document.getElementById('gridTitle').innerText = `${currentBuilding}동 ${currentLine}호 라인 전용 표시 중`;
                renderGrid();
            }
            
            function renderGrid() {
                const gridContainer = document.getElementById('unitGrid');
                gridContainer.innerHTML = '';
                
                const floorRow = document.createElement('div');
                floorRow.className = 'floor-row';
                
                for(let f = 10; f >= 1; f--) {
                    let u = `${f}0${currentLine}`;
                    floorRow.appendChild(createUnitBox(currentBuilding, u));
                }
                gridContainer.appendChild(floorRow);
            }
            
            function createUnitBox(b, u) {
                const box = document.createElement('div');
                const key = `${b}-${u}`;
                const data = reports[key];
                
                if(data) {
                    box.innerHTML = `${u}호<br><span style="font-size:11px;">${data.status}</span>`;
                    if(data.status === '심각') box.className = 'unit-box status-danger';
                    else if(data.status === '주의') box.className = 'unit-box status-warn';
                    else box.className = 'unit-box status-good';
                    if(data.status === '심각') box.onclick = () => showPeriodicityView();
                } else {
                    box.innerHTML = `${u}호<br><span style="font-size:11px; font-weight:normal;">자료없음</span>`;
                    box.className = 'unit-box status-none';
                }
                return box;
            }

            function initGlobalCharts() {
                if(typeChartInst) typeChartInst.destroy();
                typeChartInst = new Chart(document.getElementById('typeChart'), {
                    type: 'doughnut',
                    data: {
                        labels: ['발망치 (미세진동+)', '가구 끄는 소리', '일반 공기전달음'],
                        datasets: [{ data: [10, 2, 8], backgroundColor: ['#ff453a', '#ff9f0a', '#0a84ff'], borderColor: '#2c2c2e' }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { boxWidth: 10 } } } }
                });

                if(timeChartInst) timeChartInst.destroy();
                timeChartInst = new Chart(document.getElementById('timeChart'), {
                    type: 'bar',
                    data: {
                        labels: ['오전(06~12)', '오후(12~18)', '저녁(18~22)', '심야(22~06)'],
                        datasets: [{ label: '발생 건수', data: [2, 1, 5, 12], backgroundColor: ['#32d74b', '#0a84ff', '#ff9f0a', '#bf5af2'], borderRadius: 4 }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });
                
                if(barChartInst) barChartInst.destroy();
                barChartInst = new Chart(document.getElementById('barChart'), {
                    type: 'bar',
                    data: {
                        labels: ['503호', '603호', '502호', '103호'],
                        datasets: [
                            { label: '최고 소음', data: [66, 60, 55, 35], backgroundColor: '#ff453a' },
                            { label: '평균 소음', data: [55, 45, 52, 30], backgroundColor: '#ffd60a' }
                        ]
                    },
                    options: { responsive: true, maintainAspectRatio: false, scales: { y: { suggestedMax: 80 } } }
                });
            }

            function showPeriodicityView() {
                document.getElementById('dashboardView').style.display = 'none';
                document.getElementById('periodicityView').style.display = 'flex';
                renderPeriodicityCharts();
            }
            
            function hidePeriodicityView() {
                document.getElementById('periodicityView').style.display = 'none';
                document.getElementById('dashboardView').style.display = 'flex';
            }
            
            function renderPeriodicityCharts() {
                const labels = [];
                const vibData = [];
                const noiseData = [];
                
                for(let i=0; i<=60; i++) {
                    labels.push(`23:30:${i < 10 ? '0'+i : i}`);
                    let v = Math.random() * 0.005;
                    let n = 30 + Math.random() * 5;
                    
                    if(i===15 || i===35 || i===50) {
                        v = 0.08 + Math.random() * 0.02;
                        n = 60 + Math.random() * 6;
                    }
                    if(i===16 || i===36 || i===51) { v = 0.03; n = 45; }
                    
                    vibData.push(v);
                    noiseData.push(n);
                }
                
                if(noiseDbChartInst) noiseDbChartInst.destroy();
                noiseDbChartInst = new Chart(document.getElementById('noiseDbChart'), {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: '측정 소음 (dB)', data: noiseData,
                            borderColor: '#32d74b', backgroundColor: 'rgba(50, 215, 75, 0.1)',
                            fill: true, tension: 0.2, pointRadius: 0, borderWidth: 2
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, scales: { y: { suggestedMax: 80, ticks: { maxTicksLimit: 5 } }, x: { ticks: { maxTicksLimit: 10 } } }, plugins: { legend: { display: false } } }
                });
                
                if(vibChartInst) vibChartInst.destroy();
                vibChartInst = new Chart(document.getElementById('vibChart'), {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: '구조 진동 (g)', data: vibData,
                            borderColor: '#0a84ff', backgroundColor: 'rgba(10, 132, 255, 0.1)',
                            fill: true, tension: 0.1, pointRadius: 0, borderWidth: 2
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, scales: { y: { suggestedMax: 0.15, ticks: { maxTicksLimit: 5 } }, x: { ticks: { maxTicksLimit: 10 } } }, plugins: { legend: { display: false } } }
                });
            }

            changeLine('3');
            initGlobalCharts();
        </script>
    </body>
    </html>
    """
    reports_json = json.dumps(reports_db)
    return render_template_string(html_template, reports_json=reports_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
