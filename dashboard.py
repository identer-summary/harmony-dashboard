from flask import Flask, request, jsonify, render_template_string
import json
from datetime import datetime

app = Flask(__name__)

# 초기 DB (503호와 603호의 초기 설정값)
reports_db = {
    "202-603": {"building": "202", "unit": "603", "avgNoise": 45, "maxNoise": 60, "status": "주의", "vibration": 0.0015, "frequency": 150},
    "202-503": {"building": "202", "unit": "503", "avgNoise": 55, "maxNoise": 82, "status": "심각", "vibration": 0.0021, "frequency": 120},
}

@app.route('/api/report', methods=['POST'])
def receive_report():
    data = request.json
    building = data.get('building', '미상')
    unit = data.get('unit', '미상')
    
    avg_noise = data.get('avgNoise', 0)
    if avg_noise >= 50:
        status = "심각"
    elif avg_noise >= 40:
        status = "주의"
    else:
        status = "양호"
        
    data['status'] = status
    data['time'] = datetime.now().strftime("%H:%M:%S")
    
    key = f"{building}-{unit}"
    if key in reports_db:
        reports_db[key].update(data)
    else:
        reports_db[key] = data
        
    return jsonify({"status": "success"})

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(reports_db)

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
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #09090b; margin: 0; padding: 15px; color: #ffffff; overflow: hidden; }
            .header { background: #1c1c1e; padding: 15px 30px; border-radius: 12px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
            h2 { color: #ffffff; margin: 0; font-size: 18px; }
            .layout { display: flex; gap: 15px; height: calc(100vh - 90px); min-height: 600px; }
            .left-panel { flex: 1.5; background: #1c1c1e; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; border: 1px solid #333; }
            .section-label { font-size: 13px; color: #8e8e93; margin-bottom: 8px; font-weight: bold; }
            .building-select { width: 100%; background: #2c2c2e; color: #ff9f0a; border: 1px solid #ff9f0a; border-radius: 8px; padding: 10px; font-size: 15px; font-weight: bold; margin-bottom: 15px; outline: none; }
            .grid-container { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 5px; }
            .grid-container::-webkit-scrollbar { width: 6px; }
            .grid-container::-webkit-scrollbar-thumb { background-color: #3a3a3c; border-radius: 10px; }
            .unit-box { padding: 15px 10px; text-align: center; border-radius: 8px; font-size: 14px; font-weight: bold; cursor: pointer; border: 1px solid #333; flex-shrink: 0; transition: 0.2s; }
            .status-good { background: rgba(50, 215, 75, 0.15); color: #32d74b; border-color: rgba(50, 215, 75, 0.4); }
            .status-warn { background: rgba(255, 214, 10, 0.15); color: #ffd60a; border-color: rgba(255, 214, 10, 0.4); }
            .status-danger { background: rgba(255, 69, 58, 0.15); color: #ff453a; border-color: rgba(255, 69, 58, 0.4); box-shadow: 0 0 10px rgba(255,69,58,0.3); }
            .right-panel { flex: 8.5; background: #1c1c1e; border-radius: 12px; padding: 15px 20px; border: 1px solid #333; position: relative; overflow: hidden; }
            .dashboard-view { display: flex; flex-direction: column; gap: 15px; height: 100%; }
            .top-row { display: flex; gap: 15px; height: 35%; }
            .chart-box { flex: 1; background: #2c2c2e; border: 1px solid #333; border-radius: 12px; padding: 12px; display: flex; flex-direction: column; }
            .chart-title { margin: 0 0 8px 0; color: #fff; font-size: 14px; }
            .alert-card { background: rgba(255, 69, 58, 0.1); border: 1px solid rgba(255, 69, 58, 0.5); border-radius: 12px; padding: 12px 20px; display: flex; justify-content: space-between; cursor: pointer; transition: 0.2s; }
            .alert-card:hover { background: rgba(255, 69, 58, 0.2); transform: translateY(-2px); }
            .bottom-row { flex: 1; display: flex; flex-direction: column; background: #2c2c2e; border-radius: 12px; border: 1px solid #333; padding: 12px; min-height: 0; }
            .scrollable-chart-wrapper { overflow-x: auto; flex: 1; display: flex; }
            .scrollable-chart-wrapper::-webkit-scrollbar { height: 8px; }
            .scrollable-chart-wrapper::-webkit-scrollbar-thumb { background-color: #555; border-radius: 4px; }
            .chart-inner-container { min-width: 800px; height: 100%; flex: 1; position: relative; }
            .chart-canvas-container { position: relative; flex: 1; min-height: 0; width: 100%; }
            .periodicity-view { display: none; height: 100%; flex-direction: column; gap: 12px; }
            .back-btn { padding: 0 0 5px 0; background: transparent; color: #8e8e93; border: none; cursor: pointer; font-size: 12px; text-align: left; }
            .report-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 10px; }
            .report-title { font-size: 20px; font-weight: bold; margin: 0; }
            .target-info { font-size: 13px; color: #8e8e93; text-align: right; line-height: 1.5; }
            .target-info span { font-weight: bold; color: #fff; }
            .report-content { display: flex; gap: 15px; flex: 1; min-height: 0; }
            .chart-column { flex: 6; display: flex; flex-direction: column; gap: 10px; }
            .data-summary { display: flex; gap: 10px; }
            .data-card { background: #2c2c2e; border: 1px solid #333; border-radius: 8px; padding: 15px; flex: 1; text-align: center; }
            .data-card h4 { margin: 0 0 5px 0; color: #8e8e93; font-size: 12px; }
            .data-card .value { font-size: 22px; font-weight: bold; color: #ff453a; }
            .data-card .value.vib { color: #ff9f0a; }
            .timeline-box { background: #2c2c2e; border: 1px solid #333; border-radius: 12px; padding: 15px; flex: 1; display: flex; flex-direction: column; }
            .action-column { flex: 4; display: flex; flex-direction: column; gap: 10px; }
            .letter-box { background: rgba(255, 159, 10, 0.1); border: 1px solid rgba(255, 159, 10, 0.4); border-radius: 12px; padding: 15px; flex: 1; display: flex; flex-direction: column; }
            .letter-title { color: #ff9f0a; font-weight: bold; font-size: 15px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
            .letter-content { background: #1c1c1e; padding: 15px; border-radius: 8px; font-size: 13px; color: #d1d1d6; line-height: 1.6; flex: 1; border: 1px solid #333; overflow-y: auto; }
            .highlight { color: #ff453a; font-weight: bold; }
            .action-btn { background: #ff453a; color: #fff; border: none; padding: 14px; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; text-align: center; margin-top: 10px; transition: 0.2s; }
            .action-btn:hover { background: #ff3b30; transform: scale(1.02); }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🏢 Harmony Watcher - 실시간 단지 관제 센터</h2>
            <span style="color: #8e8e93;" id="updateTime">데이터 대기 중...</span>
        </div>
        
        <div class="layout">
            <div class="left-panel">
                <div class="section-label">동 선택</div>
                <select class="building-select" id="bldgSelect"><option value="202">🏢 202동</option></select>
                <div class="section-label">라인 선택</div>
                <select class="building-select" id="lineSelect" onchange="renderGrid()">
                    <option value="1">1호 라인</option><option value="2">2호 라인</option>
                    <option value="3" selected>3호 라인 ◀</option><option value="4">4호 라인</option>
                </select>
                <div class="section-label" style="margin-top: 5px;">세대 현황 (20층~1층)</div>
                <div class="grid-container" id="unitGrid"></div>
            </div>
            
            <div class="right-panel">
                <div id="dashboardView" class="dashboard-view">
                    <div class="top-row">
                        <div class="chart-box"><h4 class="chart-title">단지 소음 유형 통계</h4><div class="chart-canvas-container"><canvas id="typeChart"></canvas></div></div>
                        <div class="chart-box"><h4 class="chart-title">단지 시간대별 발생 통계</h4><div class="chart-canvas-container"><canvas id="timeChart"></canvas></div></div>
                    </div>
                    <div class="alert-card" onclick="showPeriodicityView('202-503')">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="font-size: 24px;">🚨</div>
                            <div>
                                <h4 style="margin: 0 0 5px 0; color: #ff453a; font-size: 15px;">[AI 심층 리포트] 202동 503호 야간 층간소음 주기성 감지</h4>
                                <p style="margin: 0; color: #e5e5ea; font-size: 12px;">클릭하여 위층 인과관계 분석 및 조치하기</p>
                            </div>
                        </div>
                    </div>
                    <div class="bottom-row">
                        <h4 class="chart-title" id="barChartTitle">세대별 소음 비교 (전체)</h4>
                        <div class="scrollable-chart-wrapper">
                            <div class="chart-inner-container">
                                <canvas id="barChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="periodicityView" class="periodicity-view">
                    <button class="back-btn" onclick="hidePeriodicityView()">◀ 대시보드 메인으로</button>
                    <div class="report-header">
                        <h3 class="report-title">심층 데이터 분석 리포트</h3>
                        <div class="target-info">
                            🔵 측정 대상: <span id="targetUnit">202동 503호</span> (피해/측정 세대)<br>
                            🟠 중재 대상: <span style="color:#ff9f0a;" id="causeUnit">202동 603호</span> (원인/위층 세대)
                        </div>
                    </div>
                    <div class="report-content">
                        <div class="chart-column">
                            <div class="data-summary">
                                <div class="data-card"><h4>최고 소음 (dB)</h4><div class="value" id="dispMaxDb">0 dB</div></div>
                                <div class="data-card"><h4>최고 진동 (mg)</h4><div class="value vib" id="dispMaxVib">0.00 mg</div></div>
                                <div class="data-card"><h4>주요 주파수</h4><div class="value" style="color:#bf5af2;" id="dispFreq">0 Hz</div></div>
                            </div>
                            <div class="timeline-box">
                                <h4 class="chart-title">위층 발생 추정 충격 전달 패턴</h4>
                                <div class="chart-canvas-container"><canvas id="realDataChart"></canvas></div>
                            </div>
                        </div>
                        
                        <div class="action-column">
                            <div class="letter-box">
                                <div class="letter-title">⚠️ 주의 고지서 초안</div>
                                <div class="letter-content">
                                    <span style="color:#ff9f0a" id="letterTo">수신: 202동 603호 귀하 및 관리사무소</span><br>
                                    <span style="color:#ff9f0a">발신: 공동주택 관리실</span><br><br>
                                    <div style="border: 1px solid #333; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                                        <span style="color:#8e8e93; font-size:11px;">발생 원인: 건물 구조체를 통해 전달된 저주파 대역의 충격 진동</span>
                                    </div>
                                    아래층에서 측정된 데이터에 기반한 소음 완화 협조 요청입니다.<br><br>
                                    야간 시간대 동안 수치 기준을 초과하는 심각한 <span class="highlight">총격성 소음(최대 <span id="textMaxDb">82.0</span>dB)</span>과 
                                    <span class="highlight">미세 진동(최대 <span id="textMaxVib">2.10</span>mg)</span>이 아래층 실내로 전달되었습니다.<br><br>
                                    이는 AI 분석 결과, <span class="highlight">저주파 대역(<span id="textFreq">150</span>Hz)</span>에 집중되어 있어 보행(발망치) 및 가구 이동 등으로 인한 중량 충격 패턴과 일치합니다.<br><br>
                                    이웃 간의 평온한 휴식을 위해 야간 시간대 매트 사용 및 주의를 당부드립니다.
                                </div>
                                <button class="action-btn" onclick="alert('주의 고지서가 발송되었습니다.')">주의 및 협조 안내문 발송 ✉️</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            Chart.defaults.color = '#8e8e93';
            Chart.defaults.scale.grid.color = '#3a3a3c';
            Chart.defaults.font.size = 11;

            let reports = {{ reports_json|safe }};
            let realDataChartInst = null;
            let barChartInst = null;
            let currentOpenUnit = null;

            const fallbackNoise = [77, 77, 72, 72, 66, 66, 63, 63, 66, 66, 66, 66, 64, 64, 52, 52, 54, 54, 46, 66, 77, 77, 82, 82, 72, 59, 59, 43, 43, 55, 55, 64, 64, 64, 64, 77, 77, 73, 73, 70, 70, 61, 61, 57, 54, 54, 59, 59, 17, 48, 50, 50, 46, 52, 52, 52, 45, 45, 54, 54];
            const fallbackVibRaw = [0.002, 0.002, 0.001, 0.001, 0.002, 0.002, 0.001, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002];
            const fallbackTime = fallbackNoise.map((_, i) => `${i}s`);

            function ensureDataForLine(line) {
                for(let f = 1; f <= 20; f++) {
                    let u = `${f}0${line}`;
                    let key = `202-${u}`;
                    if(!reports[key]) {
                        let fakeNoise = Math.floor(Math.random() * 15) + 20;
                        let rand = Math.random();
                        if (rand > 0.95) fakeNoise = Math.floor(Math.random() * 10) + 50; 
                        else if (rand > 0.85) fakeNoise = Math.floor(Math.random() * 10) + 40; 

                        let status = '양호';
                        if(fakeNoise >= 50) status = '심각';
                        else if(fakeNoise >= 40) status = '주의';
                        
                        reports[key] = {
                            building: "202",
                            unit: u,
                            maxNoise: fakeNoise,
                            avgNoise: fakeNoise - 5,
                            vibration: 0.0,
                            frequency: 0,
                            status: status
                        };
                    }
                }
            }

            function renderGrid() {
                const line = document.getElementById('lineSelect').value;
                document.getElementById('barChartTitle').innerText = `세대별 소음 비교 (${line}호 라인 전체)`;
                
                ensureDataForLine(line);
                
                const gridContainer = document.getElementById('unitGrid');
                gridContainer.innerHTML = '';
                let targetId = null;
                
                for(let f = 20; f >= 1; f--) {
                    let u = `${f}0${line}`;
                    let key = `202-${u}`;
                    let data = reports[key];
                    let box = document.createElement('div');
                    
                    box.innerHTML = `${u}호<br><span style="font-size:12px;">${data.status}</span>`;
                    if(data.status === '심각') {
                        box.className = 'unit-box status-danger';
                        if(u === '503') targetId = `unit-${u}`; 
                    } else if(data.status === '주의') {
                        box.className = 'unit-box status-warn';
                    } else {
                        box.className = 'unit-box status-good';
                    }
                    box.onclick = () => showPeriodicityView(key);
                    box.id = `unit-${u}`;
                    gridContainer.appendChild(box);
                }
                
                if(!currentOpenUnit) {
                    setTimeout(() => {
                        if(targetId) {
                            const targetBox = document.getElementById(targetId);
                            if(targetBox) targetBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }, 300);
                }
                
                document.getElementById('updateTime').innerText = "최종 업데이트: " + new Date().toLocaleTimeString();
                updateBarChart(line);
            }

            function updateBarChart(line) {
                const labels = [];
                const maxDbs = [];
                const bgColors = []; // 🚀 색상 동기화를 위한 배열
                
                for(let f = 1; f <= 20; f++) {
                    let u = `${f}0${line}`;
                    labels.push(`${u}호`);
                    let key = `202-${u}`;
                    
                    if (reports[key]) {
                        maxDbs.push(reports[key].maxNoise);
                        
                        // 🚀 차트 색상도 좌측 그리드와 100% 동일하게 'status' 값을 기준으로 칠하도록 수정!
                        let status = reports[key].status;
                        if (status === '심각') {
                            bgColors.push('#ff453a');
                        } else if (status === '주의') {
                            bgColors.push('#ffd60a');
                        } else {
                            bgColors.push('#32d74b');
                        }
                    } else {
                        maxDbs.push(0);
                        bgColors.push('#32d74b');
                    }
                }
                
                if(barChartInst) barChartInst.destroy();
                barChartInst = new Chart(document.getElementById('barChart'), {
                    type: 'bar',
                    data: { 
                        labels: labels, 
                        datasets: [{ 
                            label: '최고 소음 (dB)', 
                            data: maxDbs, 
                            backgroundColor: bgColors, // 🚀 상태 기준 색상 적용 완료
                            borderRadius: 4 
                        }] 
                    },
                    options: { responsive: true, maintainAspectRatio: false, animation: {duration: 0}, scales: { y: { suggestedMax: 90 } }, plugins: { legend: { display: false } } }
                });
            }

            function showPeriodicityView(unitKey) {
                currentOpenUnit = unitKey;
                document.getElementById('dashboardView').style.display = 'none';
                document.getElementById('periodicityView').style.display = 'flex';
                
                const data = reports[unitKey];
                let plotNoise = fallbackNoise;
                let plotVib = fallbackVibRaw.map(v => v * 1000); 
                let plotTime = fallbackTime;
                
                if(data) {
                    document.getElementById('targetUnit').innerText = `202동 ${data.unit}호`;
                    document.getElementById('causeUnit').innerText = `202동 ${parseInt(data.unit)+100}호`;
                    document.getElementById('letterTo').innerText = `수신: 202동 ${parseInt(data.unit)+100}호 귀하 및 관리사무소`;
                    
                    document.getElementById('dispMaxDb').innerText = `${data.maxNoise || 0} dB`;
                    document.getElementById('textMaxDb').innerText = `${data.maxNoise || 0}`;
                    
                    let vib_mg = (data.vibration || 0) * 1000;
                    document.getElementById('dispMaxVib').innerText = `${vib_mg.toFixed(2)} mg`;
                    document.getElementById('textMaxVib').innerText = `${vib_mg.toFixed(2)}`;
                    
                    document.getElementById('dispFreq').innerText = `${data.frequency || 0} Hz 이하`;
                    document.getElementById('textFreq').innerText = `${data.frequency || 0}`;

                    if(data.measurements && data.measurements.length > 0) {
                        plotNoise = data.measurements.map(m => m.noise);
                        plotVib = data.measurements.map(m => m.vibration * 1000); 
                        plotTime = data.measurements.map(m => m.time);
                    }
                }
                
                if(realDataChartInst) {
                    realDataChartInst.data.labels = plotTime;
                    realDataChartInst.data.datasets[0].data = plotNoise;
                    realDataChartInst.data.datasets[1].data = plotVib;
                    realDataChartInst.update();
                } else {
                    realDataChartInst = new Chart(document.getElementById('realDataChart'), {
                        type: 'line',
                        data: {
                            labels: plotTime,
                            datasets: [
                                { label: '소음 (dB)', data: plotNoise, borderColor: '#0a84ff', backgroundColor: 'rgba(10, 132, 255, 0.1)', yAxisID: 'y', tension: 0.1, borderWidth: 2, pointRadius: 0, fill: true },
                                { label: '미세진동 (mg)', data: plotVib, borderColor: '#ff453a', backgroundColor: 'transparent', yAxisID: 'y1', tension: 0.1, borderWidth: 2, pointRadius: 0, borderDash: [5, 5] }
                            ]
                        },
                        options: { 
                            responsive: true, maintainAspectRatio: false,
                            interaction: { mode: 'index', intersect: false },
                            animation: { duration: 0 },
                            scales: {
                                y: { type: 'linear', display: true, position: 'left', suggestedMax: 90, title: { display: true, text: '소음(dB)' } },
                                y1: { type: 'linear', display: true, position: 'right', suggestedMax: 3.0, grid: { drawOnChartArea: false }, title: { display: true, text: '진동(mg)' } }
                            }
                        }
                    });
                }
            }
            
            function hidePeriodicityView() {
                currentOpenUnit = null;
                document.getElementById('periodicityView').style.display = 'none';
                document.getElementById('dashboardView').style.display = 'flex';
                renderGrid();
            }

            function initGlobalCharts() {
                new Chart(document.getElementById('typeChart'), { type: 'doughnut', data: { labels: ['발망치(저주파)','가구끌기','일반소음'], datasets: [{ data: [12, 4, 8], backgroundColor: ['#ff453a', '#ff9f0a', '#0a84ff'], borderColor: '#2c2c2e' }] }, options: { responsive: true, maintainAspectRatio: false }});
                new Chart(document.getElementById('timeChart'), { type: 'bar', data: { labels: ['오전','오후','저녁','야간(심야)'], datasets: [{ label: '발생 건수', data: [2, 1, 6, 15], backgroundColor: ['#32d74b', '#0a84ff', '#ff9f0a', '#bf5af2'], borderRadius: 4 }] }, options: { responsive: true, maintainAspectRatio: false }});
            }

            initGlobalCharts();
            renderGrid();

            setInterval(() => {
                fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    Object.assign(reports, data);
                    if (currentOpenUnit) {
                        showPeriodicityView(currentOpenUnit);
                    } else {
                        renderGrid();
                    }
                })
                .catch(error => console.error("데이터 갱신 실패:", error));
            }, 5000); 
        </script>
    </body>
    </html>
    """
    reports_json = json.dumps(reports_db)
    return render_template_string(html_template, reports_json=reports_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
