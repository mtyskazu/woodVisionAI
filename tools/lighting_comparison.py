"""照明比較ツール — 白色 / 赤色照明 × 拡散板有無の組み合わせ評価

Phase 1 検証項目:
  - 白色（W）と赤色（R）照明のコントラスト比較
  - 拡散板（DF80, 透過率80%）による反射抑制効果の確認
  - ハレーション発生の定量評価

使い方:
  1. 各条件で撮像した画像を所定のフォルダに配置
  2. 本ツールで解析・レポート生成

ディレクトリ構成例:
  data/lighting_test/
  ├── white_no_diffuser/      # 白色照明 拡散板なし
  ├── white_with_diffuser/    # 白色照明 拡散板あり
  ├── red_no_diffuser/        # 赤色照明 拡散板なし
  └── red_with_diffuser/      # 赤色照明 拡散板あり
"""

from __future__ import annotations

import argparse
import csv
import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

LIGHTING_CONDITIONS = [
    "white_no_diffuser",
    "white_with_diffuser",
    "red_no_diffuser",
    "red_with_diffuser",
]


@dataclass
class ImageMetrics:
    """画像の品質評価メトリクス"""

    filename: str
    condition: str
    mean_brightness: float
    std_brightness: float
    contrast_rms: float
    halation_ratio: float
    snr: float
    edge_sharpness: float

    def as_dict(self) -> dict[str, str | float]:
        return {
            "filename": self.filename,
            "condition": self.condition,
            "mean_brightness": round(self.mean_brightness, 2),
            "std_brightness": round(self.std_brightness, 2),
            "contrast_rms": round(self.contrast_rms, 2),
            "halation_ratio": round(self.halation_ratio, 4),
            "snr": round(self.snr, 2),
            "edge_sharpness": round(self.edge_sharpness, 2),
        }


