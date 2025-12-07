
import simpy
import random

# Класс "Хоккейная коробка" для хранения статистики
class HockeyRink:
    def __init__(self):
        self.served_groups = 0
        self.rejected_groups = 0
        self.total_wait_time = 0.0
        self.total_game_time = 0.0
        self.total_ice_resurfacing_time = 0.0  # общее время заливки льда
        self.bad_ice_time = 0.0  # время катания на плохом льду
        self.ice_resurfacing_count = 0  # количество заливок льда
        self.queue_lengths = []  # для сбора статистики по длине очереди
        self.queue_times = []    # временные метки для queue_lengths
        self.utilization = 0.0
        self.ice_resurfacing_wait_times = []  # время ожидания заливочной машины
        self.last_resurfacing_time = 0.0  # время последней заливки
        self.ice_quality_times = []  # качество льда во времени (0-1)

# Процесс: заливка льда
def ice_resurfacing_process(env, rink_resource, params, stats):
    while True:
        # Ждем S часов между заливками
        yield env.timeout(params['S'] * 60)  # переводим часы в минуты
        
        # Фиксируем время, когда лед стал "плохим"
        ice_became_bad_time = env.now
        
        print(f"🕒 Время заливки льда! Лед стал 'плохим' в {env.now:.2f} мин.")
        
        # Запоминаем, что начался период "плохого" льда
        stats.last_resurfacing_time = ice_became_bad_time
        
        # Запрашиваем доступ к коробке для заливки
        wait_start = env.now
        with rink_resource.request(priority=0) as req:  # высокий приоритет (0 - наивысший)
            # Ждем, пока коробка освободится
            yield req
            wait_time = env.now - wait_start
            stats.ice_resurfacing_wait_times.append(wait_time)
            
            # Если была игра, которая продолжалась на "плохом" льду
            if wait_time > 0:
                stats.bad_ice_time += wait_time
                print(f"⚠️  Игра на 'плохом' льду длилась {wait_time:.2f} мин.")
            
            # Начинаем заливку льда
            print(f"🧊 Начинаем заливку льда в {env.now:.2f} мин. (ждали: {wait_time:.2f} мин.)")
            
            # Время заливки льда
            resurfacing_time = params['L']
            yield env.timeout(resurfacing_time)
            
            # Обновляем статистику
            stats.total_ice_resurfacing_time += resurfacing_time
            stats.ice_resurfacing_count += 1
            print(f"✅ Заливка льда завершена в {env.now:.2f} мин. (длилась: {resurfacing_time} мин.)")

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
        with rink_resource.request(priority=1) as req:  # обычный приоритет для групп
            yield req
            # Выходим из очереди
            yield waiting_room.get()
            # Расчет времени ожидания
            wait_time = env.now - wait_start
            stats.total_wait_time += wait_time
            
            # Проверяем, началась ли игра на "плохом" льду
            ice_quality_start = 1.0  # идеальный лед = 1.0
            time_since_last_resurfacing = env.now - stats.last_resurfacing_time
            resurfacing_interval = params['S'] * 60
            
            if time_since_last_resurfacing > resurfacing_interval:
                # Лед уже "плохой", но игра еще не закончилась
                ice_quality_start = max(0.1, 1.0 - (time_since_last_resurfacing - resurfacing_interval) / (resurfacing_interval * 2))
                print(f"⚠️  Группа {group_id} начинает игру на льду качества {ice_quality_start:.2f}")
            
            # Начинаем играть
            print(f"🏒 Группа {group_id} начала ИГРАТЬ в момент времени {env.now:.2f} мин. (Ожидала: {wait_time:.2f} мин.)")
            
            # Генерируем время игры (защита от отрицательных значений)
            min_game_time = max(0.1, params['A'] - params['B'])
            max_game_time = params['A'] + params['B']
            game_time = random.uniform(min_game_time, max_game_time)
            stats.total_game_time += game_time
            
            # Отслеживаем качество льда во время игры
            game_end_time = env.now + game_time
            while env.now < game_end_time:
                # Рассчитываем текущее качество льда
                time_since_resurfacing = env.now - stats.last_resurfacing_time
                
                if time_since_resurfacing > resurfacing_interval:
                    # Лед "плохой"
                    quality = max(0.1, 1.0 - (time_since_resurfacing - resurfacing_interval) / (resurfacing_interval * 2))
                    stats.ice_quality_times.append((env.now, quality))
                    
                    # Если качество льда ниже 0.5, считаем это "плохим" льдом
                    if quality < 0.5:
                        # Увеличиваем время шага моделирования для расчета
                        step = min(1.0, game_end_time - env.now)  # шаг 1 минута или меньше
                        stats.bad_ice_time += step
                else:
                    # Лед хороший
                    quality = 1.0
                    stats.ice_quality_times.append((env.now, quality))
                
                # Ждем небольшой шаг времени
                yield env.timeout(min(1.0, game_end_time - env.now))
            
            # Завершаем игру
            stats.served_groups += 1
            print(f"✅ Группа {group_id} закончила игру в момент времени {env.now:.2f} мин. (Играла: {game_time:.2f} мин.)")

