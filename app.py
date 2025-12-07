# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
import contextlib
from model import run_simulation, HockeyRink

# Настройка страницы
st.set_page_config(
    page_title="Моделирование хоккейной коробки",
    page_icon="🏒",
    layout="wide"
)

# Заголовок приложения
st.title("🏒 Моделирование работы хоккейной коробки с заливкой льда")
st.markdown("---")

# Боковая панель с параметрами
st.sidebar.header("⚙️ Параметры моделирования")

# Основные параметры системы
st.sidebar.subheader("Основные параметры")
T = st.sidebar.number_input("Время моделирования (T, часы)", min_value=1, max_value=100, value=10)
N = st.sidebar.number_input("Средний интервал между группами (N, мин)", min_value=1, max_value=60, value=5, help="Должен быть ≥ M")
M = st.sidebar.number_input("Разброс интервала (M, мин)", min_value=0, max_value=20, value=4, help="Должен быть ≤ N")
A = st.sidebar.number_input("Среднее время игры (A, мин)", min_value=1, max_value=120, value=12, help="Должно быть ≥ B")
B = st.sidebar.number_input("Разброс времени игры (B, мин)", min_value=0, max_value=30, value=8, help="Должен быть ≤ A")
K = st.sidebar.number_input("Максимальный размер очереди (K, групп)", min_value=1, max_value=20, value=5)

# Параметры заливки льда
st.sidebar.subheader("Параметры заливки льда")
S = st.sidebar.number_input("Интервал между заливками (S, часы)", min_value=0.5, max_value=24.0, value=2.0, step=0.5, 
                           help="Через сколько часов требуется новая заливка льда")
L = st.sidebar.number_input("Время заливки льда (L, минуты)", min_value=5, max_value=120, value=30,
                           help="Сколько минут занимает процедура заливки льда")

# Дополнительные настройки
st.sidebar.header("📊 Настройки отображения")
show_logs = st.sidebar.checkbox("Показывать логи моделирования", value=False)
show_detailed_stats = st.sidebar.checkbox("Показать расширенную статистику", value=True)
show_ice_quality = st.sidebar.checkbox("Показать график качества льда", value=True)

# ВАЛИДАЦИЯ ПАРАМЕТРОВ
validation_errors = []

# Проверка основных параметров
if M > N:
    validation_errors.append(f"❌ Ошибка: Разброс интервала (M={M}) не может быть больше среднего интервала (N={N})")

if B > A:
    validation_errors.append(f"❌ Ошибка: Разброс времени игры (B={B}) не может быть больше среднего времени игры (A={A})")

if N <= 0:
    validation_errors.append("❌ Ошибка: Средний интервал (N) должен быть положительным")

if A <= 0:
    validation_errors.append("❌ Ошибка: Среднее время игры (A) должно быть положительным")

if M < 0:
    validation_errors.append("❌ Ошибка: Разброс интервала (M) не может быть отрицательным")

if B < 0:
    validation_errors.append("❌ Ошибка: Разброс времени игры (B) не может быть отрицательным")

if K <= 0:
    validation_errors.append("❌ Ошибка: Размер очереди (K) должен быть положительным")

if T <= 0:
    validation_errors.append("❌ Ошибка: Время моделирования (T) должно быть положительным")

# Проверка параметров заливки льда
if S <= 0:
    validation_errors.append("❌ Ошибка: Интервал заливки льда (S) должен быть положительным")

if L <= 0:
    validation_errors.append("❌ Ошибка: Время заливки льда (L) должно быть положительным")

# Проверка разумности интервалов
if L > S * 60:
    validation_errors.append(f"⚠️ Предупреждение: Время заливки ({L} мин) больше интервала ({S} ч = {S*60} мин)")

if L > A * 3:
    validation_errors.append(f"⚠️ Предупреждение: Время заливки ({L} мин) значительно больше среднего времени игры ({A} мин)")

