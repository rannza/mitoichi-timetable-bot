
import urllib.request
import zipfile
from io import BytesIO

SHEET_ID = "1fdSGqT1s2kit91TcQV_mjcuvOawGAU6JZ_5N684bH3U"

URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=xlsx"
)


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
        files = archive.namelist()

        print("\n===== Excel内部ファイル一覧 =====")

        for name in files:
            if (
                name.startswith("xl/media/")
                or name.startswith("xl/drawings/")
                or name.startswith("xl/worksheets/_rels/")
                or name.startswith("xl/embeddings/")
                or name.startswith("customXml/")
            ):
                info = archive.getinfo(name)

                print(
                    f"{name} "
                    f"({info.file_size:,} bytes)"
                )

        print("\n===== 画像データの検査 =====")

        media_files = [
            name for name in files
            if name.startswith("xl/media/")
        ]

        if not media_files:
            print("xl/media 内に画像ファイルはありません。")

        for name in media_files:
            data = archive.read(name)

            print(f"\nファイル名: {name}")
            print(f"サイズ: {len(data):,} bytes")
            print(f"先頭データ: {data[:16].hex()}")

            if data.startswith(b"\xff\xd8\xff"):
                print("形式: JPEG")
            elif data.startswith(b"\x89PNG\r\n\x1a\n"):
                print("形式: PNG")
            else:
                print("形式: その他・未判定")

    print("\n===== 調査完了 =====")


if __name__ == "__main__":
    main()
