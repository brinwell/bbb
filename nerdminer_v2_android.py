import http.server
import socketserver
import threading
import time
import hashlib
import random
import json
import requests
from datetime import datetime

class NerdMinerV2:
    def __init__(self):
        self.mining = False
        self.stats = {
            'hash_rate': 0,
            'total_hashes': 0,
            'accepted_shares': 0,
            'rejected_shares': 0,
            'uptime': 0,
            'temperature': 45,
            'block_height': 0,
            'difficulty': "0",
            'network_hashrate': "0 EH/s",
            'btc_price': 0,
            'pool': "nerdminer.com:3333",
            'worker': "android",
            'efficiency': "100%"
        }
        self.start_time = 0
        self.hash_history = []
        self.last_shares = []
        
        # Загружаем реальные данные
        self.update_network_data()
        
    def update_network_data(self):
        """Получение реальных данных из сети"""
        try:
            # BTC цена
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
            if response.status_code == 200:
                self.stats['btc_price'] = response.json()['bitcoin']['usd']
            
            # Данные блокчейна
            response = requests.get("https://blockchain.info/q/getblockcount", timeout=5)
            if response.status_code == 200:
                self.stats['block_height'] = int(response.text)
            
            response = requests.get("https://blockchain.info/q/getdifficulty", timeout=5)
            if response.status_code == 200:
                diff = float(response.text)
                self.stats['difficulty'] = f"{diff/1e12:.2f} T"
                self.stats['network_hashrate'] = f"{diff * 2**32 / 600 / 1e18:.2f} EH/s"
                
        except Exception as e:
            print(f"Network data error: {e}")
    
    def start_mining(self):
        if self.mining:
            return
            
        self.mining = True
        self.start_time = time.time()
        self.stats.update({
            'hash_rate': 0,
            'total_hashes': 0,
            'accepted_shares': 0,
            'rejected_shares': 0,
            'uptime': 0
        })
        self.hash_history = []
        self.last_shares = []
        
        # Запуск майнинга
        for i in range(2):
            thread = threading.Thread(target=self.mine_worker, daemon=True)
            thread.start()
            
        # Обновление статистики
        stats_thread = threading.Thread(target=self.stats_worker, daemon=True)
        stats_thread.start()
        
        # Обновление сетевых данных
        network_thread = threading.Thread(target=self.network_worker, daemon=True)
        network_thread.start()
        
        print("🚀 NerdMiner v2 started!")
    
    def stop_mining(self):
        self.mining = False
        print("⏹️ NerdMiner stopped!")
    
    def mine_worker(self):
        worker_id = threading.get_ident()
        local_hashes = 0
        last_stat_time = time.time()
        
        while self.mining:
            # Имитация реального майнинга
            data = f"nerdminer{worker_id}{time.time()}{random.randint(0, 1000000000)}"
            hash_result = hashlib.sha256(data.encode()).hexdigest()
            
            self.stats['total_hashes'] += 1
            local_hashes += 1
            
            # Найден шар (каждые ~1000 хешей)
            if random.random() < 0.001:
                self.stats['accepted_shares'] += 1
                self.last_shares.append({
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'diff': random.randint(1000, 10000)
                })
                if len(self.last_shares) > 5:
                    self.last_shares.pop(0)
            
            # Обновление хешрейта каждую секунду
            current_time = time.time()
            if current_time - last_stat_time >= 1.0:
                self.stats['hash_rate'] = local_hashes
                local_hashes = 0
                last_stat_time = current_time
            
            time.sleep(0.001)
    
    def stats_worker(self):
        while self.mining:
            self.stats['uptime'] = time.time() - self.start_time
            self.stats['temperature'] = random.randint(40, 60)
            
            # Добавление в историю для графика
            self.hash_history.append(self.stats['hash_rate'])
            if len(self.hash_history) > 30:
                self.hash_history.pop(0)
            
            time.sleep(1)
    
    def network_worker(self):
        while self.mining:
            self.update_network_data()
            time.sleep(60)  # Обновление каждую минуту
    
    def get_efficiency(self):
        total = self.stats['accepted_shares'] + self.stats['rejected_shares']
        if total == 0:
            return "100%"
        eff = (self.stats['accepted_shares'] / total) * 100
        return f"{eff:.1f}%"
    
    def format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def generate_sparkline_data(self):
        """Генерация данных для спарклайна"""
        if not self.hash_history:
            return []
        
        max_val = max(self.hash_history)
        if max_val == 0:
            return [0] * len(self.hash_history)
        
        return [int((h / max_val) * 100) for h in self.hash_history]

class NerdMinerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.miner = kwargs.pop('miner')
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.serve_main_page()
        elif self.path == '/api/stats':
            self.serve_stats()
        elif self.path == '/api/start':
            self.miner.start_mining()
            self.send_json({'status': 'started'})
        elif self.path == '/api/stop':
            self.miner.stop_mining()
            self.send_json({'status': 'stopped'})
        else:
            super().do_GET()
    
    def serve_main_page(self):
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NerdMiner v2 - Android</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Courier New', monospace;
                    background: #0a0a0a;
                    color: #00ff00;
                    padding: 10px;
                    line-height: 1.4;
                }
                .container { max-width: 400px; margin: 0 auto; }
                .header { 
                    text-align: center; 
                    border-bottom: 1px solid #00ff00;
                    padding: 10px 0;
                    margin-bottom: 10px;
                }
                .stats { margin-bottom: 15px; }
                .stat-row { 
                    display: flex; 
                    justify-content: space-between;
                    margin-bottom: 5px;
                    font-size: 14px;
                }
                .sparkline {
                    height: 40px;
                    background: #001100;
                    margin: 10px 0;
                    position: relative;
                }
                .sparkline-line {
                    position: absolute;
                    bottom: 0;
                    width: 100%;
                    height: 100%;
                    stroke: #00ff00;
                    fill: none;
                    stroke-width: 2;
                }
                .controls {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                    margin: 15px 0;
                }
                button {
                    background: #003300;
                    color: #00ff00;
                    border: 1px solid #00ff00;
                    padding: 10px;
                    font-family: 'Courier New';
                    cursor: pointer;
                }
                button:active { background: #005500; }
                .shares { margin-top: 15px; }
                .share { 
                    font-size: 12px; 
                    margin-bottom: 3px;
                    color: #00cc00;
                }
                .status {
                    text-align: center;
                    padding: 5px;
                    margin: 10px 0;
                    background: #002200;
                    border: 1px solid #00ff00;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>NERDMINER v2</h2>
                    <div>ANDROID EDITION</div>
                </div>
                
                <div class="status" id="status">STOPPED</div>
                
                <div class="stats" id="stats">
                    <!-- Stats will be loaded by JavaScript -->
                </div>
                
                <div class="sparkline" id="sparkline">
                    <svg viewBox="0 0 100 40" class="sparkline-line" id="sparkline-svg"></svg>
                </div>
                
                <div class="controls">
                    <button onclick="startMining()">START</button>
                    <button onclick="stopMining()">STOP</button>
                </div>
                
                <div class="shares" id="shares">
                    <div class="share">No shares yet</div>
                </div>
            </div>

            <script>
                let updateInterval;
                
                function updateStats() {
                    fetch('/api/stats')
                        .then(r => r.json())
                        .then(data => {
                            // Update status
                            document.getElementById('status').textContent = 
                                data.mining ? 'MINING 🟢' : 'STOPPED 🔴';
                            
                            // Update stats
                            document.getElementById('stats').innerHTML = `
                                <div class="stat-row">
                                    <span>Hash Rate:</span>
                                    <span>${data.hash_rate.toLocaleString()} H/s</span>
                                </div>
                                <div class="stat-row">
                                    <span>Total Hashes:</span>
                                    <span>${data.total_hashes.toLocaleString()}</span>
                                </div>
                                <div class="stat-row">
                                    <span>Shares:</span>
                                    <span>A: ${data.accepted_shares} R: ${data.rejected_shares}</span>
                                </div>
                                <div class="stat-row">
                                    <span>Efficiency:</span>
                                    <span>${data.efficiency}</span>
                                </div>
                                <div class="stat-row">
                                    <span>Uptime:</span>
                                    <span>${data.uptime}</span>
                                </div>
                                <div class="stat-row">
                                    <span>Block:</span>
                                    <span>${data.block_height.toLocaleString()}</span>
                                </div>
                                <div class="stat-row">
                                    <span>Difficulty:</span>
                                    <span>${data.difficulty}</span>
                                </div>
                                <div class="stat-row">
                                    <span>BTC Price:</span>
                                    <span>$${data.btc_price.toLocaleString()}</span>
                                </div>
                            `;
                            
                            // Update sparkline
                            updateSparkline(data.sparkline);
                            
                            // Update shares
                            if (data.last_shares.length > 0) {
                                document.getElementById('shares').innerHTML = 
                                    data.last_shares.map(share => 
                                        `<div class="share">${share.time} - Diff: ${share.diff}</div>`
                                    ).join('');
                            }
                        });
                }
                
                function updateSparkline(data) {
                    if (data.length === 0) return;
                    
                    const svg = document.getElementById('sparkline-svg');
                    let path = 'M0,40 ';
                    
                    data.forEach((value, index) => {
                        const x = (index / (data.length - 1)) * 100;
                        const y = 40 - (value / 100) * 40;
                        path += `L${x},${y} `;
                    });
                    
                    svg.innerHTML = `<path d="${path}" />`;
                }
                
                function startMining() {
                    fetch('/api/start').then(() => {
                        if (!updateInterval) {
                            updateInterval = setInterval(updateStats, 2000);
                        }
                    });
                }
                
                function stopMining() {
                    fetch('/api/stop');
                }
                
                // Start updating stats
                updateInterval = setInterval(updateStats, 2000);
                updateStats();
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_stats(self):
        stats = {
            'mining': self.miner.mining,
            'hash_rate': self.miner.stats['hash_rate'],
            'total_hashes': self.miner.stats['total_hashes'],
            'accepted_shares': self.miner.stats['accepted_shares'],
            'rejected_shares': self.miner.stats['rejected_shares'],
            'uptime': self.miner.format_time(self.miner.stats['uptime']),
            'efficiency': self.miner.get_efficiency(),
            'block_height': self.miner.stats['block_height'],
            'difficulty': self.miner.stats['difficulty'],
            'btc_price': self.miner.stats['btc_price'],
            'sparkline': self.miner.generate_sparkline_data(),
            'last_shares': self.miner.last_shares
        }
        self.send_json(stats)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def main():
    miner = NerdMinerV2()
    
    # Запуск веб-сервера
    port = 8080
    handler = lambda *args: NerdMinerHandler(*args, miner=miner)
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🌐 NerdMiner v2 Web Interface: http://localhost:{port}")
        print("📱 Open this URL in your phone's browser")
        print("🎛️ Controls: START/STOP mining from web interface")
        
        # Автозапуск браузера (если возможно)
        try:
            import webbrowser
            webbrowser.open(f"http://localhost:{port}")
        except:
            pass
            
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 NerdMiner stopped!")

if __name__ == "__main__":
    main()