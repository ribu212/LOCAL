import requests
from datetime import datetime
import flet as ft

# 定数の定義
AREA_LIST_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL_TEMPLATE = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

# 地域リスト取得関数
def get_area_list():
    # APIリクエストを送信して、地域データを取得する
    response = requests.get(AREA_LIST_URL)
    response.raise_for_status()
    area_data = response.json()  # JSONデータに変換する
    areas = []

    # 地域データをパースして、地域コードと名称のペアを作成する
    for region_code, region_info in area_data['offices'].items():
        areas.append((region_code, region_info['name']))
    return areas

# 天気予報取得関数
def get_weather_forecast(region_code):
    # 指定した地域コードで天気予報のAPIリクエストを送信する
    forecast_url = FORECAST_URL_TEMPLATE.format(region_code)
    response = requests.get(forecast_url)

    try:
        response.raise_for_status()  # ステータスコードが200以外の場合、例外を発生させる
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e}")
        return [{"date": "N/A", "weather": "取得エラー", "tempMax": "N/A", "tempMin": "N/A"}]

    forecast_data = response.json()  # JSONデータに変換

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

        for i in range(3):  # 天気予報の最初の3日分を表示
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

    except (IndexError, KeyError) as e:
        print(f"Data Error: {e}")
        return [{"date": "N/A", "weather": "データ取得エラー", "tempMax": "N/A", "tempMin": "N/A"}]

    return weather_data

# メイン関数
def main(page: ft.Page):
    # 地域リストを取得
    areas = get_area_list()

    # ドロップダウンメニューを作成
    dropdown = ft.Dropdown(
        label="地域を選択してください",
        hint_text="地域",
        options=[ft.dropdown.Option(key=code, text=name) for code, name in areas]
    )

    # 天気情報を表示する行を作成
    weather_info = ft.Row(wrap=True, spacing=10)   

    # ドロップダウンメニューの選択変更時のイベントハンドラー
    def on_area_select(e):
        region_code = dropdown.value  # 選択された地域コードを取得
        print(f"Selected region code: {region_code}")  
        if region_code:
            weather_info.controls.clear()  # 古い天気情報をクリア
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
                weather_info.controls.append(card)  # 新しい天気情報を追加
            page.update()  # ページを更新して新しい情報を表示

    dropdown.on_change = on_area_select  # イベントハンドラーを設定

    # ページにコンポーネントを追加
    page.add(
        ft.Column(
            [
                ft.Text("天気予報アプリ", size=24, weight="bold"),
                dropdown,
                weather_info
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=20,
        )
    )

# アプリケーションのエントリーポイント
if __name__ == "__main__":
    ft.app(target=main)