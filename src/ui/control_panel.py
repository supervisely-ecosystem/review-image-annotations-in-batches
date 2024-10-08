import time
from collections import defaultdict
from typing import Dict, List

import supervisely as sly
from supervisely.app.widgets import (
    Button,
    Card,
    ClassesListSelector,
    Container,
    DatasetThumbnail,
    Field,
    InputNumber,
    RadioGroup,
    Select,
    Switch,
    TagsListSelector,
    Text,
)

import src.globals as g
import src.ui.workbench as workbench
import src.utils as u


@u.handle_exception_dialog
def load_labeling_jobs():
    g.jobs_names = None
    g.labeling_jobs_list = None
    filtered_projects = []
    workspace_project_ids = defaultdict(list)
    g.labeling_jobs_list = g.api.labeling_job.get_list(
        team_id=sly.env.team_id(),
        reviewer_id=sly.env.user_id(),
        is_part_of_queue=False,
        exclude_statuses=g.exclude_job_statuses,
    )
    # -------------------------- Filter Jobs With Projects Of "images" Type ------------------------- #
    for job in g.labeling_jobs_list:
        workspace_project_ids[job.workspace_id].append(job.project_id)
    for workspace_id, project_ids in workspace_project_ids.items():
        project_infos = g.api.project.get_list(
            workspace_id=workspace_id,
            filters=[{"field": "id", "operator": "in", "value": project_ids}],
        )
        for info in project_infos:
            if info.type == "images":
                filtered_projects.append(info.id)
    filtered_jobs = [
        job_info for job_info in g.labeling_jobs_list if job_info.project_id in filtered_projects
    ]
    # ---------------------------------------- Update Globals ---------------------------------------- #
    g.labeling_jobs_list = filtered_jobs
    g.jobs_names = [Select.Item(None, "Select Labeling Job")]
    g.jobs_names.extend(
        [Select.Item(labeling_job.id, labeling_job.name) for labeling_job in g.labeling_jobs_list]
    )
    sly.logger.debug(f"Loaded {len(g.labeling_jobs_list)} Labeling Jobs.")


load_labeling_jobs()


# ------------------------------------- Update Labeling Jobs ------------------------------------- #
sly.logger.debug("App was loaded from ecosystem.")
job_selector = Select(g.jobs_names, placeholder="Select Labeling Job")
job_selector.set_value(None)

# ------------------------------------ GUI Labeling Jobs Card ------------------------------------ #
dataset_thumbnail = DatasetThumbnail()
job_dataset_card = Card(content=dataset_thumbnail, title="Related Dataset")
job_dataset_card.hide()

start_review_button = Button("Start Review")
g.change_settings_button = Button("Change Settings", icon="zmdi zmdi-lock-open")
g.change_settings_button.hide()

no_job_message = Text(
    "Please, select a Labeling Job before clicking the button.",
    status="warning",
)
no_job_message.hide()
# -------------------------------------- GUI Job Info Card -------------------------------------- #
job_info_widgets = [
    Text("ID:"),
    Text("Created by: "),
    Text("Assigned to: "),
    Text("Reviewer: "),
    Text("Status: "),
    Text("Classes to label: "),
    Text("Tags to label: "),
    Text("Description: "),
]

job_info_card = Card("Info", content=Container(widgets=job_info_widgets))
job_info_card.hide()

# ----------------------------------- Image Filtering Settings ----------------------------------- #
filter_images_switcher = Switch(False, on_text="Yes", off_text="No")
filter_images_text_l1 = Text(
    text="Filtering works simultaneously by tags and classes",
    color="#5a6772",
)
filter_images_text_l2 = Text(
    text=" - If no elements is selected in a category, only images lacking these elements will be displayed",
    color="#5a6772",
)
filter_images_text_l3 = Text(
    text=" - If all elements in a category are selected, images containing at least one of these elements will be displayed",
    color="#5a6772",
)
job_tags_selector = TagsListSelector(multiple=True)
job_tags_field = Field(title="by Tags", content=job_tags_selector)
job_classes_selector = ClassesListSelector(multiple=True)
job_classes_field = Field(title="by Classes", content=job_classes_selector)
tips_container = Container(
    widgets=[filter_images_text_l2, filter_images_text_l3], gap=4, style="margin-left: 20px;"
)
filter_fields_container = Container(
    widgets=[job_tags_field, job_classes_field], direction="horizontal"
)
filter_container = Container(widgets=[tips_container, filter_fields_container])
filter_container.hide()
filter_card = Card(
    "Filter Images",
    content=Container(
        widgets=[
            filter_images_text_l1,
            filter_images_switcher,
            filter_container,
        ]
    ),
)

