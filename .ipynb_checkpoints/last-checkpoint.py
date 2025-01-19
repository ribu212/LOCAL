import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import sqlite3

class RealEstateScraper:
    def __init__(self, base_url, db_file):
        self.base_url = base_url
        self.db_file = db_file

        # データベースの初期設定
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)  # データベースファイルに接続
        c = conn.cursor()

        # テーブル作成
        c.execute('''
        CREATE TABLE IF NOT EXISTS suumo_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            distance TEXT,
            price TEXT
        )
        ''')

        conn.commit()
        conn.close()

    def get_property_data(self, max_pages=1):
        properties = []
        for page_number in range(1, max_pages + 1):
            page_url = self.base_url + f'?page={page_number}'
            response = requests.get(page_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            if not soup.find_all('div', class_='cassetteitem'):
                break

            for listing in soup.find_all('div', class_='cassetteitem'):
                name = listing.find('div', class_='cassetteitem_content-title').get_text(strip=True)
                distances = listing.find_all('div', class_='cassetteitem_detail-text')
                price_tags = listing.find_all('span', class_='cassetteitem_other-emphasis')

                if distances and price_tags:
                    distance_texts = [dist.get_text(strip=True) for dist in distances]
                    price_texts = [price.get_text(strip=True) for price in price_tags]

                    properties.append({
                        'name': name,
                        'distance': distance_texts[0],
                        'price': price_texts[0]
                    })
            time.sleep(1)  # 次のリクエストを送る前に一時停止。過負荷を防ぐ。
        self.df = pd.DataFrame(properties)

    def save_to_db(self):
        conn = sqlite3.connect(self.db_file)  # データベースファイルに接続
        self.df.to_sql('suumo_properties', conn, if_exists='append', index=False)
        conn.close()
        print("データはデータベースに保存されました。")

# スクレイピングとデータベースに保存の実行
scraper = RealEstateScraper('https://suumo.jp/chintai/saitama/sa_saitama/', 'suumo.db')
scraper.get_property_data(max_pages=300)  # 必要に応じてページ数を変更
scraper.save_to_db()


# 物件の価格と最寄り駅までの距離の関係分析

この分析では、SUUMOで取得したさいたま市の賃貸物件情報を使用して、物件の価格と最寄り駅までの距離の関係を分析します。

## 仮説
最寄り駅までの距離が短いほど、賃貸物件の価格は高いという仮説を検証します。

# ライブラリのインポート
import pandas as pd
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# SQLiteに接続（データベース名を suumo.db に設定）
conn = sqlite3.connect('suumo.db')

# データベースからデータをクエリして取得
df = pd.read_sql('SELECT * FROM suumo_properties', conn)
conn.close()

# データのクレンジング
df['distance'] = df['distance'].str.replace('m', '').astype(float)  # 距離の単位の除去と変換
df['price'] = df['price'].str.replace('万円', '').str.replace(',', '').astype(float)  # 価格の単位の除去と変換
df = df.dropna(subset=['distance', 'price'])  # 欠損値の除去

df.head()

## データの可視化

最初に物件の価格と最寄り駅までの距離の関係を散布図で可視化します。

# 散布図の作成
plt.figure(figsize=(10, 6))
sns.scatterplot(x='distance', y='price', data=df)
plt.xlabel('最寄り駅までの距離 (m)')
plt.ylabel('物件の価格 (万円)')
plt.title('物件の価格と最寄り駅までの距離の関係')
plt.show()

## 回帰分析

物件の価格と最寄り駅までの距離間の関係を定量的に評価するために、単回帰分析を実行します。

# 回帰分析
X = df[['distance']].values
y = df['price'].values
model = LinearRegression()
model.fit(X, y)
predictions = model.predict(X)

# 回帰分析の結果をプロット
plt.figure(figsize=(10, 6))
sns.scatterplot(x='distance', y='price', data=df)
plt.plot(df['distance'], predictions, color='red')
plt.xlabel('最寄り駅までの距離 (m)')
plt.ylabel('物件の価格 (万円)')
plt.title('物件の価格と最寄り駅までの距離の関係 (回帰分析結果)')
plt.show()

# モデルの係数と評価
print("回帰係数:", model.coef_[0])
print("切片:", model.intercept_)
print("決定係数 (R^2):", model.score(X, y))

## 結論

回帰係数、切片、決定係数 (R^2) を基に仮説の検証結果を考察します。

- 回帰係数が負の値である場合、最寄り駅までの距離が短いほど物件の価格が高いという仮説をサポートします。
- R^2 が高い場合、モデルがデータに対する高い説明力を持っていることを示します。

これらの結果を基に、最寄り駅までの距離と物件の価格の関係について結論を導きます。