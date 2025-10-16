"""
Модуль мониторинга производительности
"""

import time
import psutil
import logging
from typing import Dict, List
from dataclasses import dataclass
from collections import deque


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    response_time: float = 0.0


class PerformanceMonitor:
    """Класс для мониторинга производительности системы"""
    
    def __init__(self, max_history: int = 100):
        self.logger = logging.getLogger(__name__)
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.response_times: deque = deque(maxlen=50)
        self.start_time = time.time()
    
    def collect_metrics(self) -> PerformanceMetrics:
        """Собирает текущие метрики производительности"""
        try:
            process = psutil.Process()
            
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=process.cpu_percent(),
                memory_percent=process.memory_percent(),
                memory_mb=process.memory_info().rss / 1024 / 1024
            )
            
            self.metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора метрик: {e}")
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_mb=0.0
            )
    
    def record_response_time(self, start_time: float, end_time: float):
        """Записывает время отклика"""
        response_time = end_time - start_time
        self.response_times.append(response_time)
        
        if self.metrics_history:
            self.metrics_history[-1].response_time = response_time
    
    def get_average_response_time(self) -> float:
        """Возвращает среднее время отклика"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_system_stats(self) -> Dict:
        """Возвращает статистику системы"""
        try:
            current_metrics = self.collect_metrics()
            uptime = time.time() - self.start_time
            
            return {
                "uptime_seconds": uptime,
                "uptime_formatted": self._format_uptime(uptime),
                "current_cpu": current_metrics.cpu_percent,
                "current_memory_mb": current_metrics.memory_mb,
                "current_memory_percent": current_metrics.memory_percent,
                "average_response_time": self.get_average_response_time(),
                "total_requests": len(self.response_times),
                "system_cpu": psutil.cpu_percent(interval=1),
                "system_memory": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def _format_uptime(self, seconds: float) -> str:
        """Форматирует время работы"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_performance_report(self) -> str:
        """Генерирует отчет о производительности"""
        stats = self.get_system_stats()
        
        if not stats:
            return "Статистика недоступна"
        
        report = f"""
📊 Отчет о производительности:
• Время работы: {stats.get('uptime_formatted', 'N/A')}
• CPU процесса: {stats.get('current_cpu', 0):.1f}%
• Память процесса: {stats.get('current_memory_mb', 0):.1f} MB ({stats.get('current_memory_percent', 0):.1f}%)
• Среднее время отклика: {stats.get('average_response_time', 0):.2f}s
• Обработано запросов: {stats.get('total_requests', 0)}
• CPU системы: {stats.get('system_cpu', 0):.1f}%
• Память системы: {stats.get('system_memory', 0):.1f}%
• Диск: {stats.get('disk_usage', 0):.1f}%
        """.strip()
        
        return report
    
    def check_performance_alerts(self) -> List[str]:
        """Проверяет превышение пороговых значений производительности"""
        alerts = []
        stats = self.get_system_stats()
        
        if stats.get('current_memory_percent', 0) > 80:
            alerts.append("⚠️ Высокое потребление памяти процессом")
        
        if stats.get('system_memory', 0) > 90:
            alerts.append("⚠️ Критическое потребление памяти системой")
        
        if stats.get('system_cpu', 0) > 90:
            alerts.append("⚠️ Высокая загрузка CPU системы")
        
        if stats.get('average_response_time', 0) > 5.0:
            alerts.append("⚠️ Медленное время отклика")
        
        return alerts