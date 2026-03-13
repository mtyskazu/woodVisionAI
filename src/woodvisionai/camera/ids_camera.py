"""IDS Peak SDK カメララッパー

IDS GV-50C0CP-C-HQ (GigE Vision) を制御するための高レベルAPI。
初期化 → 設定 → 撮像 → 解放 のライフサイクルを管理する。
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import numpy as np

from woodvisionai.config import CameraConfig

logger = logging.getLogger(__name__)

try:
    from ids_peak import ids_peak
    from ids_peak_ipl import ids_peak_ipl

    IDS_AVAILABLE = True
except ImportError:
    IDS_AVAILABLE = False
    logger.warning(
        "IDS Peak SDK が見つかりません。"
        "シミュレーションモードで動作します。"
        "実カメラを使用する場合は IDS Peak SDK をインストールしてください。"
    )


class IDSCameraError(Exception):
    """IDS カメラ操作エラー"""


class IDSCamera:
    """IDS Peak SDK カメラ制御クラス

    Usage:
        with IDSCamera.open(config) as cam:
            frame = cam.grab_frame()
    """

    def __init__(self, config: CameraConfig | None = None) -> None:
        self._config = config or CameraConfig()
        self._device = None
        self._datastream = None
        self._nodemap = None
        self._is_acquiring = False

    @classmethod
    @contextmanager
    def open(
        cls, config: CameraConfig | None = None
    ) -> Generator[IDSCamera, None, None]:
        """カメラを開いてコンテキストマネージャとして使用する"""
        camera = cls(config)
        try:
            camera.initialize()
            yield camera
        finally:
            camera.close()

    def initialize(self) -> None:
        """SDK初期化 → デバイス検出 → オープン → 設定適用"""
        if not IDS_AVAILABLE:
            raise IDSCameraError(
                "IDS Peak SDK が利用できません。インストールを確認してください。"
            )

        ids_peak.Library.Initialize()
        logger.info("IDS Peak SDK 初期化完了")

        device_manager = ids_peak.DeviceManager.Instance()
        device_manager.Update()

        devices = device_manager.Devices()
        if len(devices) == 0:
            raise IDSCameraError("カメラが検出されません")

        device_descriptor = devices[0]
        logger.info(
            "カメラ検出: %s (S/N: %s)",
            device_descriptor.DisplayName(),
            device_descriptor.SerialNumber(),
        )

        self._device = device_descriptor.OpenDevice(
            ids_peak.DeviceAccessType_Control
        )
        self._nodemap = self._device.RemoteDevice().NodeMaps()[0]

        self._apply_config()
        self._setup_buffers()

        logger.info("カメラ初期化完了")

    def _apply_config(self) -> None:
        """CameraConfig の値をカメラノードマップに適用する"""
        nm = self._nodemap
        cfg = self._config

        self._set_node_value("Width", cfg.width)
        self._set_node_value("Height", cfg.height)

        exposure_node = nm.FindNode("ExposureTime")
        exposure_node.SetValue(
            max(
                exposure_node.Minimum(),
                min(cfg.exposure_us, exposure_node.Maximum()),
            )
        )
        logger.info("露光時間: %.1f µs", cfg.exposure_us)

        if cfg.gain_db > 0:
            gain_node = nm.FindNode("Gain")
            gain_node.SetValue(
                max(
                    gain_node.Minimum(),
                    min(cfg.gain_db, gain_node.Maximum()),
                )
            )
            logger.info("ゲイン: %.1f dB", cfg.gain_db)

        self._configure_trigger()

    def _configure_trigger(self) -> None:
        """トリガーモードの設定（ソフト / ハードウェア）"""
        cfg = self._config
        nm = self._nodemap

        if cfg.trigger_mode == "Off":
            self._set_enum_entry("TriggerMode", "Off")
            logger.info("フリーラン撮像モード")
            return

        self._set_enum_entry("TriggerSelector", "ExposureStart")
        self._set_enum_entry("TriggerMode", "On")
        self._set_enum_entry("TriggerSource", cfg.trigger_source)
        self._set_enum_entry("TriggerActivation", cfg.trigger_activation)
        logger.info(
            "ハードウェアトリガーモード: source=%s, activation=%s",
            cfg.trigger_source,
            cfg.trigger_activation,
        )

    def _setup_buffers(self) -> None:
        """データストリームのバッファを確保する"""
        self._datastream = self._device.DataStreams()[0].OpenDataStream()
        payload_size = self._nodemap.FindNode("PayloadSize").Value()

        for _ in range(self._config.buffer_count):
            buf = self._datastream.AllocAndAnnounceBuffer(payload_size)
            self._datastream.QueueBuffer(buf)

        logger.info(
            "バッファ確保: %d 個 (各 %d bytes)",
            self._config.buffer_count,
            payload_size,
        )

    def start_acquisition(self) -> None:
        """撮像開始"""
        if self._is_acquiring:
            return

        self._datastream.StartAcquisition()
        self._nodemap.FindNode("TLParamsLocked").SetValue(1)
        self._nodemap.FindNode("AcquisitionStart").Execute()
        self._nodemap.FindNode("AcquisitionStart").WaitUntilDone()
        self._is_acquiring = True
        logger.info("撮像開始")

    def stop_acquisition(self) -> None:
        """撮像停止"""
        if not self._is_acquiring:
            return

        self._nodemap.FindNode("AcquisitionStop").Execute()
        self._nodemap.FindNode("AcquisitionStop").WaitUntilDone()
        self._nodemap.FindNode("TLParamsLocked").SetValue(0)
        self._datastream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)

        self._datastream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)
        for buffer in self._datastream.AnnouncedBuffers():
            self._datastream.RevokeBuffer(buffer)

        self._is_acquiring = False
        logger.info("撮像停止")

    def grab_frame(self, timeout_ms: int = 5000) -> np.ndarray:
        """1フレーム取得してRGB numpy配列として返す

        Args:
            timeout_ms: バッファ待機タイムアウト (ms)

        Returns:
            shape (H, W, 3) の uint8 RGB 配列
        """
        if not self._is_acquiring:
            self.start_acquisition()

        buffer = self._datastream.WaitForFinishedBuffer(timeout_ms)
        try:
            ipl_image = ids_peak_ipl.Image.CreateFromSizeAndBuffer(
                buffer.PixelFormat(),
                buffer.BasePtr(),
                buffer.Size(),
                buffer.Width(),
                buffer.Height(),
            )
            rgb_image = ipl_image.ConvertTo(
                ids_peak_ipl.PixelFormatName_RGB8
            )
            frame = rgb_image.get_numpy_3D().copy()
        finally:
            self._datastream.QueueBuffer(buffer)

        return frame

    def close(self) -> None:
        """カメラリソースを解放する"""
        try:
            self.stop_acquisition()
        except Exception:
            pass

        self._datastream = None
        self._nodemap = None

        if self._device is not None:
            self._device = None

        if IDS_AVAILABLE:
            ids_peak.Library.Close()

        logger.info("カメラリソース解放完了")

    def _set_node_value(self, name: str, value: int | float) -> None:
        """ノードの値を安全に設定する"""
        try:
            node = self._nodemap.FindNode(name)
            node.SetValue(value)
        except Exception as e:
            logger.warning("ノード '%s' の設定に失敗: %s", name, e)

    def _set_enum_entry(self, name: str, entry: str) -> None:
        """Enumerationノードのエントリを安全に設定する"""
        try:
            node = self._nodemap.FindNode(name)
            node.SetCurrentEntry(node.FindEntry(entry))
        except Exception as e:
            logger.warning("Enum '%s' → '%s' の設定に失敗: %s", name, entry, e)

    @property
    def is_acquiring(self) -> bool:
        return self._is_acquiring

    @property
    def device_info(self) -> dict[str, str]:
        """接続中デバイスの情報を返す"""
        if self._device is None:
            return {}
        desc = self._device.Descriptor()
        return {
            "model": desc.DisplayName(),
            "serial": desc.SerialNumber(),
            "ip": desc.IPAddress() if hasattr(desc, "IPAddress") else "N/A",
        }
