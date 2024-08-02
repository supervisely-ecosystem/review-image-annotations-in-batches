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

# STATIC_DIR = os.path.join(SLY_APP_DATA_DIR, "static")

selected_task = os.environ.get("modal.state.slyJobId", None)

# ? do we need to restrict lebaling tasks to only the ones that are assigned to the current user?
labeling_tasks_list = api.labeling_job.get_list(
    team_id=sly.env.team_id(), reviewer_id=sly.env.user_id()
)
tasks_names = [
    Select.Item(labeling_task.id, labeling_task.name) for labeling_task in labeling_tasks_list
]

images_list = []
task_info: LabelingJobInfo = None
image_batches = []
current_batch_idx = 0
populate_gallery_func = None
review_images_cnt = 0
task_project_meta = None


@dataclass
class Settings:
    batch_size: int
    group_by: str
    tags: list
    classes: list
    all_images: bool
    tags_editing: bool


settings = None
