from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Destination:
    """Một vị trí thả sản phẩm.

    Destination không gắn cứng với màu. Nhiều màu có thể cùng route tới
    một Destination duy nhất.
    """

    id: int
    key: str
    display_name: str
    x: float
    y: float
    z: float
    enabled: bool = True

    def validate(self) -> None:
        if self.id <= 0:
            raise ValueError("Destination ID phải lớn hơn 0")
        if not self.key.strip():
            raise ValueError("Destination key không được để trống")
        if not self.display_name.strip():
            raise ValueError("Tên Destination không được để trống")