# Показываем ошибки, если они есть
if validation_errors:
    st.sidebar.error("Обнаружены ошибки в параметрах:")
    for error in validation_errors:
        st.sidebar.write(error)
    
    # Блокируем кнопку запуска
    st.sidebar.button("🚀 Запустить моделирование", type="primary", disabled=True)
    
    # Показываем подсказки по правильным значениям
    st.sidebar.markdown("---")
    st.sidebar.info("**Рекомендации по параметрам:**")
    st.sidebar.write("• M ≤ N (разброс ≤ среднего интервала)")
    st.sidebar.write("• B ≤ A (разброс ≤ среднего времени игры)")
    st.sidebar.write("• Все значения должны быть положительными")
    st.sidebar.write("• L должно быть разумным относительно S и A")
    
else:   
    # Кнопка запуска моделирования
    if st.sidebar.button("🚀 Запустить моделирование", type="primary"):
        
        # Показываем индикатор загрузки
        with st.spinner("Идет моделирование..."):
            # Захватываем вывод для логов
            log_output = io.StringIO()
            
            with contextlib.redirect_stdout(log_output):
                # Запускаем модель с выбранными параметрами
                params = {'N': N, 'M': M, 'A': A, 'B': B, 'K': K, 'T': T, 'S': S, 'L': L}
                results = run_simulation(params)
            
            logs = log_output.getvalue()
        
        # Основная область результатов - 6 колонок
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric(
                label="Обслуженных групп",
                value=results.served_groups,
                delta=f"+{results.served_groups}"
            )
        
        with col2:
            st.metric(
                label="Отклоненных групп",
                value=results.rejected_groups,
                delta=f"-{results.rejected_groups}",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                label="Загрузка коробки",
                value=f"{results.utilization:.1f}%",
                delta=f"{results.utilization:.1f}%"
            )
        
        with col4:
            total_groups = results.served_groups + results.rejected_groups
            rejection_rate = (results.rejected_groups / total_groups * 100) if total_groups > 0 else 0
            st.metric(
                label="Процент отказов",
                value=f"{rejection_rate:.1f}%",
                delta=f"{rejection_rate:.1f}%",
                delta_color="inverse"
            )
        
        with col5:
            bad_ice_percentage = (results.bad_ice_time / (T * 60)) * 100 if T > 0 else 0
            st.metric(
                label="Плохой лед",
                value=f"{bad_ice_percentage:.1f}%",
                delta=f"{results.bad_ice_time:.1f} мин",
                delta_color="inverse"
            )
        
        with col6:
            st.metric(
                label="Заливок льда",
                value=results.ice_resurfacing_count,
                delta=f"+{results.ice_resurfacing_count}"
            )
        
        # Визуализация результатов
        st.markdown("---")
        st.subheader("📊 Визуализация результатов")
        
        # Создаем данные для графиков - теперь 6 графиков (3x2)
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        ax1, ax2, ax3 = axes[0]
        ax4, ax5, ax6 = axes[1]
        
        # График 1: Распределение времени игры (без отрицательных значений)
        min_game_time = max(0.1, A - B)
        max_game_time = A + B
        game_times_example = np.random.uniform(min_game_time, max_game_time, 1000)
        ax1.hist(game_times_example, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_xlabel('Время игры (минуты)')
        ax1.set_ylabel('Частота')
        ax1.set_title('Распределение времени игры')
        ax1.grid(True, alpha=0.3)
        
        # График 2: Распределение интервалов между группами (без отрицательных значений)
        min_interval = max(0.1, N - M)
        max_interval = N + M
        intervals_example = np.random.uniform(min_interval, max_interval, 1000)
        ax2.hist(intervals_example, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_xlabel('Интервал между группами (минуты)')
        ax2.set_ylabel('Частота')
        ax2.set_title('Распределение интервалов прибытия')
        ax2.grid(True, alpha=0.3)
        
        # График 3: Соотношение обслуженных и отклоненных
        labels = ['Обслуженные', 'Отклоненные']
        sizes = [results.served_groups, results.rejected_groups]
        colors = ['#66b3ff', '#ff6666']
        
        if sum(sizes) > 0:
            ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax3.set_title('Соотношение обслуженных и отклоненных групп')
        else:
            ax3.text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Соотношение обслуженных и отклоненных групп')
        
        # График 4: Загрузка системы по типам
        total_time = T * 60
        game_time_pct = (results.total_game_time / total_time * 100) if total_time > 0 else 0
        resurfacing_time_pct = (results.total_ice_resurfacing_time / total_time * 100) if total_time > 0 else 0
        idle_time_pct = max(0, 100 - game_time_pct - resurfacing_time_pct)
        
        categories = ['Игры', 'Заливка', 'Простой']
        values = [game_time_pct, resurfacing_time_pct, idle_time_pct]
        colors_bar = ['#4CAF50', '#2196F3', '#E0E0E0']
        bars = ax4.bar(categories, values, color=colors_bar, alpha=0.7)
        ax4.set_ylabel('Процент времени (%)')
        ax4.set_title('Распределение времени работы коробки')
        ax4.set_ylim(0, 100)
        ax4.grid(True, alpha=0.3)
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{value:.1f}%', ha='center', va='bottom')
        
        # График 5: Время ожидания заливочной машины
        if hasattr(results, 'ice_resurfacing_wait_times') and results.ice_resurfacing_wait_times:
            wait_times = results.ice_resurfacing_wait_times
            ax5.hist(wait_times, bins=min(10, len(wait_times)), alpha=0.7, color='orange', edgecolor='black')
            ax5.set_xlabel('Время ожидания (минуты)')
            ax5.set_ylabel('Частота')
            ax5.set_title('Время ожидания заливочной машины')
            ax5.grid(True, alpha=0.3)
            
            if len(wait_times) > 0:
                avg_wait = np.mean(wait_times)
                ax5.axvline(avg_wait, color='red', linestyle='--', alpha=0.7, 
                           label=f'Среднее: {avg_wait:.1f} мин')
                ax5.legend()
        else:
            ax5.text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=ax5.transAxes)
            ax5.set_title('Время ожидания заливочной машины')
        
        # График 6: Соотношение качества льда
        bad_ice_pct = (results.bad_ice_time / total_time * 100) if total_time > 0 else 0
        good_ice_pct = 100 - bad_ice_pct
        
        ice_labels = ['Хороший лед', 'Плохой лед']
        ice_sizes = [good_ice_pct, bad_ice_pct]
        ice_colors = ['#66bb6a', '#ef5350']
        
        if total_time > 0:
            ax6.pie(ice_sizes, labels=ice_labels, colors=ice_colors, autopct='%1.1f%%', startangle=90)
            ax6.set_title('Соотношение качества льда')
        else:
            ax6.text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=ax6.transAxes)
            ax6.set_title('Соотношение качества льда')
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # График качества льда во времени
        if show_ice_quality and hasattr(results, 'ice_quality_times') and results.ice_quality_times:
            st.markdown("---")
            st.subheader("📈 Динамика качества льда во времени")
            
            # Подготовка данных
            times = [t for t, q in results.ice_quality_times]
            qualities = [q for t, q in results.ice_quality_times]
            
            # Ограничим количество точек для лучшей читаемости
            if len(times) > 500:
                step = len(times) // 500
                times = times[::step]
                qualities = qualities[::step]
            
            fig_ice, ax_ice = plt.subplots(figsize=(12, 4))
            ax_ice.plot(times, qualities, alpha=0.7, color='purple', linewidth=1)
            ax_ice.fill_between(times, 0, qualities, alpha=0.3, color='purple')
            ax_ice.set_xlabel('Время моделирования (минуты)')
            ax_ice.set_ylabel('Качество льда (0-1)')
            ax_ice.set_title('Изменение качества льда во времени')
            ax_ice.grid(True, alpha=0.3)
            ax_ice.set_ylim(0, 1.1)
            
            # Добавим горизонтальные линии для порогов
            ax_ice.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='Порог "плохого" льда (0.5)')
            ax_ice.axhline(y=0.8, color='y', linestyle='--', alpha=0.5, label='Среднее качество (0.8)')
            ax_ice.legend()
            
            st.pyplot(fig_ice)
        
        # Расширенная статистика
        if show_detailed_stats:
            st.markdown("---")
            st.subheader("📈 Детальная статистика")
            
            # Расчет дополнительных метрик
            total_groups = results.served_groups + results.rejected_groups
            rejection_rate = (results.rejected_groups / total_groups * 100) if total_groups > 0 else 0
            avg_wait_time = results.total_wait_time / results.served_groups if results.served_groups > 0 else 0
            efficiency = (results.served_groups / (T * 60)) * 60 if T > 0 else 0  # групп в час
            
            # Время работы разбитое по типам
            total_time_min = T * 60
            game_time_pct = (results.total_game_time / total_time_min * 100) if total_time_min > 0 else 0
            resurfacing_time_pct = (results.total_ice_resurfacing_time / total_time_min * 100) if total_time_min > 0 else 0
            idle_time_pct = max(0, 100 - game_time_pct - resurfacing_time_pct)
            bad_ice_pct = (results.bad_ice_time / total_time_min * 100) if total_time_min > 0 else 0
            
            # Основные метрики - 3 колонки
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Основные показатели:**")
                basic_stats = {
                    'Показатель': [
                        'Общее время моделирования',
                        'Всего поступило групп',
                        'Обслуженных групп', 
                        'Отклоненных групп',
                        'Процент отказов',
                        'Количество заливок'
                    ],
                    'Значение': [
                        f"{T} часов ({T*60} минут)",
                        f"{total_groups} групп",
                        f"{results.served_groups} групп",
                        f"{results.rejected_groups} групп", 
                        f"{rejection_rate:.2f}%",
                        f"{results.ice_resurfacing_count}"
                    ]
                }
                st.table(pd.DataFrame(basic_stats))
            
            with col2:
                st.markdown("**Временные характеристики:**")
                time_stats = {
                    'Показатель': [
                        'Общее время игр',
                        'Общее время заливки',
                        'Общее время ожидания групп',
                        'Время плохого льда',
                        'Среднее время ожидания',
                        'Среднее время игры'
                    ],
                    'Значение': [
                        f"{results.total_game_time:.1f} мин ({game_time_pct:.1f}%)",
                        f"{results.total_ice_resurfacing_time:.1f} мин ({resurfacing_time_pct:.1f}%)",
                        f"{results.total_wait_time:.1f} мин", 
                        f"{results.bad_ice_time:.1f} мин ({bad_ice_pct:.1f}%)",
                        f"{avg_wait_time:.2f} мин",
                        f"{results.total_game_time/results.served_groups:.1f} мин" if results.served_groups > 0 else "0 мин"
                    ]
                }
                st.table(pd.DataFrame(time_stats))
            
            with col3:
                st.markdown("**Эффективность и загрузка:**")
                efficiency_stats = {
                    'Показатель': [
                        'Коэффициент загрузки',
                        'Время простоя',
                        'Производительность',
                        'Интервал между заливками',
                        'Время заливки',
                        'Эффективность использования'
                    ],
                    'Значение': [
                        f"{results.utilization:.2f}%",
                        f"{idle_time_pct:.1f}%",
                        f"{efficiency:.2f} групп/час",
                        f"{S} часов",
                        f"{L} минут",
                        f"{(game_time_pct / (game_time_pct + resurfacing_time_pct) * 100):.1f}%" if (game_time_pct + resurfacing_time_pct) > 0 else "0%"
                    ]
                }
                st.table(pd.DataFrame(efficiency_stats))
            
            # Статистика очереди
            st.markdown("**Статистика очереди:**")
            if hasattr(results, 'queue_lengths') and results.queue_lengths:
                queue_data = {
                    'Метрика': [
                        'Максимальная длина очереди',
                        'Средняя длина очереди', 
                        'Медианная длина очереди',
                        'Время с пустой очередью',
                        'Время с полной очередью',
                        'Процент времени с очередью'
                    ],
                    'Значение': [
                        f"{max(results.queue_lengths)} групп",
                        f"{np.mean(results.queue_lengths):.2f} групп",
                        f"{np.median(results.queue_lengths):.2f} групп",
                        f"{(results.queue_lengths.count(0) / len(results.queue_lengths) * 100):.1f}%",
                        f"{(results.queue_lengths.count(K) / len(results.queue_lengths) * 100):.1f}%",
                        f"{100 - (results.queue_lengths.count(0) / len(results.queue_lengths) * 100):.1f}%"
                    ]
                }
                st.table(pd.DataFrame(queue_data))
                
                # График длины очереди во времени
                st.markdown("**Динамика длины очереди:**")
                fig_queue, ax_queue = plt.subplots(figsize=(10, 4))
                # Ограничим количество точек для графика
                if len(results.queue_times) > 200:
                    step = len(results.queue_times) // 200
                    times = results.queue_times[::step]
                    lengths = results.queue_lengths[::step]
                else:
                    times = results.queue_times
                    lengths = results.queue_lengths
                
                ax_queue.plot(times, lengths, alpha=0.7, linewidth=1)
                ax_queue.fill_between(times, 0, lengths, alpha=0.3)
                ax_queue.set_xlabel('Время (минуты)')
                ax_queue.set_ylabel('Длина очереди (групп)')
                ax_queue.set_title('Изменение длины очереди во времени')
                ax_queue.grid(True, alpha=0.3)
                ax_queue.set_ylim(bottom=0)
                st.pyplot(fig_queue)
        
        # Логи моделирования
        if show_logs:
            st.markdown("---")
            st.subheader("📋 Логи моделирования")
            
            # Создаем расширяемую область для логов
            with st.expander("Показать логи выполнения", expanded=False):
                st.text_area("Логи:", logs, height=300)
        
        # Схема процесса
        st.markdown("---")
        st.subheader("📋 Структурная схема процесса")
        
        try:
            st.image("структурная схема модели.drawio.png", 
                    caption="Структурная схема процесса функционирования хоккейной коробки",
                    use_container_width=True)
        except:
            st.warning("Файл со схемой не найден. Убедитесь, что файл 'структурная схема модели.drawio.png' находится в той же папке.")

    else:
        # Сообщение перед запуском
        st.info("👈 Задайте параметры в боковой панели и нажмите кнопку 'Запустить моделирование'")
        
        # Показываем схему процесса до запуска
        try:
            st.image("структурная схема модели.drawio.png", 
                    caption="Структурная схема процесса функционирования хоккейной коробки",
                    use_container_width=True)
        except:
            st.warning("Файл со схемой не найден. Убедитесь, что файл 'структурная схема модели.drawio.png' находится в той же папке.")
        
        # Информация о параметрах по умолчанию
        st.markdown("---")
        st.subheader("ℹ️ О параметрах моделирования")
        
        param_info = {
            'Параметр': ['N', 'M', 'A', 'B', 'K', 'T', 'S', 'L'],
            'Описание': [
                'Среднее время между приходом групп (минуты)',
                'Разброс времени прихода групп (минуты)',
                'Среднее время игры (минуты)',
                'Разброс времени игры (минуты)',
                'Максимальный размер очереди (групп)',
                'Время моделирования (часы)',
                'Интервал между заливками льда (часы)',
                'Время заливки льда (минуты)'
            ],
            'Ограничения': [
                'N ≥ M, N > 0',
                '0 ≤ M ≤ N',
                'A ≥ B, A > 0',
                '0 ≤ B ≤ A',
                'K > 0',
                'T > 0',
                'S > 0',
                'L > 0'
            ]
        }
        st.table(pd.DataFrame(param_info))

# Подвал приложения
st.markdown("---")
st.markdown(
    "**Курсовая работа по дисциплине 'Имитационное моделирование дискретных процессов'** • "
    "Разработано с использованием Python, SimPy и Streamlit"
)