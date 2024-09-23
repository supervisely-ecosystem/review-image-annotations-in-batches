import copy
import time
import uuid
from pathlib import Path
from typing import Literal

import markupsafe
import supervisely
from jinja2 import Environment
from supervisely.app import DataJson
from supervisely.app.content import StateJson
from supervisely.app.jinja2 import create_env
from supervisely.app.widgets import GridGallery


class ReviewGallery(GridGallery):

    def __init__(
        self,
        edit_tags: bool = False,
        default_review_state: Literal["accept", "reject", "ignore"] = "accept",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._default_review_state = default_review_state
        self._edit_tags = edit_tags
        self._review_states = {}  # states for active switchers
        self._tag_values = {}  # values for active tags
        self._tag_change_states = {}  # for fast checking if tag value was changed

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
            "reviewStates": None,
            "tagValues": None,
            "tagChangeStates": None,
            "editTags": None,
        }

    def to_html(self):
        current_dir = Path(__file__).parent.absolute()
        jinja2_sly_env: Environment = create_env(current_dir)
        html = jinja2_sly_env.get_template("template.html").render({"widget": self})
        html = self._wrap_loading_html(self.widget_id, html)
        html = self._wrap_disable_html(self.widget_id, html)
        html = self._wrap_hide_html(self.widget_id, html)
        return markupsafe.Markup(html)

    def edit_tags(self, value: bool):
        self._edit_tags = value
        StateJson()[self.widget_id]["editTags"] = self._edit_tags
        StateJson().send_changes()

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
                "image_name": image_info.name,
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
        self._review_states.update({image_info.id: self._default_review_state})
        self._tag_values.update({tag["id"]: tag.get("value", None) for tag in image_info.tags})
        self._update()
        return cell_uuid

    def _update(self):
        self._update_layout()
        self._update_project_meta()
        self._update_annotations()
        StateJson()[self.widget_id]["reviewStates"] = self._review_states
        StateJson()[self.widget_id]["tagValues"] = self._tag_values
        StateJson()[self.widget_id]["tagChangeStates"] = self._tag_change_states
        DataJson().send_changes()
        StateJson().send_changes()

    def _update_annotations(self):
        annotations = {}
        for cell_data in self._data:
            # ---------------------------------------- Prepare Classes --------------------------------------- #
            figures = [label.to_json() for label in cell_data["annotation"].labels]
            class_titles = list(set(figure["classTitle"] for figure in figures))
            rgb_class_colors = [self._task_meta.get_obj_class(name).color for name in class_titles]
            class_colors = [f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})" for rgb in rgb_class_colors]
            classes_data = [
                {"title": title, "color": color} for title, color in zip(class_titles, class_colors)
            ]
            # ----------------------------------------- Prepare Tags ----------------------------------------- #
            img_tags = [
                {"id": tag["id"], "tag_id": tag["tagId"], "value": tag.get("value", None)}
                for tag in cell_data["tags"]
            ]

            tags_data = []
            for tag in img_tags:
                tag_meta = self._task_meta.get_tag_meta_by_id(tag["tag_id"])
                if not tag_meta:
                    continue
                tags_data.append(
                    {
                        "id": tag["id"],
                        "title": tag_meta.name,
                        "color": f"rgb({tag_meta.color[0]}, {tag_meta.color[1]}, {tag_meta.color[2]})",
                        "value": tag["value"],
                        "type": tag_meta.value_type,
                        "options": (
                            tag_meta.possible_values
                            if tag_meta.value_type == "oneof_string"
                            else None
                        ),
                    }
                )
            # -------------------------------------- Prepare Annotation -------------------------------------- #
            annotations[cell_data["cell_uuid"]] = {
                "uuid": cell_data["cell_uuid"],
                "image_id": cell_data["image_id"],
                "image_name": cell_data["image_name"],
                "url": cell_data["image_url"],
                "figures": [label.to_json() for label in cell_data["annotation"].labels],
                "title": cell_data["title"],
                "title_url": cell_data["title_url"],
                "classes": classes_data,
                "tags": tags_data,
            }
            if not cell_data["zoom_to"] is None:
                zoom_params = {
                    "figureId": cell_data["zoom_to"],
                    "factor": cell_data["zoom_factor"],
                }
                annotations[cell_data["cell_uuid"]]["zoomToFigure"] = zoom_params
        self._annotations = copy.deepcopy(annotations)
        DataJson()[self.widget_id]["content"]["annotations"] = self._annotations

    def get_review_states(self):
        return StateJson()[self.widget_id]["reviewStates"]

    def get_tag_values(self):
        return StateJson()[self.widget_id]["tagValues"]

    def get_tag_change_states(self):
        return StateJson()[self.widget_id]["tagChangeStates"]

    def set_default_review_state(self, state: Literal["accept", "reject", "ignore"]):
        self._default_review_state = state

    def clean_states(self):
        self._review_states = {}
        self._tag_values = {}
        self._tag_change_states = {}
        StateJson()[self.widget_id]["reviewStates"] = self._review_states
        StateJson()[self.widget_id]["tagValues"] = self._tag_values
        StateJson()[self.widget_id]["tagChangeStates"] = self._tag_change_states
        StateJson().send_changes()
