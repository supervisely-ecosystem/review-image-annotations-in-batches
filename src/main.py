import supervisely as sly
from supervisely.app.widgets import Container

import src.globals as g
import src.ui.control_panel as control_panel
import src.ui.workbench as workbench

layout = Container(
    widgets=[
        control_panel.card,
        workbench.card,
    ]
)

app = sly.Application(layout=layout)
