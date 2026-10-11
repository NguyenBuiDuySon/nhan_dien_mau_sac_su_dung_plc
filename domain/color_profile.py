from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class HSVRange:
    """Một dải HSV theo chuẩn OpenCV: H 0..179, S/V 0..255."""

    lower: tuple[int, int, int]
    upper: tuple[int, int, int]

    def validate(self) -> None:
        limits = ((0, 179), (0, 255), (0, 255))
        for index, ((low_limit, high_limit), low, high) in enumerate(
            zip(limits, self.lower, self.upper, strict=True)
        ):
            if not low_limit <= low <= high_limit:
                raise ValueError(f"HSV lower[{index}] nằm ngoài giới hạn")
            if not low_limit <= high <= high_limit:
                raise ValueError(f"HSV upper[{index}] nằm ngoài giới hạn")
            if low > high:
                raise ValueError(f"HSV lower[{index}] không được lớn hơn upper[{index}]")


@dataclass(slots=True)
class ColorProfile:
    """Cấu hình một màu nhận diện, độc lập hoàn toàn với vị trí thả."""

    id: int
    key: str
    display_name: str
    ui_color: str
    enabled: bool = True
    hsv_ranges: list[HSVRange] = field(default_factory=list)
    min_confidence: float | None = None

    def validate(self) -> None:
        if self.id <= 0:
            raise ValueError("Color ID phải lớn hơn 0")
        if not self.key.strip():
            raise ValueError("Color key không được để trống")
        if not self.display_name.strip():
            raise ValueError("Tên hiển thị màu không được để trống")
        if not self.hsv_ranges:
            raise ValueError("Mỗi màu phải có ít nhất một dải HSV")
        for hsv_range in self.hsv_ranges:
            hsv_range.validate()
        if self.min_confidence is not None and not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence phải nằm trong 0..1")
