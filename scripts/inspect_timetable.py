
import urllib.request
from io import BytesIO
from openpyxl import load_workbook

# 時間割が掲載されているGoogleスプレッドシート
SHEET_ID = "1fdSGqT1s2kit91TcQV_mjcuvOawGAU6JZ_5N684bH3U"

# Excel形式でダウンロード
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

def main():
    print("時間割Excelの取得を開始します。")

    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        excel_data = response.read()

    print(f"ダウンロード成功: {len(excel_data):,} bytes")

    # Excelファイルを読み込む
    workbook = load_workbook(
        BytesIO(excel_data),
        data_only=True
    )

    print(f"シート数: {len(workbook.worksheets)}")

    total_images = 0

    for sheet in workbook.worksheets:
        images = getattr(sheet, "_images", [])

        print(f"\nシート名: {sheet.title}")
        print(f"画像数: {len(images)}")

        for index, img in enumerate(images, start=1):
            image_data = img._data()

            print(f"  画像 {index}")
            print(f"  形式: {img.format}")
            print(f"  幅: {img.width}px")
            print(f"  高さ: {img.height}px")
            print(f"  データサイズ: {len(image_data):,} bytes")
            print(f"  先頭データ: {image_data[:8].hex()}")

            total_images += 1

    print(f"\n検査完了。合計画像数: {total_images}")

if __name__ == "__main__":
    main()
