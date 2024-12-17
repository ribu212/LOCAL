import requests
from datetime import datetime
import sqlite3
import flet as ft

# 定数の定義
AREA_LIST_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL_TEMPLATE = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

# データベースの初期化
def init_db():
    conn = sqlite3.connect('weather.db')
    c = conn.cursor()

    # 天気予報テーブルの作成
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather_forecast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT NOT NULL,
            date TEXT NOT NULL,
            forecast TEXT NOT NULL,
            temperature_min REAL,
            temperature_max REAL
        )
    ''')
    
    # エリア情報テーブルの作成（オプショナル）
    c.execute('''
        CREATE TABLE IF NOT EXISTS area_info (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# 地域リスト取得関数
def get_area_list():
    response = requests.get(AREA_LIST_URL)
    response.raise_for_status()
    area_data = response.json()
    areas = [(region_code, region_info['name']) for region_code, region_info in area_data['offices'].items()]
    return areas

# 天気予報取得関数
def get_weather_forecast(region_code):
    forecast_url = FORECAST_URL_TEMPLATE.format(region_code)
    response = requests.get(forecast_url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e}")
        return [{"date": "N/A", "weather": "取得エラー", "tempMax": "N/A", "tempMin": "N/A"}]

    forecast_data = response.json()
    weather_data = []

    try:
        area_forecasts = forecast_data[0]['timeSeries'][0]['areas']
        date_series = forecast_data[0]['timeSeries'][0]['timeDefines']

        temp_max_series = None
        temp_min_series = None
        for time_series in forecast_data:
            for series in time_series['timeSeries']:
                if 'tempsMax' in series['areas'][0]:
                    temp_max_series = series['areas'][0]['tempsMax']
                if 'tempsMin' in series['areas'][0]:
                    temp_min_series = series['areas'][0]['tempsMin']

        for i in range(3):
            date = datetime.strptime(date_series[i], "%Y-%m-%dT%H:%M:%S%z").date()
            weather = area_forecasts[0]['weathers'][i]
            temp_max = temp_max_series[i] if temp_max_series and len(temp_max_series) > i else "N/A"
            temp_min = temp_min_series[i] if temp_min_series and len(temp_min_series) > i else "N/A"
            weather_data.append({
                "date": date,
                "weather": weather,
                "tempMax": temp_max,
                "tempMin": temp_min
            })

            # データベースに保存
            save_weather_forecast(region_code, date, weather, temp_min, temp_max)

    except (IndexError, KeyError) as e:
        print(f"Data Error: {e}")
        return [{"date": "N/A", "weather": "データ取得エラー", "tempMax": "N/A", "tempMin": "N/A"}]

    return weather_data

# 天気予報データをDBに保存する関数
def save_weather_forecast(area_code, date, forecast, temp_min, temp_max):
    conn = sqlite3.connect('weather.db')
    c = conn.cursor()

    c.execute('''
        INSERT INTO weather_forecast (area_code, date, forecast, temperature_min, temperature_max)
        VALUES (?, ?, ?, ?, ?)
    ''', (area_code, date, forecast, temp_min, temp_max))

    conn.commit()
    conn.close()

# 過去の天気予報データを取得する関数
def fetch_forecast_by_date(date):
    conn = sqlite3.connect('weather.db')
    c = conn.cursor()
    c.execute('''
        SELECT * FROM weather_forecast WHERE date = ?
    ''', (date,))
    forecasts = c.fetchall()
    conn.close()
    return forecasts

# メイン関数
def main(page: ft.Page):
    init_db()
    areas = get_area_list()

    dropdown = ft.Dropdown(
        label="地域を選択してください",
        hint_text="地域",
        options=[ft.dropdown.Option(key=code, text=name) for code, name in areas]
    )

    weather_info = ft.Row(wrap=True, spacing=10)

    def on_area_select(e):
        region_code = dropdown.value
        print(f"Selected region code: {region_code}")
        if region_code:
            weather_info.controls.clear()
            forecast = get_weather_forecast(region_code)
            for day in forecast:
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(f"日付: {day['date']}"),
                                ft.Text(f"天気: {day['weather']}"),
                                ft.Text(f"最高気温: {day['tempMax']}"),
                                ft.Text(f"最低気温: {day['tempMin']}"),
                            ],
                            spacing=5,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=10,
                    ),
                    elevation=5,
                )
                weather_info.controls.append(card)
            page.update()

    dropdown.on_change = on_area_select

    # 日付選択フィールド
    def show_forecast_by_date(selected_date):
        weather_info.controls.clear()
        forecasts = fetch_forecast_by_date(selected_date)
        for forecast in forecasts:
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(f"地域コード: {forecast[1]}"),
                            ft.Text(f"日付: {forecast[2]}"),
                            ft.Text(f"天気: {forecast[3]}"),
                            ft.Text(f"最高気温: {forecast[5]}"),
                            ft.Text(f"最低気温: {forecast[4]}"),
                        ],
                        spacing=5,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    padding=10,
                ),
                elevation=5,
            )
            weather_info.controls.append(card)
        page.update()

    date_picker = ft.DatePicker(on_change=lambda e: show_forecast_by_date(e.control.value))

    page.add(
        ft.Column(
            [
                ft.Text("天気予報アプリ", size=24, weight="bold"),
                dropdown,
                ft.Text("日付を選択してください"),
                date_picker,
                weather_info
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=20,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)