def compute_metrics(image: np.ndarray, condition: str, filename: str) -> ImageMetrics:
    """画像から品質メトリクスを算出する

    Args:
        image: BGR形式の画像 (H, W, 3)
        condition: 照明条件名
        filename: ファイル名

    Returns:
        ImageMetrics
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    mean_brightness = float(np.mean(gray))
    std_brightness = float(np.std(gray))
    contrast_rms = std_brightness

    # ハレーション: 飽和画素(>250)の割合
    halation_pixels = np.sum(gray > 250)
    halation_ratio = float(halation_pixels) / gray.size

    # SNR (Signal-to-Noise Ratio)
    snr = mean_brightness / std_brightness if std_brightness > 0 else 0.0

    # エッジ鮮鋭度: Laplacianの分散
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    edge_sharpness = float(np.var(laplacian))

    return ImageMetrics(
        filename=filename,
        condition=condition,
        mean_brightness=mean_brightness,
        std_brightness=std_brightness,
        contrast_rms=contrast_rms,
        halation_ratio=halation_ratio,
        snr=snr,
        edge_sharpness=edge_sharpness,
    )


def analyze_condition(image_dir: Path, condition: str) -> list[ImageMetrics]:
    """指定条件ディレクトリ内の全画像を解析する"""
    cond_dir = image_dir / condition
    if not cond_dir.exists():
        logger.warning("ディレクトリが見つかりません: %s", cond_dir)
        return []

    extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
    image_files = sorted(
        f for f in cond_dir.iterdir() if f.suffix.lower() in extensions
    )

    if not image_files:
        logger.warning("画像ファイルが見つかりません: %s", cond_dir)
        return []

    results = []
    for img_path in image_files:
        image = cv2.imread(str(img_path))
        if image is None:
            logger.warning("画像の読み込みに失敗: %s", img_path)
            continue

        metrics = compute_metrics(image, condition, img_path.name)
        results.append(metrics)
        logger.debug("解析完了: %s", img_path.name)

    logger.info(
        "条件 '%s': %d 枚の画像を解析", condition, len(results)
    )
    return results


def generate_summary(all_metrics: list[ImageMetrics]) -> dict[str, dict[str, float]]:
    """条件ごとの平均メトリクスを集計する"""
    from collections import defaultdict

    groups: dict[str, list[ImageMetrics]] = defaultdict(list)
    for m in all_metrics:
        groups[m.condition].append(m)

    summary: dict[str, dict[str, float]] = {}
    for condition, metrics_list in groups.items():
        n = len(metrics_list)
        summary[condition] = {
            "num_images": n,
            "avg_brightness": round(sum(m.mean_brightness for m in metrics_list) / n, 2),
            "avg_contrast_rms": round(sum(m.contrast_rms for m in metrics_list) / n, 2),
            "avg_halation_ratio": round(
                sum(m.halation_ratio for m in metrics_list) / n, 4
            ),
            "avg_snr": round(sum(m.snr for m in metrics_list) / n, 2),
            "avg_edge_sharpness": round(
                sum(m.edge_sharpness for m in metrics_list) / n, 2
            ),
        }

    return summary


def export_csv(all_metrics: list[ImageMetrics], output_path: Path) -> None:
    """メトリクスをCSVファイルに出力する"""
    if not all_metrics:
        logger.warning("出力するデータがありません")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(all_metrics[0].as_dict().keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in all_metrics:
            writer.writerow(m.as_dict())

    logger.info("CSV出力完了: %s", output_path)


def print_report(summary: dict[str, dict[str, float]]) -> None:
    """比較レポートをコンソールに表示する"""
    print("\n" + "=" * 80)
    print("照明条件比較レポート")
    print("=" * 80)

    header = (
        f"{'条件':<25} {'枚数':>5} {'輝度':>8} {'コントラスト':>10} "
        f"{'ハレーション':>10} {'SNR':>8} {'鮮鋭度':>12}"
    )
    print(header)
    print("-" * 80)

    for condition, stats in summary.items():
        label = condition.replace("_", " ").title()
        print(
            f"{label:<25} {stats['num_images']:>5.0f} "
            f"{stats['avg_brightness']:>8.1f} "
            f"{stats['avg_contrast_rms']:>10.1f} "
            f"{stats['avg_halation_ratio']:>10.4f} "
            f"{stats['avg_snr']:>8.2f} "
            f"{stats['avg_edge_sharpness']:>12.1f}"
        )

    print("=" * 80)

    # 推奨条件の判定
    if summary:
        best = min(summary.items(), key=lambda x: x[1]["avg_halation_ratio"])
        print(f"\n推奨: '{best[0]}' (ハレーション率が最も低い)")

        best_contrast = max(summary.items(), key=lambda x: x[1]["avg_contrast_rms"])
        print(f"高コントラスト: '{best_contrast[0]}'")

    print()


def main() -> None:
    """CLIエントリーポイント"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="照明条件比較ツール — 白色/赤色 × 拡散板の評価"
    )
    parser.add_argument(
        "-d", "--data-dir",
        type=str,
        default="data/lighting_test",
        help="照明テスト画像のルートディレクトリ (default: data/lighting_test)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="data/lighting_test/results.csv",
        help="結果CSV出力パス (default: data/lighting_test/results.csv)",
    )
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=LIGHTING_CONDITIONS,
        help="評価する照明条件のリスト",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error("データディレクトリが見つかりません: %s", data_dir)
        logger.info(
            "以下のディレクトリ構成で画像を配置してください:\n"
            "  %s/\n"
            "  ├── white_no_diffuser/\n"
            "  ├── white_with_diffuser/\n"
            "  ├── red_no_diffuser/\n"
            "  └── red_with_diffuser/",
            data_dir,
        )
        return

    all_metrics: list[ImageMetrics] = []
    for condition in args.conditions:
        metrics = analyze_condition(data_dir, condition)
        all_metrics.extend(metrics)

    if not all_metrics:
        logger.error("解析可能な画像がありません")
        return

    summary = generate_summary(all_metrics)
    print_report(summary)

    output_path = Path(args.output)
    export_csv(all_metrics, output_path)

    logger.info("解析完了: 合計 %d 枚の画像を処理", len(all_metrics))


if __name__ == "__main__":
    main()