# ---------------------------------- GUI Labeling Job Selector ---------------------------------- #
refresh_button = Button("", icon="zmdi zmdi-refresh", button_size="small", plain=True, icon_gap=0)
job_selector_container = Container(
    widgets=[job_selector, refresh_button],
    gap=4,
    direction="horizontal",
    overflow="wrap",
    fractions=[["0 1 auto"], ["0 1 auto"]],
)

# -------------------------------------- GUI Job Info Card -------------------------------------- #


job_info_container = Container(widgets=[job_dataset_card, job_info_card], gap=0)

data_container = Container(widgets=[job_selector_container, job_info_container])
data_card = Card("Labeling Job", content=data_container)

# -------------------------------------- Batch Size Settings ------------------------------------- #
batch_size_input = InputNumber(40, min=4, max=100)
batch_size_text = Text(
    text="Set the number of images to be displayed in the batch", color="#5a6772"
)
batch_size_card = Card("Batch size", content=Container(widgets=[batch_size_text, batch_size_input]))

# --------------------------------------- Group By Settings -------------------------------------- #
group_by_radio_group_items = [
    RadioGroup.Item(value="tag", label="Tags"),
    RadioGroup.Item(value="class", label="Classes"),
]
group_by_radio_group = RadioGroup(items=group_by_radio_group_items, size="large")
group_by_text = Text(
    text="Images will be grouped by a specified criterion. If an image has multiple tags or classes, it will be placed in the group corresponding to the tag or class that was processed first in the grouping logic",
    color="#5a6772",
)
group_by_card = Card(
    content=Container(
        widgets=[
            group_by_text,
            group_by_radio_group,
        ]
    ),
    title="Group by",
)

# ------------------------------------- Tags Editing Settings ------------------------------------ #
tags_editing_switcher = Switch(False, on_text="Yes", off_text="No")
tags_editing_text = Text(
    text='Editing tags allows you to change the values of tags. Changes will only be applied to the tag of the image if its review status is set to "Accepted"',
    color="#5a6772",
)
tags_editing_card = Card(
    "Edit Tags",
    content=Container(
        widgets=[
            tags_editing_text,
            tags_editing_switcher,
        ]
    ),
)

# -------------------------------------- Acceptance Settings ------------------------------------- #
acceptance_radio_group_items = [
    RadioGroup.Item(value="accepted", label="Accept"),
    RadioGroup.Item(value="ignore", label="Skip"),
    RadioGroup.Item(value="rejected", label="Reject"),
]
acceptance_radio_group = RadioGroup(items=acceptance_radio_group_items, size="large")
acceptance_text = Text(
    text="Set the default decision, which will be automatically selected for each image in the batch before the review starts",
    color="#5a6772",
)
acceptance_radio_group_card = Card(
    content=Container(
        widgets=[
            acceptance_text,
            acceptance_radio_group,
        ]
    ),
    title="Default decision",
)

# --------------------------------------- Settings Elements -------------------------------------- #
settings_1st_line_container = Container(
    widgets=[batch_size_card, group_by_card],
    direction="horizontal",
    style="flex: 3 2 0%;/* display: flex; */",
    fractions=[3, 2],
)
settings_2nd_line_container = Container(
    widgets=[filter_card, tags_editing_card],
    direction="horizontal",
    style="flex: 3 2 0%;/* display: flex; */",
    fractions=[3, 2],
)
settings_3d_line_container = Container(
    widgets=[acceptance_radio_group_card],
    direction="horizontal",
)
settings_container = Container(
    widgets=[settings_1st_line_container, settings_2nd_line_container, settings_3d_line_container]
)
settings_card = Card("Review Settings", content=settings_container)

# ---------------------------------------- GUI Control Panel ------------------------------------- #
input_container = Container(
    widgets=[
        data_card,
        settings_card,
    ],
    fractions=[2, 3],
    style="flex: 2 3 0%;/* display: flex; */",
    direction="horizontal",
    gap=10,
)

