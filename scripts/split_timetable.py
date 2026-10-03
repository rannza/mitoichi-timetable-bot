
import urllib.request
import zipfile
import hashlib
import os
from io import BytesIO
from pathlib import Path
from PIL import Image

# GoogleスプレッドシートのID
SHEET_ID = "1fdSGqT1s2kit91TcQV_mjcuvOawGAU6JZ_5N684bH3U"

URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=xlsx"
)

# 保存先
OUTPUT_DIR = Path("output")
STATE_DIR = Path("state")
HASH_FILE = STATE_DIR / "source.sha256"

# Excel内の元画像
IMAGE_PATH = "xl/media/image1.jpg"

EXPECTED_SIZE = (960, 720)
CROP_SIZE = (468, 302)

# 4枚の切り抜き範囲
REGIONS = {
    "jh": (5, 10, 473, 312),
    "h2": (485, 10, 953, 312),
    "h1": (5, 370, 473, 672),
    "h3": (485, 370, 953, 672),
}


def set_output(name, value):
    """GitHub Actionsに結果を渡す"""
    output_file = os.environ.get("GITHUB_OUTPUT")

    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


def main():
    print("時間割画像の取得を開始します。")

    # Excelファイルをダウンロード
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        excel_data = response.read()

    print(f"ダウンロード成功: {len(excel_data):,} bytes")

    # Excelから元画像を取り出す
    with zipfile.ZipFile(BytesIO(excel_data)) as archive:
        if IMAGE_PATH not in archive.namelist():
            raise FileNotFoundError(
                f"{IMAGE_PATH} が見つかりません。"
            )

        jpeg_data = archive.read(IMAGE_PATH)

    print(f"JPEG取得成功: {len(jpeg_data):,} bytes")

    # 元画像のハッシュ値を計算
    current_hash = hashlib.sha256(jpeg_data).hexdigest()

    # 前回のハッシュ値を確認
    previous_hash = None

    if HASH_FILE.exists():
        previous_hash = HASH_FILE.read_text(
            encoding="utf-8"
        ).strip()

    # 画像が変更されていない場合は終了
    outputs_exist = all(
        (OUTPUT_DIR / f"{name}.png").exists()
        for name in REGIONS
    ) and (OUTPUT_DIR / "h1_watch.png").exists()

    if current_hash == previous_hash and outputs_exist:
        print("画像に変更はありません。")
        print("4分割処理を省略します。")
        set_output("changed", "false")
        return

    print("画像の変更を検出しました。")
    print("4分割処理を開始します。")

    # 元画像を開く
    with Image.open(BytesIO(jpeg_data)) as source:
        source.load()

        print(f"元画像サイズ: {source.size}")

        if source.size != EXPECTED_SIZE:
            raise ValueError(
                f"画像サイズが想定と異なります: {source.size}"
            )

        if source.mode != "RGB":
            source = source.convert("RGB")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        temporary_files = []

        try:
            # 4枚に切り抜く
            for name, coordinates in REGIONS.items():
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

                # 保存したPNGを検証
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

            # 4枚すべて検証できたら正式な名前に変更
                    # Apple Watch用の横長画像を作成
        with Image.open(OUTPUT_DIR / "h1.png") as watch_source:
            watch_source.load()

            # 710×302pxの白いキャンバスを作成
            watch_image = Image.new(
                "RGB",
                (710, 302),
                (255, 255, 255)
            )

            # 元画像を中央に配置
            watch_image.paste(
                watch_source,
                (121, 0)
            )

            # PNGとして保存
            watch_image.save(
                OUTPUT_DIR / "h1_watch.png",
                format="PNG",
                optimize=False
            )

        print("生成成功: h1_watch.png 710x302")

        finally:
            # 残った一時ファイルを削除
            for temp_path, _ in temporary_files:
                if temp_path.exists():
                    temp_path.unlink()

    # 今回のハッシュ値を保存
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    temp_hash_file = STATE_DIR / "source.sha256.tmp"
    temp_hash_file.write_text(
        current_hash + "\n",
        encoding="utf-8"
    )
    temp_hash_file.replace(HASH_FILE)

    print("\n===== 更新完了 =====")
    print("jh.png / h2.png / h1.png / h3.png")
    print("すべて468x302pxのPNGです。")

    set_output("changed", "true")


if __name__ == "__main__":
    main()
