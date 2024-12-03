import requests
import flet as ft

def get_area_list():
    url = "http://www.jma.go.jp/bosai/common/const/area.json"
    response = requests.get(url)
    area_json = response.json()
    return area_json['centers']

def main(page: ft.Page):
    page.title = "気象庁天気予報アプリ"

    area_list = get_area_list()
    tabs = [ft.Tab(text=info['name']) for code, info in area_list.items()]
    navigation_tabs = ft.Tabs(tabs=tabs, on_change=lambda e: get_forecast(page, list(area_list.keys())[e.control.selected_index], e.control.selected_index))
    page.add(navigation_tabs)

def get_forecast(page: ft.Page, area_code, tab_index):
    forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    response = requests.get(forecast_url)
    if response.status_code != 200:
        forecast_text = "天気情報の取得に失敗しました。"
    else:
        forecast_data = response.json()
        try:
            # 事前にレスポンスデータの構造を確認し、ここでデータを適切に抽出
            weather_info = forecast_data[0]["timeSeries"][0]["areas"][0]["weathers"][0]
            forecast_text = f"天気予報: {weather_info}"
        except Exception as e:
            forecast_text = f"データの解析に失敗しました: {str(e)}"

    page.dialog = ft.MessageBox(title=f"天気予報（{area_code}）", content=forecast_text, actions=[ft.MessageBoxAction("OK")])
    page.update()

if __name__ == "__main__":
    ft.app(target=main)