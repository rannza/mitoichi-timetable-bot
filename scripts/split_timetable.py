
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

SHEET_ID = "1fdSGqT1s2kit91TcQV_mjcuvOawGAU6JZ_5N684bH3U"

URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=xlsx"
)

OUTPUT_DIR = Path("output")
IMAGE_PATH = "xl/media/image1.jpg"

EXPECTED_SIZE = (960, 720)
CROP_SIZE = (470, 305)


def main():
    print("時間割Excelの取得を開始します。")

    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        excel_data = response.read()

    print(f"ダウンロード成功: {len(excel_data):,} bytes")

    # Excelから元のJPEGを取り出す
    with zipfile.ZipFile(BytesIO(excel_data)) as archive:
        if IMAGE_PATH not in archive.namelist():
            raise FileNotFoundError(
                f"{IMAGE_PATH} が見つかりません。"
            )

        jpeg_data = archive.read(IMAGE_PATH)

    # JPEGを読み込む
    with Image.open(BytesIO(jpeg_data)) as source:
        source.load()

        print(f"元画像サイズ: {source.size}")
        print(f"元画像モード: {source.mode}")

        if source.size != EXPECTED_SIZE:
            raise ValueError(
                f"画像サイズが想定と異なります: {source.size}"
            )

        # PNGで扱いやすいRGB形式にする
        if source.mode != "RGB":
            source = source.convert("RGB")

        # 4つの領域を定義
        regions = {
            "jh": (5, 5, 475, 310),
            "h2": (485, 5, 955, 310),
            "h1": (5, 365, 475, 670),
            "h3": (485, 365, 955, 670),
        }

        # すべて一時領域で生成・検証してから出力する
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        temporary_files = []

        try:
            for name, coordinates in regions.items():
                image = source.crop(coordinates)

                if image.size != CROP_SIZE:
                    raise ValueError(
                        f"{name} のサイズが異なります: {image.size}"
                    )

                temp_path = OUTPUT_DIR / f"{name}.tmp.png"

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

            # 4枚すべての検証成功後に確定
            for temp_path, final_path in temporary_files:
                temp_path.replace(final_path)

        finally:
            for temp_path, _ in temporary_files:
                if temp_path.exists():
                    temp_path.unlink()

    print("\n===== 生成完了 =====")
    print("jh.png / h2.png / h1.png / h3.png")
    print("すべて470x305pxのPNGです。")


if __name__ == "__main__":
    main()
