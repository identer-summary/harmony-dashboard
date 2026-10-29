from flask import Flask, request, jsonify, render_template_string
import json
from datetime import datetime

app = Flask(__name__)

# 초기 시연용 데이터 (앱에서 전송 시 503호 데이터가 실시간으로 덮어씌워짐)
reports_db = {
    "202-603": {"building": "202", "unit": "603", "avgNoise": 45, "maxNoise": 60, "status": "주의", "color": "#ffd60a", "totalEvents": 3},
    "202-503": {"building": "202", "unit": "503", "avgNoise": 55, "maxNoise": 82, "status": "심각", "color": "#ff453a", "totalEvents": 12},
    "202-502": {"building": "202", "unit": "502", "avgNoise": 52, "maxNoise": 55, "status": "심각", "color": "#ff453a", "totalEvents": 5},
    "202-103": {"building": "202", "unit": "103", "avgNoise": 30, "maxNoise": 35, "status": "양호", "color": "#32d74b", "totalEvents": 0},
    "202-203": {"building": "202", "unit": "203", "avgNoise": 28, "maxNoise": 33, "status": "양호", "color": "#32d74b", "totalEvents": 0},
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
    
    key = f"{building}-{unit}"
    if key in reports_db:
        reports_db[key].update(data)
    else:
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
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #09090b; margin: 0; padding: 15px; color: #ffffff; overflow: hidden; }
            .header { background: #1c1c1e; padding: 15px 30px; border-radius: 12px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
            h2 { color: #ffffff; margin: 0; font-size: 18px; }
            .layout { display: flex; gap: 15px; height: calc(100vh - 90px); min-height: 600px; }
            
            /* 좌측 패널 */
            .left-panel { flex: 3; background: #1c1c1e; border-radius: 12px; padding: 20px; overflow-y: auto; border: 1px solid #333; }
            .section-label { font-size: 13px; color: #8e8e93; margin-bottom: 8px; font-weight: bold; }
            .building-select { width: 100%; background: #2c2c2e; color: #ff9f0a; border: 1px solid #ff9f0a; border-radius: 8px; padding: 10px; font-size: 15px; font-weight: bold; margin-bottom: 15px; }
            .line-filters { display: flex; gap: 8px; margin-bottom: 15px; }
            .line-btn { flex: 1; background: #2c2c2e; color: #8e8e93; border: 1px solid #3a3a3c; padding: 8px 4px; border-radius: 8px; font-size: 12px; font-weight: bold; cursor: pointer; }
            .line-btn.active { background: rgba(255, 159, 10, 0.2); color: #ff9f0a; border-color: #ff9f0a; }
            .floor-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; width: 100%; justify-content: center; }
            .unit-box { padding: 12px 5px; text-align: center; border-radius: 8px; font-size: 13px; font-weight: bold; cursor: pointer; border: 1px solid #333; }
            .status-none { background: #2c2c2e; color: #8e8e93; }
            .status-good { background: rgba(50, 215, 75, 0.15); color: #32d74b; border-color: rgba(50, 215, 75, 0.4); }
            .status-warn { background: rgba(255, 214, 10, 0.15); color: #ffd60a; border-color: rgba(255, 214, 10, 0.4); }
            .status-danger { background: rgba(255, 69, 58, 0.15); color: #ff453a; border-color: rgba(255, 69, 58, 0.4); }
            
            /* 우측 패널 */
            .right-panel { flex: 7; background: #1c1c1e; border-radius: 12px; padding: 15px 20px; border: 1px solid #333; position: relative; overflow: hidden; }
            
            /* 1. 대시보드 메인 뷰 */
            .dashboard-view { display: flex; flex-direction: column; gap: 15px; height: 100%; }
            .top-row { display: flex; gap: 15px; height: 35%; }
            .chart-box { flex: 1; background: #2c2c2e; border: 1px solid #333; border-radius: 12px; padding: 12px; display: flex; flex-direction: column; }
            .chart-title { margin: 0 0 8px 0; color: #fff; font-size: 14px; }
            .alert-card { background: rgba(255, 69, 58, 0.1); border: 1px solid rgba(255, 69, 58, 0.5); border-radius: 12px; padding: 12px 20px; display: flex; justify-content: space-between; cursor: pointer; }
            .bottom-row { flex: 1; display: flex; flex-direction: column; background: #2c2c2e; border-radius: 12px; border: 1px solid #333; padding: 12px; }
            .chart-canvas-container { position: relative; flex: 1; min-height: 0; width: 100%; }
            
            /* 2. 심층 분석 리포트 뷰 */
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
            
            .action-btn { background: #ff453a; color: #fff; border: none; padding: 14px; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; text-align: center; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🏢 Harmony Watcher - 실시간 단지 관제 센터</h2>
            <span style="color: #8e8e93;" id="updateTime">데이터 대기 중...</span>
        </div>
        
        <div class="layout">
            <!-- 좌측 패널 -->
            <div class="left-panel">
                <div class="section-label">동 선택</div>
                <select class="building-select" id="bldgSelect"><option value="202">🏢 202동</option></select>
                <div class="section-label">라인 필터</div>
                <div class="line-filters">
                    <button class="line-btn">1호</button><button class="line-btn">2호</button>
                    <button class="line-btn active">3호 라인 ◀</button><button class="line-btn">4호</button>
                </div>
                <div class="grid-container" id="unitGrid"></div>
            </div>
            
            <!-- 우측 패널 -->
            <div class="right-panel">
                <!-- 1. 대시보드 뷰 -->
                <div id="dashboardView" class="dashboard-view">
                    <div class="top-row">
                        <div class="chart-box"><h4 class="chart-title">단지 소음 유형</h4><div class="chart-canvas-container"><canvas id="typeChart"></canvas></div></div>
                        <div class="chart-box"><h4 class="chart-title">세대별 소음 비교</h4><div class="chart-canvas-container"><canvas id="barChart"></canvas></div></div>
                    </div>
                    <div class="alert-card" onclick="showPeriodicityView()">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="font-size: 24px;">🚨</div>
                            <div>
                                <h4 style="margin: 0 0 5px 0; color: #ff453a; font-size: 15px;">[AI 심층 리포트] 202동 503호 야간 층간소음 주기성 감지</h4>
                                <p style="margin: 0; color: #e5e5ea; font-size: 12px;">클릭하여 603호(위층) 인과관계 분석 및 조치하기</p>
                            </div>
                        </div>
                    </div>
                    <div class="bottom-row"><h4 class="chart-title">단지 시간대별 통계</h4><div class="chart-canvas-container"><canvas id="timeChart"></canvas></div></div>
                </div>
                
                <!-- 2. 심층 분석 리포트 뷰 -->
                <div id="periodicityView" class="periodicity-view">
                    <button class="back-btn" onclick="hidePeriodicityView()">◀ 대시보드 메인으로</button>
                    
                    <div class="report-header">
                        <h3 class="report-title">심층 데이터 분석 리포트</h3>
                        <div class="target-info">
                            🔵 측정 대상: <span>202동 503호</span> (피해/측정 세대)<br>
                            🟠 중재 대상: <span style="color:#ff9f0a;">202동 603호</span> (원인/위층 세대)
                        </div>
                    </div>
                    
                    <div class="report-content">
                        <!-- 좌측: 실제 측정 데이터 차트 -->
                        <div class="chart-column">
                            <div class="data-summary">
                                <div class="data-card"><h4>최고 소음 (dB)</h4><div class="value" id="dispMaxDb">82.0 dB</div></div>
                                <div class="data-card"><h4>최고 진동 (g)</h4><div class="value vib" id="dispMaxVib">0.0021 g</div></div>
                                <div class="data-card"><h4>주요 주파수</h4><div class="value" style="color:#bf5af2;" id="dispFreq">150 Hz 이하</div></div>
                            </div>
                            <div class="timeline-box">
                                <h4 class="chart-title">실시간 데이터 타임라인 (503호 측정)</h4>
                                <div class="chart-canvas-container"><canvas id="realDataChart"></canvas></div>
                            </div>
                        </div>
                        
                        <!-- 우측: AI 판독 및 603호 경고문 -->
                        <div class="action-column">
                            <div class="letter-box">
                                <div class="letter-title">⚠️ 위층(603호) 전달용 주의 고지서 초안</div>
                                <div class="letter-content">
                                    <span style="color:#ff9f0a">수신: 202동 603호 귀하 및 관리사무소</span><br>
                                    <span style="color:#ff9f0a">발신: 공동주택 관리실 & 503호</span><br><br>
                                    <div style="border: 1px solid #333; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                                        <span style="color:#8e8e93; font-size:11px;">발생 원인: 건물 구조체를 통해 전달된 150Hz 이하 저주파 대역의 충격 진동</span>
                                    </div>
                                    아래층(503호)에서 측정된 데이터에 기반한 소음 완화 협조 요청입니다.<br><br>
                                    야간 시간대 동안 수치 기준을 초과하는 심각한 <span class="highlight">총격성 소음(최대 82.0dB)</span>과 <span class="highlight">미세 진동(최대 0.0021g)</span>이 아래층 실내로 전달되었습니다.<br><br>
                                    이는 AI 분석 결과, <span class="highlight">150Hz 이하의 저주파 대역</span>에 집중되어 있어 위층의 보행(발망치) 및 가구 이동 등으로 인한 중량 충격 패턴과 85.4% 일치합니다.<br><br>
                                    이웃 간의 평온한 휴식을 위해 야간 시간대 매트 사용 및 주의를 당부드립니다.
                                </div>
                                <button class="action-btn" onclick="alert('603호 입주민 앱 및 인터폰으로 주의 고지서가 발송되었습니다.')">603호 주의 및 협조 안내문 발송 ✉️</button>
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

            const reports = {{ reports_json|safe }};
            let realDataChartInst = null;

            // 💡 실제 503호 측정 60초 데이터 (Max 82dB, 0.0021g 추출값)
            const realNoiseData = [77, 77, 72, 72, 66, 66, 63, 63, 66, 66, 66, 66, 64, 64, 52, 52, 54, 54, 46, 66, 77, 77, 82, 82, 72, 59, 59, 43, 43, 55, 55, 64, 64, 64, 64, 77, 77, 73, 73, 70, 70, 61, 61, 57, 54, 54, 59, 59, 17, 48, 50, 50, 46, 52, 52, 52, 45, 45, 54, 54];
            const realVibData = [0.002, 0.002, 0.001, 0.001, 0.002, 0.002, 0.001, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002];
            const timeLabels = realNoiseData.map((_, i) => `${i}s`);

            function renderGrid() {
                const gridContainer = document.getElementById('unitGrid');
                gridContainer.innerHTML = '';
                const floorRow = document.createElement('div');
                floorRow.className = 'floor-row';
                
                for(let f = 10; f >= 1; f--) {
                    let u = `${f}03`;
                    let key = `202-${u}`;
                    let data = reports[key];
                    let box = document.createElement('div');
                    
                    if(data) {
                        box.innerHTML = `${u}호<br><span style="font-size:11px;">${data.status}</span>`;
                        if(data.status === '심각') box.className = 'unit-box status-danger';
                        else if(data.status === '주의') box.className = 'unit-box status-warn';
                        else box.className = 'unit-box status-good';
                        if(u === '503') box.onclick = () => showPeriodicityView();
                    } else {
                        box.innerHTML = `${u}호<br><span style="font-size:11px; font-weight:normal;">자료없음</span>`;
                        box.className = 'unit-box status-none';
                    }
                    floorRow.appendChild(box);
                }
                gridContainer.appendChild(floorRow);
                document.getElementById('updateTime').innerText = "최종 업데이트: " + new Date().toLocaleTimeString();
            }

            function showPeriodicityView() {
                document.getElementById('dashboardView').style.display = 'none';
                document.getElementById('periodicityView').style.display = 'flex';
                
                if(realDataChartInst) realDataChartInst.destroy();
                realDataChartInst = new Chart(document.getElementById('realDataChart'), {
                    type: 'line',
                    data: {
                        labels: timeLabels,
                        datasets: [
                            { label: '소음 (dB)', data: realNoiseData, borderColor: '#0a84ff', backgroundColor: 'rgba(10, 132, 255, 0.1)', yAxisID: 'y', tension: 0.1, borderWidth: 2, pointRadius: 0, fill: true },
                            { label: '미세진동 (g)', data: realVibData, borderColor: '#ff453a', backgroundColor: 'transparent', yAxisID: 'y1', tension: 0.1, borderWidth: 2, pointRadius: 0, borderDash: [5, 5] }
                        ]
                    },
                    options: { 
                        responsive: true, maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        scales: {
                            y: { type: 'linear', display: true, position: 'left', suggestedMax: 90, title: { display: true, text: '소음(dB)' } },
                            y1: { type: 'linear', display: true, position: 'right', suggestedMax: 0.003, grid: { drawOnChartArea: false }, title: { display: true, text: '진동(g)' } }
                        }
                    }
                });
            }
            
            function hidePeriodicityView() {
                document.getElementById('periodicityView').style.display = 'none';
                document.getElementById('dashboardView').style.display = 'flex';
            }

            function initGlobalCharts() {
                new Chart(document.getElementById('typeChart'), { type: 'doughnut', data: { labels: ['발망치(저주파)','일반소음'], datasets: [{ data: [12, 5], backgroundColor: ['#ff453a', '#0a84ff'], borderColor: '#2c2c2e' }] }, options: { responsive: true, maintainAspectRatio: false }});
                new Chart(document.getElementById('barChart'), { type: 'bar', data: { labels: ['503호','603호'], datasets: [{ label: '최고 dB', data: [82, 60], backgroundColor: '#ff453a' }] }, options: { responsive: true, maintainAspectRatio: false }});
                new Chart(document.getElementById('timeChart'), { type: 'bar', data: { labels: ['주간','야간'], datasets: [{ label: '발생', data: [2, 15], backgroundColor: '#bf5af2' }] }, options: { responsive: true, maintainAspectRatio: false }});
            }

            renderGrid();
            initGlobalCharts();

            // 💡 10초 주기 자동 새로고침 적용
            setInterval(() => {
                if (document.getElementById('periodicityView').style.display !== 'flex') {
                    location.reload();
                }
            }, 10000); 
        </script>
    </body>
    </html>
    """
    reports_json = json.dumps(reports_db)
    return render_template_string(html_template, reports_json=reports_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
