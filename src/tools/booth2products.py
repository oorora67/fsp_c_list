import json
import sys
import os
import re

try:
    import requests
except ImportError:
    print(
        "requestsパッケージが必要です。pip install requests でインストールしてください。"
    )
    sys.exit(1)

# Booth APIのJSONから商品一覧用JSONを生成するツール
# 使い方: python booth2products.py booth_item.json products.json


def booth_to_products(booth_json):
    main = booth_json
    category = main.get("category", {}).get("name", "")
    image = main.get("images", [{}])[0].get("original", "")
    description = main.get("description", "")
    tags = [t["name"] for t in main.get("tags", [])]

    # variationsがあれば展開、なければ本体のみ
    variations = main.get("variations") or []
    if not variations:
        variations = [
            {"id": main.get("id"), "name": main.get("name"), "price": main.get("price")}
        ]
    products = []
    for v in variations:
        # 価格は数値化
        price = v.get("price")
        if isinstance(price, str):
            price = int("".join(filter(str.isdigit, price)))
        products.append(
            {
                "id": v.get("id"),
                "name": main.get("name")
                + (
                    f" ({v.get('name')})"
                    if v.get("name") and v.get("name") != main.get("name")
                    else ""
                ),
                "price": price,
                "category": [category] if category else [],
                "image": image,
                "description": description,
                "tags": tags,
            }
        )
    return products


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python booth2products.py <booth_item.json or Booth商品URL> <products.json>"
        )
        return
    input_arg = sys.argv[1]
    output_file = sys.argv[2]
    booth_json = None
    # URLの場合
    if re.match(r"^https?://", input_arg):
        # Booth商品ページURLからAPIエンドポイントに変換
        m = re.search(r"/items/(\d+)", input_arg)
        if not m:
            print("URLから商品IDが取得できません")
            return
        item_id = m.group(1)
        api_url = f'https://{input_arg.split("/")[2]}/items/{item_id}.json'
        print(f"APIから取得: {api_url}")
        resp = requests.get(api_url)
        if resp.status_code != 200:
            print(f"API取得失敗: {resp.status_code}")
            return
        booth_json = resp.json()
    elif os.path.isfile(input_arg):
        with open(input_arg, encoding="utf-8") as f:
            booth_json = json.load(f)
    else:
        print("ファイルが存在しないか、URL形式が不正です")
        return
    products = booth_to_products(booth_json)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"{output_file} を出力しました")


if __name__ == "__main__":
    main()
