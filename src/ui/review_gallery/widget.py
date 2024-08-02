import copy
import time
import uuid
from pathlib import Path
from typing import List, Optional

import markupsafe
import supervisely
from jinja2 import Environment
from supervisely.app import DataJson
from supervisely.app.content import StateJson
from supervisely.app.jinja2 import create_env
from supervisely.app.widgets import GridGallery


class ReviewGallery(GridGallery):

    def __init__(self, edit_tags: Optional[bool] = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._review_state = {}  # states for active switchers

    def to_html(self):
        current_dir = Path(__file__).parent.absolute()
        jinja2_sly_env: Environment = create_env(current_dir)
        html = jinja2_sly_env.get_template("template.html").render({"widget": self})
        html = self._wrap_loading_html(self.widget_id, html)
        html = self._wrap_disable_html(self.widget_id, html)
        html = self._wrap_hide_html(self.widget_id, html)
        return markupsafe.Markup(html)

    def _update_annotations(self):
        annotations = {}
        for cell_data in self._data:
            figures = [label.to_json() for label in cell_data["annotation"].labels]
            class_titles = list(set(figure["classTitle"] for figure in figures))
            rgb_class_colors = [self._task_meta.get_obj_class(name).color for name in class_titles]
            class_colors = [f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})" for rgb in rgb_class_colors]
            class_data = [
                {"title": title, "color": color} for title, color in zip(class_titles, class_colors)
            ]

            img_tags = [
                {"tagId": tag["tagId"], "value": tag.get("value", None)}
                for tag in cell_data["tags"]
            ]
            # img_tag_ids = [tag["tagId"] for tag in cell_data["tags"]]
            tag_titles = [self._task_meta.get_tag_meta_by_id(tag["tagId"]).name for tag in img_tags]
            rgb_tag_colors = [
                self._task_meta.get_tag_meta_by_id(tag["tagId"]).color for tag in img_tags
            ]
            tag_values = [tag["value"] for tag in img_tags]
            tag_colors = [f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})" for rgb in rgb_tag_colors]
            tag_data = [
                {"title": title, "color": color, "value": value}
                for title, color, value in zip(tag_titles, tag_colors, tag_values)
            ]

            annotations[cell_data["cell_uuid"]] = {
                "uuid": cell_data["cell_uuid"],
                "image_id": cell_data["image_id"],
                "url": cell_data["image_url"],
                "figures": [label.to_json() for label in cell_data["annotation"].labels],
                "title": cell_data["title"],
                "title_url": cell_data["title_url"],
                "classes": class_data,
                "tags": tag_data,
            }
            if not cell_data["zoom_to"] is None:
                zoom_params = {
                    "figureId": cell_data["zoom_to"],
                    "factor": cell_data["zoom_factor"],
                }
                annotations[cell_data["cell_uuid"]]["zoomToFigure"] = zoom_params
        self._annotations = copy.deepcopy(annotations)
        DataJson()[self.widget_id]["content"]["annotations"] = self._annotations

    def append(
        self,
        image_info: supervisely.ImageInfo,
        annotation: supervisely.Annotation = None,
        title: str = "",
        column_index: int = None,
        zoom_to: int = None,
        zoom_factor: float = 1.2,
        title_url=None,
        project_meta: supervisely.ProjectMeta = None,
    ):

        self._task_meta = project_meta

        column_index = self.get_column_index(incoming_value=column_index)
        cell_uuid = str(
            uuid.uuid5(
                namespace=uuid.NAMESPACE_URL,
                name=f"{image_info.preview_url}_{title}_{column_index}_{time.time()}",
            ).hex
        )

        self._data.append(
            {
                "image_url": image_info.preview_url,
                "image_id": image_info.id,
                "annotation": (
                    supervisely.Annotation((1, 1)) if annotation is None else annotation.clone()
                ),
                "column_index": column_index,
                "title": (
                    title if title_url is None else title + ' <i class="zmdi zmdi-open-in-new"></i>'
                ),
                "cell_uuid": cell_uuid,
                "zoom_to": zoom_to,
                "zoom_factor": zoom_factor,
                "title_url": title_url,
                "tags": image_info.tags,
            }
        )
        self._review_state.update({image_info.id: True})
        self._update()
        return cell_uuid

    def _update(self):
        self._update_layout()
        self._update_project_meta()
        self._update_annotations()
        StateJson()[self.widget_id]["reviewState"] = self._review_state
        DataJson().send_changes()
        StateJson().send_changes()

    def get_json_state(self):
        return {
            "options": {
                "showOpacityInHeader": self._show_opacity_header,
                "opacity": self._opacity,
                "enableZoom": self._enable_zoom,
                "syncViews": self._sync_views,
                "syncViewsBindings": self._views_bindings,
                "resizeOnZoom": self._resize_on_zoom,
                "fillRectangle": self._fill_rectangle,
                "borderWidth": self._border_width,
                "selectable": False,
                "viewHeight": self._view_height,
                "showPreview": self._show_preview,
            },
            "selectedImage": None,
            "activeFigure": None,
            "reviewState": None,
        }

    def get_review_state(self):
        return StateJson()[self.widget_id]["reviewState"]