# Процесс-генератор: создает новые группы игроков
def group_generator(env, rink, rink_resource, waiting_room, params, stats):
    group_id = 0
    while True:
        # Ждем случайное время до прихода следующей группы (защита от отрицательных значений)
        min_interval = max(0.1, params['N'] - params['M'])
        max_interval = params['N'] + params['M']
        interval = random.uniform(min_interval, max_interval)
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
    # 1) Хоккейная коробка (емкость 1 группа) с поддержкой приоритетов
    rink_resource = simpy.PriorityResource(env, capacity=1)
    # 2) Зона ожидания (очередь) с ограниченной емкостью
    waiting_room = simpy.Store(env, capacity=params['K'])
    
    # Запускаем процесс генерации групп
    env.process(group_generator(env, stats, rink_resource, waiting_room, params, stats))
    
    # Запускаем процесс заливки льда
    env.process(ice_resurfacing_process(env, rink_resource, params, stats))
    
    # Запускаем моделирование на заданное время (переводим часы в минуты)
    simulation_time_minutes = params['T'] * 60
    env.run(until=simulation_time_minutes)
    
    # Расчет итоговых показателей (защита от деления на ноль)
    if simulation_time_minutes > 0:
        stats.utilization = ((stats.total_game_time + stats.total_ice_resurfacing_time) / simulation_time_minutes) * 100
    else:
        stats.utilization = 0
    
    # Расчет доли времени с плохим льдом
    if simulation_time_minutes > 0:
        bad_ice_percentage = (stats.bad_ice_time / simulation_time_minutes) * 100
    else:
        bad_ice_percentage = 0
    
    # Вывод результатов
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ")
    print("="*60)
    print(f"Общее время моделирования: {params['T']} час. ({simulation_time_minutes} мин.)")
    print(f"Количество обслуженных групп: {stats.served_groups}")
    print(f"Количество отклоненных групп: {stats.rejected_groups}")
    print(f"Коэффициент загрузки коробки: {stats.utilization:.2f}%")
    print(f"Количество заливок льда: {stats.ice_resurfacing_count}")
    print(f"Общее время заливки льда: {stats.total_ice_resurfacing_time:.2f} мин.")
    print(f"Время катания на 'плохом' льду: {stats.bad_ice_time:.2f} мин. ({bad_ice_percentage:.2f}%)")
    
    if stats.served_groups > 0:
        avg_wait = stats.total_wait_time / stats.served_groups
        print(f"Среднее время ожидания в очереди: {avg_wait:.2f} мин.")
    else:
        print("Среднее время ожидания: нет данных")
    
    if stats.ice_resurfacing_count > 0:
        avg_resurfacing_wait = sum(stats.ice_resurfacing_wait_times) / len(stats.ice_resurfacing_wait_times)
        print(f"Среднее время ожидания заливочной машины: {avg_resurfacing_wait:.2f} мин.")
    
    return stats

# Параметры моделирования (можно менять)
if __name__ == "__main__":
    # Параметры по умолчанию
    params = {
        'N': 5,    # Средний интервал между приходом групп
        'M': 4,    # Разброс интервала
        'A': 12,   # Среднее время игры
        'B': 8,    # Разброс времени игры
        'K': 5,    # Максимальный размер очереди
        'T': 10,   # Время моделирования в часах
        'S': 2,    # Интервал между заливками льда (часы)
        'L': 30    # Время заливки льда (минуты)
    }
    
    # Запуск моделирования
    results = run_simulation(params)