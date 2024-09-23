import os
from dataclasses import dataclass
from typing import List

import supervisely as sly
from dotenv import load_dotenv
from supervisely.api.labeling_job_api import LabelingJobInfo

from src.ui.review_gallery.widget import ReviewGallery

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()

selected_job = os.environ.get("modal.state.slyJobId", None)


@dataclass
class Settings:
    batch_size: int
    group_by: str
    tags: List[sly.Tag]
    classes: List[sly.ObjClass]
    filter_images: bool
    tags_editing: bool
    default_decision: str


# ----------------------------------------- Init Section ----------------------------------------- #
job_info: LabelingJobInfo = None
job_ds_info: sly.DatasetInfo = None
image_batches = []
current_batch_idx = 0
review_images_cnt = 0
on_refresh = False
on_complete = False
populate_gallery_func = None
job_project_meta = None
settings: Settings = None
progress = None
finish_cb = None
labeling_jobs_list = None
jobs_names = None
accepted_statuses_for_review = ["done", "none"]  # ? remove none
exclude_job_statuses = ["pending", "completed"]
image_gallery: ReviewGallery = None
change_settings_button: sly.app.widgets.Button = None
# ----------------------------------------------- - ---------------------------------------------- #
