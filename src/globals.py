import os
from dataclasses import dataclass

import supervisely as sly
from dotenv import load_dotenv
from supervisely.api.labeling_job_api import LabelingJobInfo
from supervisely.app.widgets import Select

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()

SLY_APP_DATA_DIR = sly.app.get_data_dir()

selected_task = os.environ.get("modal.state.slyJobId", None)

# ----------------------------------------- Init Section ----------------------------------------- #
images_list = []
task_info: LabelingJobInfo = None
image_batches = []
current_batch_idx = 0
review_images_cnt = 0
on_refresh = False
populate_gallery_func = None
task_project_meta = None
settings = None
progress = None
finish_cb = None
labeling_tasks_list = None
tasks_names = None
# ----------------------------------------------- - ---------------------------------------------- #


@dataclass
class Settings:
    batch_size: int
    group_by: str
    tags: list
    classes: list
    all_images: bool
    tags_editing: bool
    default_decision: str
