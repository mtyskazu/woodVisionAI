"""照明テスト撮像スクリプト

指定した条件名で複数フレームを撮像し、対応するフォルダに保存する。

使い方:
  python tools/capture_lighting_test.py --condition white_with_diffuser
  python tools/capture_lighting_test.py --condition white_no_diffuser
  python tools/capture_lighting_test.py --condition red_with_diffuser
  python tools/capture_lighting_test.py --condition red_no_diffuser
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

VALID_CONDITIONS = [
    "white_no_diffuser",
    "white_with_diffuser",
    "red_no_diffuser",
    "red_with_diffuser",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="照明テスト撮像")
    parser.add_argument(
        "-c", "--condition",
        type=str,
        required=True,
        choices=VALID_CONDITIONS,
        help="照明条件名",
    )
    parser.add_argument(
        "-n", "--num-frames",
        type=int,
        default=5,
        help="撮像フレーム数 (default: 5)",
    )
    parser.add_argument(
        "-d", "--data-dir",
        type=str,
        default="data/lighting_test",
        help="保存先ルート (default: data/lighting_test)",
    )
    args = parser.parse_args()

    from ids_peak import ids_peak
    from ids_peak_ipl import ids_peak_ipl

    ids_peak.Library.Initialize()
    dm = ids_peak.DeviceManager.Instance()
    dm.Update()

    if len(dm.Devices()) == 0:
        print("ERROR: カメラが検出されません")
        ids_peak.Library.Close()
        return

    device = dm.Devices()[0].OpenDevice(ids_peak.DeviceAccessType_Control)
    nodemap = device.RemoteDevice().NodeMaps()[0]

    width = nodemap.FindNode("Width").Value()
    height = nodemap.FindNode("Height").Value()
    exposure = nodemap.FindNode("ExposureTime").Value()

    print(f"カメラ: {dm.Devices()[0].DisplayName()}")
    print(f"解像度: {width} x {height}")
    print(f"露光時間: {exposure:.1f} us")
    print(f"条件: {args.condition}")
    print()

    ds = device.DataStreams()[0].OpenDataStream()
    payload_size = nodemap.FindNode("PayloadSize").Value()
    for _ in range(8):
        buf = ds.AllocAndAnnounceBuffer(payload_size)
        ds.QueueBuffer(buf)

    ds.StartAcquisition()
    nodemap.FindNode("TLParamsLocked").SetValue(1)
    nodemap.FindNode("AcquisitionStart").Execute()
    nodemap.FindNode("AcquisitionStart").WaitUntilDone()

    output_dir = Path(args.data_dir) / args.condition
    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(args.num_frames):
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

        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        mean_b = float(np.mean(gray))
        std_b = float(np.std(gray))
        halation = float(np.sum(gray > 250)) / gray.size

        filename = f"{args.condition}_{i + 1:03d}.png"
        filepath = output_dir / filename
        cv2.imwrite(str(filepath), bgr)

        print(
            f"  [{i + 1}/{args.num_frames}] {filename}"
            f"  輝度={mean_b:.1f}  SD={std_b:.1f}  ハレーション={halation:.4f}"
        )

    nodemap.FindNode("AcquisitionStop").Execute()
    nodemap.FindNode("AcquisitionStop").WaitUntilDone()
    nodemap.FindNode("TLParamsLocked").SetValue(0)
    ds.StopAcquisition(ids_peak.AcquisitionStopMode_Default)
    ds.Flush(ids_peak.DataStreamFlushMode_DiscardAll)
    for b in ds.AnnouncedBuffers():
        ds.RevokeBuffer(b)

    ids_peak.Library.Close()

    print()
    print(f"完了: {args.num_frames} 枚を {output_dir} に保存")


if __name__ == "__main__":
    main()