# Input card with all widgets.
card = Card(
    "⚙️ Control Panel",
    description="Select Labeling Job to be reviewed and how to display its data on the Workbench",
    content=Container(
        widgets=[
            input_container,
            Container(widgets=[no_job_message], style="align-items: flex-end;"),
            Container(widgets=[start_review_button], style="align-items: flex-end;"),
        ],
    ),
    content_top_right=g.change_settings_button,
    collapsable=True,
    overflow="unset",
)


# ------------------------------------------- Functions ------------------------------------------ #


@u.handle_exception_dialog
def disable_settings(disable):
    if disable:
        batch_size_input.disable()
        group_by_radio_group.disable()
        job_tags_field.disable()
        job_classes_field.disable()
        filter_images_switcher.disable()
        tags_editing_switcher.disable()
        job_tags_selector.disable()
        job_classes_selector.disable()
        acceptance_radio_group.disable()
    else:
        batch_size_input.enable()
        group_by_radio_group.enable()
        job_tags_field.enable()
        job_classes_field.enable()
        filter_images_switcher.enable()
        tags_editing_switcher.enable()
        job_tags_selector.enable()
        job_classes_selector.enable()
        acceptance_radio_group.enable()


@u.handle_exception_dialog
def create_image_batches(img_infos: List[sly.ImageInfo], batch_size: int = 40):
    batches = list(sly.batched(img_infos, batch_size=batch_size))
    return batches


@u.handle_exception_dialog
def populate_gallery(gallery_widget: workbench.ReviewGallery):
    start = time.time()
    gallery_widget.clean_up()
    batch = g.image_batches[g.current_batch_idx]
    anns = g.api.labeling_job.get_annotations(g.job_info.id, image_infos=batch)
    sly.logger.debug(f"TIME to get annotations: {time.time() - start}")
    start = time.time()
    for image, ann in zip(batch, anns):
        gallery_widget.append(image, ann, project_meta=g.job_project_meta)
    sly.logger.debug(f"TIME to populate gallery: {time.time() - start}")


@u.handle_exception_dialog
def show_dialog_no_images():
    text = "No images were found for review"
    sly.app.show_dialog("Warning", text, "warning")
    sly.logger.warning(text)
    unlock_control_tab()


@u.handle_exception_dialog
def get_settings():
    settings = g.Settings(
        batch_size=batch_size_input.value,
        group_by=group_by_radio_group.get_value(),
        tags=job_tags_selector.get_selected_tags(),
        classes=job_classes_selector.get_selected_classes(),
        filter_images=filter_images_switcher.is_on(),
        tags_editing=tags_editing_switcher.is_on(),
        default_decision=acceptance_radio_group.get_value(),
    )
    sly.logger.debug(f"Settings: {settings}")
    return settings


@u.handle_exception_dialog
def filter_images_by_tags(images: List[sly.ImageInfo], tags: List[str]):

    filtered_images = []
    tag_ids = [tag.sly_id for tag in tags]
    for img in images:
        if len(img.tags) == 0 and len(tags) == 0:
            filtered_images.append(img)
            continue
        img_tag_ids = [tag["tagId"] for tag in img.tags]
        if any(tag_id in tag_ids for tag_id in img_tag_ids):
            filtered_images.append(img)
    return filtered_images


@u.handle_exception_dialog
def filter_image_by_class(
    img_infos: List[sly.ImageInfo],
    figures_dict: Dict[int, List[sly.FigureInfo]],
    settings: g.Settings,
):
    if not img_infos:
        return [], []

    filtered_figures = {}
    filtered_img_ids = []
    img_ids = [info.id for info in img_infos]
    class_ids = [cls.sly_id for cls in settings.classes]
    for id in img_ids:
        figures = figures_dict.get(id, [])
        if len(settings.classes) == 0 and len(figures) == 0:
            filtered_figures[id] = figures
            filtered_img_ids.append(id)
            continue
        elif len(settings.classes) > 0 and len(figures) > 0:
            for figure in figures:
                if figure.class_id in class_ids:
                    filtered_figures[id] = figures
                    filtered_img_ids.append(id)
                    break
    filtered_img_ids = set(filtered_img_ids)
    filtered_imgs = [info for info in img_infos if info.id in filtered_img_ids]
    return filtered_imgs, filtered_figures


