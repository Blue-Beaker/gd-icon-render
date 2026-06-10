from gdicons import set_resources_path, render_icon
import os,sys
from pathlib import Path

set_resources_path(Path(sys.path[0])/"Resources")

render_icon(
    gamemode  = "cube",
    id        = 133,
    primary   = "#ffff00",
    secondary = "#b900ff",
    glow      = "#b900ff"
)
