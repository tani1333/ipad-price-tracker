import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import datetime

# Путь к файлу
file_path = Path("C:/price_tracking/ipad_price_history.txt")

# Чтение данных
data = []
with open(file_path, 'r', encoding='utf-8') as file:
    for line in file:
        parts = line.strip().split(' - ')
        if len(parts) == 2:
            date_str, price_str = parts[0].split()[0], parts[1]  # Берем только дату без времени
            date = pd.to_datetime(date_str, format='%d.%m.%Y').date()
            price = float(price_str.replace(' руб.', '').replace(' ', ''))
            data.append({'date': date, 'price': price})

# Создание DataFrame
df = pd.DataFrame(data)
df = df.groupby('date').last().reset_index()  # Убираем дубликаты дат
df = df.sort_values('date')
df['date'] = pd.to_datetime(df['date'])

# Расчет разницы цен
df['price_diff'] = df['price'].diff()
df['color'] = df['price_diff'].apply(lambda x: 'green' if x < 0 else ('red' if x > 0 else 'gray'))

# Создание фигуры с точным расстоянием между точками
fig = go.Figure()

# Конвертируем даты в числовой формат для точного позиционирования
dates_num = [d.toordinal() for d in df['date'].dt.date]

# Вычисляем необходимое расстояние между точками (5 см в единицах графика)
# 1 день = 5 см (примерно 0.2 дюйма при 96 DPI)
base_dpi = 96
cm_to_inch = 0.393701
target_cm = 5
px_per_day = target_cm * cm_to_inch * base_dpi  # Пикселей на день

# Добавляем данные
for i in range(len(df)):
    # Точка с ценой
    fig.add_trace(go.Scatter(
        x=[df['date'].iloc[i]],
        y=[df['price'].iloc[i]],
        mode='markers+text',
        text=[f"{df['price'].iloc[i]:,.0f} руб."],
        textposition='top center',
        marker=dict(size=10, color=df['color'].iloc[i] if i > 0 else 'gray'),
        showlegend=False
    ))
    
    # Линия между точками (кроме первой)
    if i > 0:
        fig.add_trace(go.Scatter(
            x=[df['date'].iloc[i-1], df['date'].iloc[i]],
            y=[df['price'].iloc[i-1], df['price'].iloc[i]],
            mode='lines',
            line=dict(width=2, color=df['color'].iloc[i]),
            showlegend=False
        ))

        # Аннотация с разницей цен
        diff = df['price_diff'].iloc[i]
        if not pd.isna(diff):
            fig.add_annotation(
                x=df['date'].iloc[i-1] + (df['date'].iloc[i] - df['date'].iloc[i-1])/2,
                y=(df['price'].iloc[i-1] + df['price'].iloc[i])/2,
                text=f"{diff:+,.0f} руб.",
                showarrow=False,
                font=dict(color=df['color'].iloc[i], size=12),
                yshift=10
            )

# Настройка осей и внешнего вида
fig.update_layout(
    title='Динамика изменения цены iPad (расстояние между точками: 5 см)',
    xaxis=dict(
        tickmode='array',
        tickvals=df['date'],
        tickformat='%d.%m.%Y',
        type='date',
        title='Дата',
        tickangle=45
    ),
    yaxis=dict(
        range=[0, df['price'].max() * 1.2],
        title='Цена (руб.)'
    ),
    template='plotly_white',
    width=px_per_day * (len(df)-1) + 200,  # Рассчитываем ширину для 5 см между точками
    height=600,
    margin=dict(l=50, r=50, b=100, t=100)
)

# Гарантируем отображение всех дат
fig.update_xaxes(
    dtick="D1",
    ticktext=df['date'].dt.strftime('%d.%m.%Y').tolist(),
    tickvals=df['date']
)

fig.show()
