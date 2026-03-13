"""システム設定 — 光学パラメータ・カメラ・搬送の一元管理"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CameraConfig:
    """IDS GV-50C0CP-C-HQ Rev.2.2 カメラ設定"""

    width: int = 1936
    height: int = 1216
    pixel_format: str = "BayerRG8"
    exposure_us: float = 5000.0
    gain_db: float = 0.0
    buffer_count: int = 8
    trigger_mode: str = "Off"
    trigger_source: str = "Line0"
    trigger_activation: str = "RisingEdge"


@dataclass(frozen=True)
class OpticsConfig:
    """光学・設置パラメータ"""

    working_distance_mm: float = 240.0
    fov_width_mm: float = 200.0
    fov_height_mm: float = 126.0
    spatial_resolution_mm_per_pixel: float = 0.103
    lens_focal_length_mm: float = 8.0


@dataclass(frozen=True)
class ConveyorConfig:
    """搬送系パラメータ"""

    speed_m_per_min: float = 10.0
    max_lumber_length_mm: float = 4000.0
    lumber_width_mm: float = 150.0

    @property
    def speed_mm_per_sec(self) -> float:
        return self.speed_m_per_min * 1000.0 / 60.0


@dataclass(frozen=True)
class CaptureConfig:
    """画像保存設定"""

    output_dir: Path = field(default_factory=lambda: Path("data/captures"))
    image_format: str = "png"
    save_raw: bool = False


@dataclass(frozen=True)
class SystemConfig:
    """システム全体の統合設定"""

    camera: CameraConfig = field(default_factory=CameraConfig)
    optics: OpticsConfig = field(default_factory=OpticsConfig)
    conveyor: ConveyorConfig = field(default_factory=ConveyorConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)

    @property
    def frames_needed_for_full_length(self) -> int:
        """材全長をカバーするのに必要なフレーム数（オーバーラップなし）"""
        return int(
            self.conveyor.max_lumber_length_mm / self.optics.fov_width_mm
        ) + 1

    @property
    def trigger_interval_mm(self) -> float:
        """フレーム間の搬送距離（FOV幅に一致）"""
        return self.optics.fov_width_mm
