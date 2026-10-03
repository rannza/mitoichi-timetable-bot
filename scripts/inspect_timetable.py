
import urllib.request
import zipfile
from io import BytesIO

SHEET_ID = "1fdSGqT1s2kit91TcQV_mjcuvOawGAU6JZ_5N684bH3U"

URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=xlsx"
)


def get_jpeg_size(data):
    """JPEGのヘッダーから幅と高さを取得する。"""

    if not data.startswith(b"\xff\xd8"):
        raise ValueError("JPEG形式ではありません。")

    i = 2
    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3,
        0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB,
        0xCD, 0xCE, 0xCF
    }

    while i < len(data):
        if data[i] != 0xFF:
            raise ValueError("JPEGマーカーを解析できません。")

        while i < len(data) and data[i] == 0xFF:
            i += 1

        marker = data[i]
        i += 1

        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue

        length = int.from_bytes(data[i:i + 2], "big")

        if marker in sof_markers:
            height = int.from_bytes(data[i + 3:i + 5], "big")
            width = int.from_bytes(data[i + 5:i + 7], "big")
            return width, height

        i += length

    raise ValueError("JPEGの画像サイズを取得できませんでした。")


def main():
    print("時間割Excelの取得を開始します。")

    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        excel_data = response.read()

    print(f"ダウンロード成功: {len(excel_data):,} bytes")

    with zipfile.ZipFile(BytesIO(excel_data)) as archive:
        image_path = "xl/media/image1.jpg"

        if image_path not in archive.namelist():
            raise FileNotFoundError(
                f"{image_path} が見つかりません。"
            )

        image_data = archive.read(image_path)

        width, height = get_jpeg_size(image_data)

        print("\n===== 元画像の検査結果 =====")
        print(f"ファイル名: {image_path}")
        print(f"形式: JPEG")
        print(f"ファイルサイズ: {len(image_data):,} bytes")
        print(f"幅: {width}px")
        print(f"高さ: {height}px")

        if (width, height) == (960, 720):
            print("判定: 期待していたサイズと一致しました。")
        else:
            print("判定: 以前の情報とサイズが異なります。")

    print("\n検査完了。")


if __name__ == "__main__":
    main()
