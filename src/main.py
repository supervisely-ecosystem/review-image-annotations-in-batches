import supervisely as sly
from supervisely.app.widgets import Container

import src.ui.control_panel as control_panel
import src.ui.workbench as workbench
from src.ui.apply_css.apply_style import ApplyCss

layout = Container(
    widgets=[
        control_panel.card,
        workbench.card,
    ]
)

app = sly.Application(layout=ApplyCss("./static/css/styles.css", layout), static_dir="static")
