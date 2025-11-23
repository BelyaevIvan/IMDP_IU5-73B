# hockey_model.py
# Имитационная модель работы хоккейной коробки
import simpy
import random

# Класс "Хоккейная коробка" для хранения статистики
class HockeyRink:
    def __init__(self):
        self.served_groups = 0
        self.rejected_groups = 0
        self.total_wait_time = 0.0
        self.total_game_time = 0.0
        self.queue_lengths = []  # для сбора статистики по длине очереди
        self.queue_times = []    # временные метки для queue_lengths
        self.utilization = 0.0

# Процесс: группа игроков приходит и пытается сыграть
def group_process(env, group_id, rink, rink_resource, waiting_room, params, stats):
    # Регистрируем факт прихода группы
    arrival_time = env.now
    
    # Проверяем, есть ли место в зоне ожидания (очереди)
    if len(waiting_room.items) >= params['K']:
        # Мест нет - отказ
        stats.rejected_groups += 1
        print(f"⛔ Группа {group_id} получила ОТКАЗ в момент времени {env.now:.2f} мин. (Очередь: {len(waiting_room.items)}/{params['K']})")
        return
    
    # Есть место - встаем в очередь
    print(f"👥 Группа {group_id} встала в ОЧЕРЕДЬ в момент времени {env.now:.2f} мин. (Очередь: {len(waiting_room.items)+1}/{params['K']})")
    
    # Запоминаем длину очереди ДО нашего прихода (для статистики)
    stats.queue_lengths.append(len(waiting_room.items))
    stats.queue_times.append(env.now)
    
    # Помещаем группу в зону ожидания
    with waiting_room.put({'id': group_id, 'arrival_time': arrival_time}) as wait_req:
        yield wait_req
        
        # Ждем, пока коробка освободится и занимаем ее
        wait_start = env.now
        with rink_resource.request() as req:
            yield req
            # Выходим из очереди
            yield waiting_room.get()
            # Расчет времени ожидания
            wait_time = env.now - wait_start
            stats.total_wait_time += wait_time
            
            # Начинаем играть
            print(f"🏒 Группа {group_id} начала ИГРАТЬ в момент времени {env.now:.2f} мин. (Ожидала: {wait_time:.2f} мин.)")
            
            # Генерируем время игры
            game_time = random.uniform(params['A'] - params['B'], params['A'] + params['B'])
            stats.total_game_time += game_time
            yield env.timeout(game_time)
            
            # Завершаем игру
            stats.served_groups += 1
            print(f"✅ Группа {group_id} закончила игру в момент времени {env.now:.2f} мин. (Играла: {game_time:.2f} мин.)")

# Процесс-генератор: создает новые группы игроков
def group_generator(env, rink, rink_resource, waiting_room, params, stats):
    group_id = 0
    while True:
        # Ждем случайное время до прихода следующей группы
        interval = random.uniform(params['N'] - params['M'], params['N'] + params['M'])
        yield env.timeout(interval)
        
        group_id += 1
        # Запускаем процесс для новой группы
        env.process(group_process(env, group_id, rink, rink_resource, waiting_room, params, stats))

# Основная функция запуска моделирования
def run_simulation(params):
    # Создаем среду SimPy
    env = simpy.Environment()
    
    # Инициализируем сбор статистики
    stats = HockeyRink()
    
    # Создаем ресурсы:
    # 1) Хоккейная коробка (емкость 1 группа)
    rink_resource = simpy.Resource(env, capacity=1)
    # 2) Зона ожидания (очередь) с ограниченной емкостью
    waiting_room = simpy.Store(env, capacity=params['K'])
    
    # Запускаем процесс генерации групп
    env.process(group_generator(env, stats, rink_resource, waiting_room, params, stats))
    
    # Запускаем моделирование на заданное время (переводим часы в минуты)
    simulation_time_minutes = params['T'] * 60
    env.run(until=simulation_time_minutes)
    
    # Расчет итоговых показателей
    stats.utilization = (stats.total_game_time / simulation_time_minutes) * 100
    
    # Вывод результатов
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ")
    print("="*60)
    print(f"Общее время моделирования: {params['T']} час. ({simulation_time_minutes} мин.)")
    print(f"Количество обслуженных групп: {stats.served_groups}")
    print(f"Количество отклоненных групп: {stats.rejected_groups}")
    print(f"Коэффициент загрузки коробки: {stats.utilization:.2f}%")
    print(f"Среднее время ожидания в очереди: {stats.total_wait_time/stats.served_groups if stats.served_groups > 0 else 0:.2f} мин.")
    
    return stats

# Параметры моделирования (можно менять)
if __name__ == "__main__":
    # Параметры по умолчанию (аналогичны примеру с грузовиками)
    params = {
        'N': 5,    # Средний интервал между приходом групп
        'M': 4,    # Разброс интервала
        'A': 12,   # Среднее время игры
        'B': 8,    # Разброс времени игры
        'K': 5,    # Максимальный размер очереди
        'T': 10    # Время моделирования в часах
    }
    
    # Запуск моделирования
    results = run_simulation(params)