@u.handle_exception_dialog
def group_images(
    images: List[sly.ImageInfo],
    figures: Dict[int, List[sly.FigureInfo]],
    group_by: str,
):
    grouped_images: List[sly.ImageInfo] = []
    len_images = len(images)
    if group_by == "class":
        cond_func = lambda img, fig, cls: any(f.class_id == cls.sly_id for f in fig)
        items = g.job_project_meta.obj_classes
    elif group_by == "tag":
        cond_func = lambda img, fig, tag: tag.sly_id in [tag["tagId"] for tag in img.tags]
        items = g.job_project_meta.tag_metas
    else:
        raise NotImplementedError(f"Invalid group_by value: {group_by}")

    for item in items:
        for idx in range(len(images) - 1, -1, -1):
            img = images[idx]
            fig = figures.get(img.id, [])
            if cond_func(img, fig, item):
                grouped_images.append(img)
                images.pop(idx)

    grouped_images.extend(images)

    if len_images != len(grouped_images):
        text = "Some images were not grouped."
        sly.app.show_dialog("Warning", text, "warning")
        sly.logger.warning(text)
    return grouped_images


disable_settings(True)
g.populate_gallery_func = populate_gallery


# ---------------------------------------- Event Handlers --------------------------------------- #


@job_selector.value_changed
@u.handle_exception_dialog
def show_job_info(job_id):
    """Handles the Labeling Job selector value change event.
    Showing the dataset thumbnail and job info when the Labeling Job is selected.
    """
    disable_settings(True)
    if job_id is None or g.on_refresh:
        # If the Labeling Job is not chosen, hiding the dataset thumbnail and Job info.
        job_dataset_card.hide()
        job_info_card.hide()
        sly.logger.debug("Labeling Job selector set to None")
        return

    no_job_message.hide()

    g.selected_job = job_id
    g.job_info = g.api.labeling_job.get_info_by_id(job_id)
    selected_dataset = g.job_info.dataset_id
    selected_project = g.job_info.project_id

    g.job_ds_info = g.api.dataset.get_info_by_id(selected_dataset)
    dataset_thumbnail.set(g.api.project.get_info_by_id(selected_project), g.job_ds_info)

    cleaned_classes = [cls.strip("'") for cls in g.job_info.classes_to_label]
    cleaned_tags = [tag.strip("'") for tag in g.job_info.tags_to_label]

    job_info_widgets[0].text = f"ID: {g.job_info.id}"
    job_info_widgets[1].text = f"Created by: {g.job_info.created_by_login}"
    job_info_widgets[2].text = f"Assigned to: {g.job_info.assigned_to_login}"
    job_info_widgets[3].text = f"Reviewer: {g.job_info.reviewer_login}"
    job_info_widgets[4].text = f"Status: {g.job_info.status}"
    job_info_widgets[5].text = f"Classes to label: {', '.join(cleaned_classes)}"
    job_info_widgets[6].text = f"Tags to label: {', '.join(cleaned_tags)}"
    job_info_widgets[7].text = f"Description: {g.job_info.description}"

    g.job_project_meta = g.api.labeling_job.get_project_meta(g.selected_job)
    job_classes_selector.set(g.job_project_meta.obj_classes)
    job_tags_selector.set(g.job_project_meta.tag_metas)

    job_dataset_card.show()
    job_info_card.show()
    disable_settings(False)


@g.change_settings_button.click
@u.handle_exception_dialog
def unlock_control_tab():
    card.uncollapse()
    card.unlock()

    job_selector.enable()
    start_review_button.show()
    g.change_settings_button.hide()
    g.image_gallery.clean_states()
    g.image_gallery.clean_up()
    workbench.card.lock()
    workbench.card.collapse()
    if g.progress is not None:
        g.progress.close()
    workbench.finish_button_container.hide()
    workbench.apply_button_container.show()


