import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from flask import Flask, render_template_string
import datetime
import os

app = Flask(__name__)

def generate_chart():
    # Ваш код обработки данных
    file_path = Path("C:/price_tracking/ipad_price_history.txt")
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split(' - ')
            if len(parts) == 2:
                date_str, price_str = parts[0].split()[0], parts[1]
                date = pd.to_datetime(date_str, format='%d.%m.%Y').date()
                price = float(price_str.replace(' руб.', '').replace(' ', ''))
                data.append({'date': date, 'price': price})

    df = pd.DataFrame(data)
    df = df.groupby('date').last().reset_index()
    df = df.sort_values('date')
    df['date'] = pd.to_datetime(df['date'])

    df['price_diff'] = df['price'].diff()
    df['color'] = df['price_diff'].apply(lambda x: 'green' if x < 0 else ('red' if x > 0 else 'gray'))

    fig = go.Figure()

    # Конфигурация графика (как в вашем коде)
    base_dpi = 96
    cm_to_inch = 0.393701
    target_cm = 5
    px_per_day = target_cm * cm_to_inch * base_dpi

    for i in range(len(df)):
        fig.add_trace(go.Scatter(
            x=[df['date'].iloc[i]],
            y=[df['price'].iloc[i]],
            mode='markers+text',
            text=[f"{df['price'].iloc[i]:,.0f} руб."],
            textposition='top center',
            marker=dict(size=10, color=df['color'].iloc[i] if i > 0 else 'gray'),
            showlegend=False
        ))
        
        if i > 0:
            fig.add_trace(go.Scatter(
                x=[df['date'].iloc[i-1], df['date'].iloc[i]],
                y=[df['price'].iloc[i-1], df['price'].iloc[i]],
                mode='lines',
                line=dict(width=2, color=df['color'].iloc[i]),
                showlegend=False
            ))

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

    fig.update_layout(
        title='Динамика изменения цены iPad',
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
        width=px_per_day * (len(df)-1) + 200,
        height=600,
        margin=dict(l=50, r=50, b=100, t=100)
    )

    fig.update_xaxes(
        dtick="D1",
        ticktext=df['date'].dt.strftime('%d.%m.%Y').tolist(),
        tickvals=df['date']
    )

    return fig.to_html(full_html=False), df

@app.route('/')
def index():
    plot_html, df = generate_chart()
    
    # Рассчитываем статистику
    current_price = f"{df['price'].iloc[-1]:,.0f}".replace(",", " ")
    price_change = f"{df['price'].iloc[-1] - df['price'].iloc[0]:+,.0f}".replace(",", " ")
    price_change_color = 'green' if (df['price'].iloc[-1] - df['price'].iloc[0]) < 0 else 'red'
    days_tracked = (df['date'].iloc[-1] - df['date'].iloc[0]).days
    last_update = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # HTML шаблон с улучшенным дизайном
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Анализатор цен на iPad</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .chart-container {
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                padding: 25px;
                margin-top: 20px;
            }
            .stat-card {
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            .price-up {
                color: #dc3545;
            }
            .price-down {
                color: #28a745;
            }
            .last-update {
                font-size: 0.9rem;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <div class="container py-4">
            <div class="text-center mb-4">
                <h1 class="display-5">Анализатор цен на iPad</h1>
                <p class="text-muted">Динамика изменения цен с детализацией по дням</p>
            </div>
            
            <div class="row">
                <div class="col-md-4">
                    <div class="stat-card bg-light">
                        <h5>Текущая цена</h5>
                        <p class="fs-3">{{ current_price }} руб.</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card bg-light">
                        <h5>Изменение цены</h5>
                        <p class="fs-3 {{ 'price-down' if price_change_color == 'green' else 'price-up' }}">
                            {{ price_change }} руб.
                        </p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card bg-light">
                        <h5>Период анализа</h5>
                        <p class="fs-3">{{ days_tracked }} дней</p>
                    </div>
                </div>
            </div>
            
            <div class="chart-container">
                {{ plot_html|safe }}
            </div>
            
            <div class="text-end mt-2 last-update">
                Данные актуальны на: {{ last_update }}
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', 
    plot_html=plot_html,
    current_price=current_price,
    price_change=price_change,
    price_change_color=price_change_color,
    days_tracked=days_tracked,
    last_update=last_update)

if __name__ == '__main__':
   if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')