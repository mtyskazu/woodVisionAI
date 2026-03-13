"""キャプチャスレッド — 連続撮像とフレーム配信

Capture Thread はカメラからフレームを取得し、
スレッドセーフなキューを介して後段（推論・保存）にフレームを配信する。
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Full, Queue
from typing import Callable

import cv2
import numpy as np

from woodvisionai.camera.ids_camera import IDSCamera, IDSCameraError, IDS_AVAILABLE
from woodvisionai.config import CameraConfig, CaptureConfig, SystemConfig

logger = logging.getLogger(__name__)


@dataclass
class CapturedFrame:
    """キャプチャされたフレームのメタデータ付きコンテナ"""

    image: np.ndarray
    frame_id: int
    timestamp: float
    position_mm: float | None = None


class CaptureThread:
    """カメラからフレームを連続取得するワーカースレッド

    Args:
        config: システム設定
        frame_queue: フレームを配信するキュー
        max_frames: 最大取得フレーム数（0 = 無制限）
        on_frame: フレーム取得時のコールバック（GUI更新などに使用）
    """

    def __init__(
        self,
        config: SystemConfig | None = None,
        frame_queue: Queue[CapturedFrame] | None = None,
        max_frames: int = 0,
        on_frame: Callable[[CapturedFrame], None] | None = None,
    ) -> None:
        self._config = config or SystemConfig()
        self._queue = frame_queue or Queue(maxsize=16)
        self._max_frames = max_frames
        self._on_frame = on_frame

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._frame_count = 0
        self._camera: IDSCamera | None = None

    def start(self) -> None:
        """キャプチャスレッドを開始する"""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("キャプチャスレッドは既に動作中です")
            return

        self._stop_event.clear()
        self._frame_count = 0
        self._thread = threading.Thread(
            target=self._run, name="CaptureThread", daemon=True
        )
        self._thread.start()
        logger.info("キャプチャスレッド開始")

    def stop(self, timeout: float = 5.0) -> None:
        """キャプチャスレッドを停止する"""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning("キャプチャスレッドの停止がタイムアウトしました")
        self._thread = None
        logger.info("キャプチャスレッド停止 (取得フレーム数: %d)", self._frame_count)

    def _run(self) -> None:
        """スレッド本体 — カメラからフレームを取得しキューに送る"""
        try:
            self._camera = IDSCamera(self._config.camera)
            self._camera.initialize()
            self._camera.start_acquisition()
            logger.info("カメラ撮像開始")

            while not self._stop_event.is_set():
                if 0 < self._max_frames <= self._frame_count:
                    break

                try:
                    raw_frame = self._camera.grab_frame(timeout_ms=5000)
                except IDSCameraError as e:
                    logger.error("フレーム取得エラー: %s", e)
                    continue

                self._frame_count += 1
                captured = CapturedFrame(
                    image=raw_frame,
                    frame_id=self._frame_count,
                    timestamp=time.time(),
                )

                try:
                    self._queue.put_nowait(captured)
                except Full:
                    logger.debug("フレームキューが満杯 — フレーム %d をドロップ", self._frame_count)

                if self._on_frame is not None:
                    try:
                        self._on_frame(captured)
                    except Exception:
                        logger.exception("on_frame コールバックでエラー")

        except IDSCameraError as e:
            logger.error("カメラ初期化エラー: %s", e)
        except Exception:
            logger.exception("キャプチャスレッドで予期しないエラー")
        finally:
            if self._camera is not None:
                self._camera.close()
                self._camera = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def queue(self) -> Queue[CapturedFrame]:
        return self._queue


def save_frame(frame: CapturedFrame, output_dir: Path, fmt: str = "png") -> Path:
    """フレームをファイルに保存する"""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"frame_{frame.frame_id:06d}.{fmt}"
    filepath = output_dir / filename

    bgr = cv2.cvtColor(frame.image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(filepath), bgr)

    logger.debug("フレーム保存: %s", filepath)
    return filepath


def main() -> None:
    """CLI エントリーポイント — テスト撮像"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="woodVisionAI キャプチャテスト")
    parser.add_argument(
        "-n", "--num-frames", type=int, default=10,
        help="取得フレーム数 (default: 10)",
    )
    parser.add_argument(
        "-o", "--output", type=str, default="data/captures",
        help="出力ディレクトリ (default: data/captures)",
    )
    parser.add_argument(
        "-e", "--exposure", type=float, default=5000.0,
        help="露光時間 µs (default: 5000)",
    )
    parser.add_argument(
        "--trigger", action="store_true",
        help="ハードウェアトリガーモードを有効にする",
    )
    args = parser.parse_args()

    cam_cfg = CameraConfig(
        exposure_us=args.exposure,
        trigger_mode="On" if args.trigger else "Off",
    )
    cap_cfg = CaptureConfig(output_dir=Path(args.output))
    config = SystemConfig(camera=cam_cfg, capture=cap_cfg)

    if not IDS_AVAILABLE:
        logger.error(
            "IDS Peak SDK が利用できません。"
            "SDK をインストールして再実行してください。"
        )
        return

    queue: Queue[CapturedFrame] = Queue(maxsize=16)
    capture = CaptureThread(
        config=config, frame_queue=queue, max_frames=args.num_frames
    )

    capture.start()
    saved = 0
    try:
        while capture.is_running or not queue.empty():
            try:
                frame = queue.get(timeout=1.0)
                path = save_frame(frame, config.capture.output_dir)
                saved += 1
                logger.info(
                    "フレーム %d/%d 保存完了: %s",
                    saved, args.num_frames, path,
                )
            except Exception:
                pass
    except KeyboardInterrupt:
        logger.info("中断されました")
    finally:
        capture.stop()

    logger.info("完了: %d フレーム保存", saved)


if __name__ == "__main__":
    main()