@start_review_button.click
@u.handle_exception_dialog
def start_review():
    """Handles the load button click event.
    Reading values from the Select Labeling Job widget,
    calling the API to get images from dataset with annotations,
    building the Review Gallery with predefined settings.
    """
    g.change_settings_button.disable()
    g.current_batch_idx = 0
    if g.selected_job is None:
        no_job_message.show()
        return

    job_selector.disable()

    g.change_settings_button.show()

    sly.logger.debug(f"Calling API with Labeling Job ID {g.selected_job} to get dataset ID.")
    g.job_info = g.api.labeling_job.get_info_by_id(g.selected_job)
    g.job_project_meta = g.api.labeling_job.get_project_meta(g.selected_job)
    selected_dataset = g.job_info.dataset_id
    selected_project = g.job_info.project_id

    sly.logger.debug(
        "Recived IDs from the API. "
        f"Selected Project: {selected_project}, "
        f"Selected Dataset: {selected_dataset}"
    )

    g.settings = get_settings()
    g.image_gallery.edit_tags(g.settings.tags_editing)

    images_filters = [
        {
            "type": "job",
            "data": {
                "jobId": g.job_info.id,
                "status": g.accepted_statuses_for_review,
                "showEntitiesInQueuePool": False,
            },
        }
    ]
    if g.settings.filter_images and g.settings.tags:
        images_filters.append(
            {
                "type": "images_tag",
                "data": {
                    "tags": [{"tagId": tag.sly_id} for tag in g.settings.tags],
                    "include": True,
                },
            }
        )
    elif g.settings.filter_images and g.settings.tags == []:
        images_filters.append(
            {
                "type": "images_tag",
                "data": {
                    "tagId": None,
                    "include": False,
                    "value": None,
                },
            }
        )

    # the approximate number of images at which the dashbord will take more time to load
    if g.job_ds_info.images_count >= 10000:
        text = f"Datasets with {g.job_ds_info.images_count} images may take more time to load. Please wait."
        sly.app.show_dialog("Processing...", text, "info")
        sly.logger.info(text)

    start = time.time()
    images = g.api.image.get_filtered_list(
        g.job_info.dataset_id,
        filters=images_filters,
    )
    sly.logger.debug(f"TIME to get images infos: {time.time() - start}")

    if not images:
        show_dialog_no_images()
        return

    start = time.time()
    figures = u.list_light_figures_info(g.job_info.dataset_id)
    sly.logger.debug(f"TIME to get light figures info: {time.time() - start}")

    if g.settings.filter_images:
        start = time.time()
        images, figures = filter_image_by_class(images, figures, g.settings)
        sly.logger.debug(f"TIME to filter annotations by class: {time.time() - start}")
        if not images:
            show_dialog_no_images()
            return

    start = time.time()
    images = group_images(images, figures, g.settings.group_by)
    sly.logger.debug(f"TIME to group images by {g.settings.group_by}: {time.time() - start}")

    # -------------------------------------- Adjust Progress Bar ------------------------------------- #
    g.review_images_cnt = len(images)
    g.progress = workbench.review_progress(message="Reviewing images...", total=g.review_images_cnt)

    g.image_batches = create_image_batches(images, g.settings.batch_size)
    g.image_gallery.set_default_review_state(g.settings.default_decision)

    # create image batch and get annotations only for it
    start = time.time()
    batch = g.image_batches[g.current_batch_idx]
    anns = g.api.labeling_job.get_annotations(g.job_info.id, image_infos=batch)
    sly.logger.debug(f"TIME to get annotations: {time.time() - start}")
    start = time.time()
    for image, ann in zip(batch, anns):
        g.image_gallery.append(image, ann, project_meta=g.job_project_meta)
    sly.logger.debug(f"TIME to populate gallery: {time.time() - start}")

    workbench.card.unlock()
    workbench.card.uncollapse()

    start_review_button.hide()
    card.lock()
    card.collapse()
    g.change_settings_button.enable()


@filter_images_switcher.value_changed
@u.handle_exception_dialog
def show_filters(switched):
    if not switched:
        filter_container.hide()
    else:
        filter_container.show()


@refresh_button.click
@u.handle_exception_dialog
def update_job_selector():
    refresh_button.icon = ""
    g.on_refresh = True
    g.image_gallery.clean_states()
    g.image_gallery.clean_up()
    load_labeling_jobs()
    job_selector.set(items=g.jobs_names)
    job_selector.set_value(None)
    job_dataset_card.hide()
    job_info_card.hide()
    if not g.on_complete:
        g.job_info = None
    g.selected_job = None
    g.on_refresh = False
    refresh_button.icon = "zmdi zmdi-refresh"


@tags_editing_switcher.value_changed
@u.handle_exception_dialog
def set_tags_editing(switched):
    g.image_gallery.edit_tags(switched)


@u.handle_exception_dialog
def finish_job():
    update_job_selector()
    unlock_control_tab()
    g.api.labeling_job.set_status(g.job_info.id, "completed")


g.finish_cb = finish_job
