st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)
from dataclasses import dataclass
import os
import random
import sys
import time
from typing import Iterator, List


@dataclass
class Snowflake:
    """雪花粒子物件：封裝座標與物理速度"""

    x: float
    y: float
    vy: float  # 垂直掉落速度
    vx: float  # 水平飄移速度
    char: str

    def update(self, wind: float, width: int, height: int) -> None:
        self.y += self.vy
        self.x = (self.x + self.vx + wind) % width
        # 落地後重置到頂端並隨機微調速度
        if self.y >= height:
            self.y = 0.0
            self.x = random.uniform(0, width - 1)
            self.vy = random.uniform(0.3, 0.8)


class ChristmasScene:
    """聖誕場景引擎：負責畫布渲染、樹體生成與粒子物理模擬"""

    # ANSI 終端機顏色代碼
    COLORS = {
        "RESET": "\033[0m",
        "GREEN": "\033[32m",
        "BRIGHT_GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "RED": "\033[91m",
        "CYAN": "\033[96m",
        "MAGENTA": "\033[95m",
        "WHITE": "\033[97m",
        "BROWN": "\033[33m",
    }
    ORNAMENT_COLORS = ["RED", "YELLOW", "CYAN", "MAGENTA"]

    def __init__(
        self,
        width: int = 60,
        height: int = 24,
        tree_height: int = 15,
        snow_count: int = 45,
    ):
        self.width = width
        self.height = height
        self.tree_height = tree_height
        self.wind = 0.0
        self.snowflakes: List[Snowflake] = [
            Snowflake(
                x=random.uniform(0, width - 1),
                y=random.uniform(0, height - 1),
                vy=random.uniform(0.3, 0.8),
                vx=random.uniform(-0.2, 0.2),
                char=random.choice(["*", ".", "❄", "·"]),
            )
            for _ in range(snow_count)
        ]

    def _wind_generator(self) -> Iterator[float]:
        """生成器：模擬自然界陣風的平滑變化"""
        target_wind = 0.0
        while True:
            if random.random() < 0.08:
                target_wind = random.uniform(-0.6, 0.6)
            # 線性插值平滑過渡風速
            self.wind += (target_wind - self.wind) * 0.1
            yield self.wind

    def _build_tree_layer(self, canvas: List[List[str]]) -> None:
        """在二維字元畫布上繪製聖誕樹與動態閃爍彩燈"""
        center_x = self.width // 2
        start_y = self.height - self.tree_height - 4

        # 1. 樹頂星星 (閃爍特效)
        star_color = (
            self.COLORS["YELLOW"] if random.random() > 0.2 else self.COLORS["WHITE"]
        )
        canvas[start_y - 1][center_x] = f"{star_color}★{self.COLORS['RESET']}"

        # 2. 樹冠與隨機彩燈
        for row in range(self.tree_height):
            y = start_y + row
            span = row + 1
            for dx in range(-span + 1, span):
                x = center_x + dx
                if 0 <= x < self.width and 0 <= y < self.height:
                    if random.random() < 0.16:
                        c_key = random.choice(self.ORNAMENT_COLORS)
                        bulb = random.choice(["●", "✦", "o"])
                        canvas[y][x] = f"{self.COLORS[c_key]}{bulb}{self.COLORS['RESET']}"
                    else:
                        leaf_color = (
                            self.COLORS["BRIGHT_GREEN"]
                            if (row + dx) % 2 == 0
                            else self.COLORS["GREEN"]
                        )
                        canvas[y][x] = f"{leaf_color}^{self.COLORS['RESET']}"

        # 3. 樹幹
        trunk_width = 3
        trunk_height = 3
        for ty in range(trunk_height):
            y = start_y + self.tree_height + ty
            for tx in range(-(trunk_width // 2), (trunk_width // 2) + 1):
                x = center_x + tx
                if 0 <= x < self.width and 0 <= y < self.height:
                    canvas[y][x] = f"{self.COLORS['BROWN']}|{self.COLORS['RESET']}"

    def render_frame(self, current_wind: float) -> str:
        """合成單一影格並回傳完整字串緩衝區"""
        canvas = [[" " for _ in range(self.width)] for _ in range(self.height)]

        # 先繪製背景雪花
        for flake in self.snowflakes:
            flake.update(current_wind, self.width, self.height)
            ix, iy = int(flake.x), int(flake.y)
            if 0 <= ix < self.width and 0 <= iy < self.height:
                canvas[iy][ix] = f"{self.COLORS['WHITE']}{flake.char}{self.COLORS['RESET']}"

        # 再疊加聖誕樹前景（遮罩層次感）
        self._build_tree_layer(canvas)

        # 底部祝福標語置中
        msg = "✨ MERRY CHRISTMAS & HAPPY NEW YEAR ✨"
        msg_x = max(0, (self.width - len(msg)) // 2)
        for idx, ch in enumerate(msg):
            if msg_x + idx < self.width:
                canvas[self.height - 1][msg_x + idx] = (
                    f"{self.COLORS['YELLOW']}{ch}{self.COLORS['RESET']}"
                )

        return "\n".join("".join(row) for row in canvas)

    def run(self, fps: int = 12) -> None:
        """啟動主渲染迴圈，使用 ANSI 游標歸位避免畫面閃爍"""
        wind_stream = self._wind_generator()
        # 隱藏終端機游標並清空畫面
        sys.stdout.write("\033[?25l\033[2J")
        try:
            while True:
                frame = self.render_frame(next(wind_stream))
                # \033[H 將游標移回左上角覆寫，實現無閃爍雙緩衝渲染
                sys.stdout.write(f"\033[H{frame}")
                sys.stdout.flush()
                time.sleep(1.0 / fps)
        except KeyboardInterrupt:
            pass
        finally:
            # 恢復終端機游標顯示
            sys.stdout.write("\033[?25h\n🎄 動畫已結束，祝聖誕快樂！\n")


if __name__ == "__main__":
    # Windows 終端機啟用 ANSI 顏色支援
    if os.name == "nt":
        os.system("")
    scene = ChristmasScene(width=64, height=25, tree_height=15, snow_count=55)
    scene.run(fps=12)
