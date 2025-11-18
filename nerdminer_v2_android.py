#!/usr/bin/env python3
import time
import hashlib
import random
import requests
import threading
import sys
import os
from datetime import datetime

class TerminalNerdMiner:
    def __init__(self):
        self.mining = False
        self.hash_rate = 0
        self.total_hashes = 0
        self.accepted_shares = 0
        self.uptime = 0
        self.start_time = 0
        self.temperature = 42
        self.screen_on = True
        
        # Управление кнопками (как в оригинале)
        self.power_last_press = 0
        self.volume_last_press = 0
        self.volume_press_count = 0
        
        # Сетевые данные
        self.btc_price = 0
        self.block_height = 0
        self.difficulty = "0"
        self.network_hashrate = "0 H/s"
        self.last_update = 0
        
        # График
        self.hash_history = []
        
        # Цвета для терминала
        self.COLORS = {
            'green': '\033[92m',
            'red': '\033[91m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'gray': '\033[90m',
            'reset': '\033[0m',
            'bold': '\033[1m'
        }
        
    def color_text(self, text, color):
        """Добавляет цвет к тексту"""
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def clear_screen(self):
        """Очистка экрана"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def fetch_btc_price(self):
        """Получение цены BTC"""
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.btc_price = data['bitcoin']['usd']
                return True
        except:
            pass
        return False
    
    def fetch_blockchain_data(self):
        """Получение данных блокчейна"""
        try:
            # Высота блока
            response = requests.get("https://blockchain.info/q/getblockcount", timeout=10)
            if response.status_code == 200:
                self.block_height = int(response.text)
            
            # Сложность
            response = requests.get("https://blockchain.info/q/getdifficulty", timeout=10)
            if response.status_code == 200:
                diff = float(response.text)
                
                # Форматирование сложности
                if diff >= 1e12:
                    self.difficulty = f"{diff/1e12:.2f}T"
                elif diff >= 1e9:
                    self.difficulty = f"{diff/1e9:.2f}G"
                else:
                    self.difficulty = f"{diff/1e6:.2f}M"
                
                # Расчет сетевого хешрейта
                network_hash = diff * 2**32 / 600
                if network_hash >= 1e18:
                    self.network_hashrate = f"{network_hash/1e18:.2f} EH/s"
                elif network_hash >= 1e15:
                    self.network_hashrate = f"{network_hash/1e15:.2f} PH/s"
                else:
                    self.network_hashrate = f"{network_hash/1e12:.2f} TH/s"
                    
            return True
        except:
            pass
        return False
    
    def update_network_data(self):
        """Обновление всех сетевых данных"""
        if time.time() - self.last_update > 60:
            self.fetch_btc_price()
            self.fetch_blockchain_data()
            self.last_update = time.time()
    
    def handle_power_button(self):
        """Обработка кнопки POWER - экран вкл/выкл"""
        current_time = time.time()
        
        # Одинарное нажатие - переключаем экран
        if current_time - self.power_last_press > 0.5:
            self.screen_on = not self.screen_on
            if not self.screen_on:
                self.clear_screen()
                print(self.color_text("📱 Screen OFF - Press P to turn on", "yellow"))
            
        self.power_last_press = current_time
        
    def handle_volume_button(self):
        """Обработка кнопки VOLUME - старт/стоп майнинг"""
        current_time = time.time()
        
        # Сбрасываем счетчик если прошло больше 1 секунды
        if current_time - self.volume_last_press > 1.0:
            self.volume_press_count = 0
            
        self.volume_press_count += 1
        self.volume_last_press = current_time
        
        # Двойное нажатие = старт/стоп майнинг
        if self.volume_press_count == 2:
            if self.mining:
                self.stop_mining()
            else:
                self.start_mining()
            self.volume_press_count = 0
    
    def start_mining(self):
        """Запуск майнинга"""
        if not self.screen_on:
            self.screen_on = True
            
        self.mining = True
        self.start_time = time.time()
        
        mining_thread = threading.Thread(target=self.mining_worker, daemon=True)
        mining_thread.start()
        return True
    
    def stop_mining(self):
        """Остановка майнинга"""
        self.mining = False
        self.hash_rate = 0
    
    def mining_worker(self):
        """Рабочий поток майнинга"""
        local_hashes = 0
        last_stat_time = time.time()
        
        while self.mining:
            # Имитация майнинга SHA-256
            data = f"nerdminer{time.time()}{random.randint(0, 1000000)}"
            hash_result = hashlib.sha256(data.encode()).hexdigest()
            
            self.total_hashes += 1
            local_hashes += 1
            
            # Обновление хешрейта каждую секунду
            current_time = time.time()
            if current_time - last_stat_time >= 1.0:
                self.hash_rate = local_hashes
                local_hashes = 0
                last_stat_time = current_time
                
                # Обновляем историю для графика
                self.hash_history.append(self.hash_rate)
                if len(self.hash_history) > 20:
                    self.hash_history.pop(0)
            
            # Случайное нахождение шара
            if random.random() < 0.001:
                self.accepted_shares += 1
                
            time.sleep(0.003)
    
    def draw_graph(self, width=40, height=8):
        """Рисует ASCII график хешрейта"""
        if not self.hash_history:
            return " " * width + "\n" * height
        
        max_val = max(self.hash_history) if max(self.hash_history) > 0 else 1
        graph = []
        
        for h in range(height, 0, -1):
            line = ""
            threshold = (h / height) * max_val
            
            for value in self.hash_history:
                if value >= threshold:
                    line += "█"
                else:
                    line += " "
            
            # Обрезаем или дополняем до нужной ширины
            if len(line) > width:
                line = line[-width:]
            else:
                line = " " * (width - len(line)) + line
                
            graph.append(line)
        
        return "\n".join(graph)
    
    def format_hashrate(self, hashrate):
        """Форматирует хешрейт для отображения"""
        if hashrate >= 1000:
            return f"{hashrate/1000:.1f}k H/s"
        else:
            return f"{hashrate:.0f} H/s"
    
    def format_number(self, number):
        """Форматирует большие числа"""
        if number >= 1e6:
            return f"{number/1e6:.1f}M"
        elif number >= 1e3:
            return f"{number/1e3:.1f}K"
        else:
            return f"{number:.0f}"
    
    def display_ui(self):
        """Отображает основной интерфейс"""
        if not self.screen_on:
            return
            
        self.clear_screen()
        
        # Заголовок
        print(self.color_text("╔══════════════════════════════════════════════════╗", "green"))
        print(self.color_text("║              NERDMINER v2 - TERMINAL            ║", "green"))
        print(self.color_text("╚══════════════════════════════════════════════════╝", "green"))
        print()
        
        # Статус майнинга
        status_color = "green" if self.mining else "red"
        status_text = "MINING" if self.mining else "STOPPED"
        print(f"{self.color_text('STATUS:', 'bold')} {self.color_text(status_text, status_color)}")
        
        # Основная статистика
        print(f"{self.color_text('HASHRATE:', 'bold')} {self.color_text(self.format_hashrate(self.hash_rate), 'cyan')}")
        print(f"{self.color_text('SHARES:', 'bold')} {self.color_text(str(self.accepted_shares), 'white')}")
        print(f"{self.color_text('TOTAL HASHES:', 'bold')} {self.color_text(self.format_number(self.total_hashes), 'white')}")
        
        # Аптайм
        if self.mining:
            self.uptime = time.time() - self.start_time
            hours = int(self.uptime // 3600)
            minutes = int((self.uptime % 3600) // 60)
            seconds = int(self.uptime % 60)
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            uptime_str = "00:00:00"
        
        print(f"{self.color_text('UPTIME:', 'bold')} {self.color_text(uptime_str, 'yellow')}")
        print(f"{self.color_text('TEMPERATURE:', 'bold')} {self.color_text(f'{self.temperature}°C', 'magenta')}")
        print()
        
        # График хешрейта
        print(self.color_text("HASHRATE GRAPH:", "bold"))
        graph = self.draw_graph()
        print(self.color_text(graph, "green"))
        print()
        
        # Сетевые данные
        print(self.color_text("NETWORK DATA:", "bold"))
        print(f"{self.color_text('BLOCK:', 'gray')} {self.color_text(f'{self.block_height:,}', 'white')}")
        print(f"{self.color_text('BTC PRICE:', 'gray')} {self.color_text(f'${self.btc_price:,.0f}', 'yellow')}")
        print(f"{self.color_text('DIFFICULTY:', 'gray')} {self.color_text(self.difficulty, 'white')}")
        print(f"{self.color_text('NETWORK HASHRATE:', 'gray')} {self.color_text(self.network_hashrate, 'cyan')}")
        print()
        
        # Управление (как в оригинале)
        print(self.color_text("PHONE BUTTON EMULATION:", "bold"))
        print(self.color_text("[P] Power Button (Screen ON/OFF)", "gray"))
        print(self.color_text("[V] Volume Button x2 (Start/Stop Mining)", "gray"))
        print(self.color_text("[R] Refresh Network Data", "gray"))
        print(self.color_text("[Q] Quit", "gray"))
        print()
        
        # Обновление температуры
        if self.mining:
            base_temp = 40
            load_factor = min(self.hash_rate / 50000, 1.0)
            self.temperature = base_temp + int(load_factor * 20)
        else:
            self.temperature = max(35, self.temperature - 1)
    
    def run(self):
        """Основной цикл программы"""
        print(self.color_text("Initializing NerdMiner...", "yellow"))
        
        # Первоначальная загрузка данных
        self.update_network_data()
        
        # Запускаем обновление сетевых данных в фоне
        def network_updater():
            while True:
                self.update_network_data()
                time.sleep(30)
        
        network_thread = threading.Thread(target=network_updater, daemon=True)
        network_thread.start()
        
        # Основной цикл
        try:
            while True:
                if self.screen_on:
                    self.display_ui()
                
                # Неблокирующий ввод
                if sys.platform != 'win32':
                    import select
                    import tty
                    import termios
                    
                    old_settings = termios.tcgetattr(sys.stdin)
                    try:
                        tty.setraw(sys.stdin.fileno())
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1).lower()
                            
                            if key == 'p':  # Power button
                                self.handle_power_button()
                            elif key == 'v':  # Volume button
                                self.handle_volume_button()
                            elif key == 'r':  # Refresh
                                self.update_network_data()
                            elif key == 'q':  # Quit
                                break
                                
                    finally:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                else:
                    # Для Windows
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode().lower()
                        if key == 'p':
                            self.handle_power_button()
                        elif key == 'v':
                            self.handle_volume_button()
                        elif key == 'r':
                            self.update_network_data()
                        elif key == 'q':
                            break
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print(self.color_text("\nShutting down NerdMiner...", "yellow"))
        finally:
            self.stop_mining()
            print(self.color_text("NerdMiner stopped.", "red"))

if __name__ == "__main__":
    miner = TerminalNerdMiner()
    miner.run()
