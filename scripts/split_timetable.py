
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image


# GoogleスプレッドシートのID
SHEET_ID = "1fdSGqT1s2kit91TcQV_mjcuvOawGAU6JZ_5N684bH3U"

# ExcelファイルのダウンロードURL
URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=xlsx"
)

# 出力先
OUTPUT_DIR = Path("output")

# Excel内部に格納されている画像
IMAGE_PATH = "xl/media/image1.jpg"

# 元画像のサイズ
EXPECTED_SIZE = (960, 720)

# 完成画像のサイズ
CROP_SIZE = (468, 304)


def main():
    print("時間割Excelの取得を開始します。")

    # Excelファイルをダウンロード
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        excel_data = response.read()

    print(f"ダウンロード成功: {len(excel_data):,} bytes")

    # Excelから元のJPEG画像を取り出す
    with zipfile.ZipFile(BytesIO(excel_data)) as archive:
        if IMAGE_PATH not in archive.namelist():
            raise FileNotFoundError(
                f"{IMAGE_PATH} が見つかりません。"
            )

        jpeg_data = archive.read(IMAGE_PATH)

    print(f"JPEG取得成功: {len(jpeg_data):,} bytes")

    # JPEG画像を読み込む
    with Image.open(BytesIO(jpeg_data)) as source:
        source.load()

        print(f"元画像サイズ: {source.size}")
        print(f"元画像モード: {source.mode}")

        # 元画像のサイズを検証
        if source.size != EXPECTED_SIZE:
            raise ValueError(
                f"画像サイズが想定と異なります: {source.size}"
            )

        # PNGで扱いやすいRGB形式にする
        if source.mode != "RGB":
            source = source.convert("RGB")

        # 4枚の切り取り範囲
        # (左, 上, 右, 下)
        regions = {
            "jh": (5, 8, 473, 312),
            "h2": (485, 8, 953, 312),
            "h1": (5, 368, 473, 672),
            "h3": (485, 368, 953, 672),
        }

        # 出力フォルダを作成
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        temporary_files = []

        try:
            # 4枚すべてを一時ファイルとして生成・検証
            for name, coordinates in regions.items():

                image = source.crop(coordinates)

                # 切り取り後のサイズを確認
                if image.size != CROP_SIZE:
                    raise ValueError(
                        f"{name} のサイズが異なります: {image.size}"
                    )

                temp_path = OUTPUT_DIR / f"{name}.tmp.png"

                # PNG形式で保存
                image.save(
                    temp_path,
                    format="PNG",
                    optimize=False
                )

                # 保存したPNGを再度開いて検証
                with Image.open(temp_path) as check:
                    check.load()

                    if check.size != CROP_SIZE:
                        raise ValueError(
                            f"{name} のPNGサイズが異なります。"
                        )

                    if check.format != "PNG":
                        raise ValueError(
                            f"{name} がPNGではありません。"
                        )

                temporary_files.append(
                    (temp_path, OUTPUT_DIR / f"{name}.png")
                )

                print(
                    f"生成成功: {name}.png "
                    f"{image.width}x{image.height}"
                )

            # 4枚すべての検証が成功してから確定
            for temp_path, final_path in temporary_files:
                temp_path.replace(final_path)

        finally:
            # 失敗時に残った一時ファイルを削除
            for temp_path, _ in temporary_files:
                if temp_path.exists():
                    temp_path.unlink()

    print("\n===== 生成完了 =====")
    print("jh.png / h2.png / h1.png / h3.png")
    print("すべて468x304pxのPNGです。")


if __name__ == "__main__":
    main()
