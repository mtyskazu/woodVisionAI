"""システム診断ツール — 環境・カメラ・撮像の一括検証

使い方:
  python tools/diagnose.py           # 環境チェック + カメラ検出
  python tools/diagnose.py --capture # 上記 + テスト撮像（カメラ接続時）
"""

from __future__ import annotations

import argparse
import logging
import platform
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

DIVIDER = "-" * 60


def check_python() -> bool:
    ver = platform.python_version()
    ok = sys.version_info >= (3, 10)
    status = "OK" if ok else "NG (3.10以上が必要)"
    print(f"  Python:          {ver}  [{status}]")
    return ok


def check_package(name: str, import_name: str | None = None) -> bool:
    import_name = import_name or name
    try:
        mod = __import__(import_name)
        ver = getattr(mod, "__version__", "N/A")
        print(f"  {name:<18} {ver:<20} [OK]")
        return True
    except ImportError:
        print(f"  {name:<18} {'未インストール':<20} [NG]")
        return False


def check_cuda() -> bool:
    try:
        import torch

        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"  CUDA:            利用可能")
            print(f"  GPU:             {device_name}")
            print(f"  VRAM:            {vram:.1f} GB")
            return True
        else:
            print(f"  CUDA:            利用不可 [NG]")
            return False
    except ImportError:
        print(f"  CUDA:            PyTorch未インストール [NG]")
        return False


def check_ids_sdk() -> bool:
    try:
        from ids_peak import ids_peak

        print(f"  ids_peak:        インポート成功 [OK]")
    except ImportError:
        print(f"  ids_peak:        未インストール [NG]")
        return False

    try:
        from ids_peak_ipl import ids_peak_ipl

        print(f"  ids_peak_ipl:    インポート成功 [OK]")
    except ImportError:
        print(f"  ids_peak_ipl:    未インストール [NG]")
        return False

    return True


def detect_cameras() -> list[dict[str, str]]:
    """接続カメラの検出"""
    try:
        from ids_peak import ids_peak
    except ImportError:
        print("  IDS Peak SDK が利用できません")
        return []

    ids_peak.Library.Initialize()
    try:
        dm = ids_peak.DeviceManager.Instance()
        dm.Update()

        devices = dm.Devices()
        print(f"\n  検出カメラ数: {len(devices)}")

        results = []
        for i, dev in enumerate(devices):
            info = {
                "index": str(i),
                "name": dev.DisplayName(),
                "model": dev.ModelName(),
                "serial": dev.SerialNumber(),
                "interface": dev.ParentInterface().DisplayName(),
            }
            results.append(info)
            print(f"\n  [{i}] {info['name']}")
            print(f"      Model:     {info['model']}")
            print(f"      Serial:    {info['serial']}")
            print(f"      Interface: {info['interface']}")

        if len(devices) == 0:
            print("  カメラが接続されていません。")
            print("  - GigE: ネットワークケーブルとIPアドレス設定を確認")
            print("  - USB:  USB3ケーブルの接続を確認")
            print("  - IDS Peak Cockpit でカメラが認識されるか確認")

        return results
    finally:
        ids_peak.Library.Close()


def test_capture(output_dir: Path) -> bool:
    """テスト撮像 — 1フレーム取得して保存"""
    try:
        from ids_peak import ids_peak
        from ids_peak_ipl import ids_peak_ipl
    except ImportError:
        print("  IDS Peak SDK が利用できません")
        return False

    import cv2

    ids_peak.Library.Initialize()
    try:
        dm = ids_peak.DeviceManager.Instance()
        dm.Update()

        if len(dm.Devices()) == 0:
            print("  カメラ未接続のためスキップ")
            return False

        device = dm.Devices()[0].OpenDevice(ids_peak.DeviceAccessType_Control)
        nodemap = device.RemoteDevice().NodeMaps()[0]

        width = nodemap.FindNode("Width").Value()
        height = nodemap.FindNode("Height").Value()
        pixel_format = nodemap.FindNode("PixelFormat").CurrentEntry().SymbolicValue()
        exposure = nodemap.FindNode("ExposureTime").Value()

        print(f"  解像度:    {width} x {height}")
        print(f"  PixelFormat: {pixel_format}")
        print(f"  露光時間:  {exposure:.1f} us")

        ds = device.DataStreams()[0].OpenDataStream()
        payload_size = nodemap.FindNode("PayloadSize").Value()

        for _ in range(4):
            buf = ds.AllocAndAnnounceBuffer(payload_size)
            ds.QueueBuffer(buf)

        ds.StartAcquisition()
        nodemap.FindNode("TLParamsLocked").SetValue(1)
        nodemap.FindNode("AcquisitionStart").Execute()
        nodemap.FindNode("AcquisitionStart").WaitUntilDone()

        buffer = ds.WaitForFinishedBuffer(5000)
        ipl_image = ids_peak_ipl.Image.CreateFromSizeAndBuffer(
            buffer.PixelFormat(),
            buffer.BasePtr(),
            buffer.Size(),
            buffer.Width(),
            buffer.Height(),
        )
        rgb_image = ipl_image.ConvertTo(ids_peak_ipl.PixelFormatName_RGB8)
        frame = rgb_image.get_numpy_3D().copy()
        ds.QueueBuffer(buffer)

        nodemap.FindNode("AcquisitionStop").Execute()
        nodemap.FindNode("AcquisitionStop").WaitUntilDone()
        nodemap.FindNode("TLParamsLocked").SetValue(0)
        ds.StopAcquisition(ids_peak.AcquisitionStopMode_Default)
        ds.Flush(ids_peak.DataStreamFlushMode_DiscardAll)
        for b in ds.AnnouncedBuffers():
            ds.RevokeBuffer(b)

        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_dir / f"test_{timestamp}.png"

        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(filepath), bgr)

        mean_val = np.mean(frame)
        std_val = np.std(frame)
        print(f"\n  撮像成功!")
        print(f"  画像サイズ:  {frame.shape}")
        print(f"  平均輝度:    {mean_val:.1f}")
        print(f"  輝度標準偏差: {std_val:.1f}")
        print(f"  保存先:      {filepath}")
        return True

    except Exception as e:
        print(f"  撮像エラー: {e}")
        return False
    finally:
        ids_peak.Library.Close()


def main() -> None:
    parser = argparse.ArgumentParser(description="woodVisionAI システム診断")
    parser.add_argument(
        "--capture", action="store_true",
        help="テスト撮像を実行する",
    )
    parser.add_argument(
        "-o", "--output", type=str, default="data/captures",
        help="テスト撮像の保存先 (default: data/captures)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  woodVisionAI システム診断")
    print(f"  実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Python環境
    print(f"\n[1/4] Python 環境")
    print(DIVIDER)
    check_python()
    print(f"  OS:              {platform.platform()}")

    # 2. パッケージ
    print(f"\n[2/4] パッケージ")
    print(DIVIDER)
    check_package("numpy")
    check_package("opencv-python", "cv2")
    check_package("Pillow", "PIL")
    check_package("torch")
    check_package("torchvision")
    check_ids_sdk()
    check_cuda()

    # 3. カメラ
    print(f"\n[3/4] カメラ検出")
    print(DIVIDER)
    cameras = detect_cameras()

    # 4. テスト撮像
    print(f"\n[4/4] テスト撮像")
    print(DIVIDER)
    if args.capture:
        if cameras:
            test_capture(Path(args.output))
        else:
            print("  カメラ未接続のためスキップ")
    else:
        print("  --capture オプションで実行可能")

    print(f"\n{'=' * 60}")
    print("  診断完了")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
