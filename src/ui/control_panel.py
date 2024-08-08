from collections import defaultdict
from typing import List

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


@sly.timeit
def load_labeling_tasks():
    filtered_projects = []
    workspace_project_ids = defaultdict(list)
    g.labeling_tasks_list = g.api.labeling_job.get_list(
        team_id=sly.env.team_id(), reviewer_id=sly.env.user_id(), is_part_of_queue=False
    )
    # -------------------------- Filter Tasks With Projects Of "images" Type ------------------------- #
    for task in g.labeling_tasks_list:
        workspace_project_ids[task.workspace_id].append(task.project_id)
    for workspace_id, project_ids in workspace_project_ids.items():
        project_infos = g.api.project.get_list(
            workspace_id=workspace_id,
            filters=[{"field": "id", "operator": "in", "value": project_ids}],
        )
        for info in project_infos:
            if info.type == "images":
                filtered_projects.append(info.id)
    filtered_tasks = [
        task_info
        for task_info in g.labeling_tasks_list
        if task_info.project_id in filtered_projects
    ]
    # ---------------------------------------- Update Globals ---------------------------------------- #
    g.labeling_tasks_list = filtered_tasks
    g.tasks_names = [
        Select.Item(labeling_task.id, labeling_task.name) for labeling_task in g.labeling_tasks_list
    ]
    sly.logger.debug(f"Loaded {len(g.labeling_tasks_list)} Labeling Tasks.")


load_labeling_tasks()

# ------------------------------------ GUI Labeling Task Card ------------------------------------ #
dataset_thumbnail = DatasetThumbnail()
task_dataset_card = Card(content=dataset_thumbnail, title="Related Dataset")
task_dataset_card.hide()

start_review_button = Button("Start Review")
# start_review_button.disable()
change_settings_button = Button("Change Settings", icon="zmdi zmdi-lock-open")
change_settings_button.hide()

no_task_message = Text(
    "Please, select a Labeling Task before clicking the button.",
    status="warning",
)
no_task_message.hide()

# ------------------------------------- Update Labeling Task ------------------------------------- #
if g.selected_task:
    # If the app was loaded from a context menu.
    sly.logger.debug("App was loaded from a context menu.")

    # Setting values to the widgets from environment variables.
    task_selector = Select(items=g.tasks_names)
    task_selector.set_value(g.selected_task)

    # Hiding unnecessary widgets.
    # task_selector.hide()
    # start_review_button.hide()  # TODO set logic

    # Creating a dataset thumbnail to show.
    g.task_info = g.api.labeling_job.get_info_by_id(g.selected_task)

    dataset_thumbnail.set(
        g.api.project.get_info_by_id(g.task_info.project_id),
        g.api.dataset.get_info_by_id(g.task_info.dataset_id),
    )
    task_dataset_card.show()

    workbench.card.unlock()
    workbench.card.uncollapse()
else:
    # If the app was loaded from ecosystem: showing the Labeling Task selector in full mode.
    sly.logger.debug("App was loaded from ecosystem.")
    task_selector = Select(g.tasks_names, placeholder="Select Labeling Task")
    task_selector.set_value(None)

# ---------------------------------- GUI Labeling Task Selector ---------------------------------- #
refresh_button = Button("", icon="zmdi zmdi-refresh", button_size="small", plain=True)
task_selector_container = Container(
    widgets=[task_selector, refresh_button],
    gap=4,
    direction="horizontal",
    overflow="wrap",
    fractions=[["0 1 auto"], ["0 1 auto"]],
)

# -------------------------------------- GUI Task Info Card -------------------------------------- #
# TODO add more info to the card
task_info_widgets = [
    Text("ID:"),
    Text("Created by: "),
    Text("Assigned to: "),
    Text("Reviewer: "),
    Text("Status: "),
    Text("Finished images: "),
    Text("Classes to label: "),
    Text("Tags to label: "),
    Text("Description: "),
]

task_info_card = Card("Task info", content=Container(widgets=task_info_widgets))
task_info_card.hide()

task_info_container = Container(widgets=[task_dataset_card, task_info_card], gap=0)

data_container = Container(widgets=[task_selector_container, task_info_container])
data_card = Card("Labeling Task", content=data_container)

# -------------------------------------- Batch Size Settings ------------------------------------- #
batch_size_input = InputNumber(4, min=4, max=100)
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

# ----------------------------------- Image Filtering Settings ----------------------------------- #
all_images_switcher = Switch(False, on_text="Yes", off_text="No")
all_images_text_l1 = Text(
    text="Filtering works simultaneously by tags and classes",
    color="#5a6772",
)
all_images_text_l2 = Text(
    text="TIP: If no checkbox is selected in a category, all images lacking these elements will be filtered out",
    color="#5a6772",
)
task_tags_selector = TagsListSelector(multiple=True)
task_tags_field = Field(title="by Tags", content=task_tags_selector)
task_classes_selector = ClassesListSelector(multiple=True)
task_classes_field = Field(title="by Classes", content=task_classes_selector)
filter_container = Container(widgets=[task_tags_field, task_classes_field], direction="horizontal")
filter_container.hide()
filter_card = Card(
    "Filter Images",
    content=Container(
        widgets=[all_images_text_l1, all_images_text_l2, all_images_switcher, filter_container]
    ),
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
    RadioGroup.Item(value="ignore", label="Ignore"),
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
    description="Select the task to be reviewed and how to display its data on the Workbench",
    content=Container(
        widgets=[
            input_container,
            no_task_message,
            start_review_button,
        ]
    ),
    content_top_right=change_settings_button,
    collapsable=True,
)


# ------------------------------------------- Functions ------------------------------------------ #
def disable_settings(disable):
    if disable:
        batch_size_input.disable()
        group_by_radio_group.disable()
        task_tags_field.disable()
        task_classes_field.disable()
        all_images_switcher.disable()
        tags_editing_switcher.disable()
        task_tags_selector.disable()
        task_classes_selector.disable()
        acceptance_radio_group.disable()
    else:
        batch_size_input.enable()
        group_by_radio_group.enable()
        task_tags_field.enable()
        task_classes_field.enable()
        all_images_switcher.enable()
        tags_editing_switcher.enable()
        task_tags_selector.enable()
        task_classes_selector.enable()
        acceptance_radio_group.enable()


def create_image_batches(
    img_infos: List[sly.ImageInfo],
    anns: List[sly.Annotation],
    batch_size: int,
):
    paired_list = list(zip(img_infos, anns))
    batches = [paired_list[i : i + batch_size] for i in range(0, len(paired_list), batch_size)]
    return batches


def populate_gallery(gallery_widget: workbench.ReviewGallery):
    gallery_widget.clean_up()
    for image in g.image_batches[g.current_batch_idx]:
        gallery_widget.append(image[0], image[1], project_meta=g.task_project_meta)


def show_dialog_no_images():
    text = "No images found with the specified filters."
    sly.app.show_dialog("Warning", text, "warning")
    sly.logger.warn(text)
    unlock_control_tab()


def get_settings():
    settings = g.Settings(
        batch_size=batch_size_input.value,
        group_by=group_by_radio_group.get_value(),
        tags=task_tags_selector.get_selected_tags(),
        classes=task_classes_selector.get_selected_classes(),
        all_images=all_images_switcher.is_on(),
        tags_editing=tags_editing_switcher.is_on(),
        default_decision=acceptance_radio_group.get_value(),
    )
    sly.logger.debug(f"Settings: {settings}")
    return settings


@sly.timeit
def filter_images_by_tags(images: List[sly.ImageInfo], tags: List[str]):
    if tags == []:
        return images
    filtered_images = []
    tag_ids = [tag.sly_id for tag in tags]
    for img in images:
        img_tag_ids = [tag["tagId"] for tag in img.tags]
        if any(tag_id in tag_ids for tag_id in img_tag_ids):
            filtered_images.append(img)
    return filtered_images


@sly.timeit
def filter_image_anns(
    img_infos: List[sly.ImageInfo],
    annotations: List[sly.Annotation],
    settings: g.Settings,
):
    if img_infos == []:
        return [], []
    filtered_anns = []
    img_idx = []
    for idx, ann in enumerate(annotations):
        for label in ann.labels:
            if label.obj_class in settings.classes:
                filtered_anns.append(ann)
                img_idx.append(idx)
                break
            # if any(tag in settings.tags for tag in label.tags):
            #     filtered_anns.append(ann)
            #     img_idx.append(idx)
            #     break
    filtered_imgs = [img_infos[idx] for idx in img_idx]
    return filtered_imgs, filtered_anns


@sly.timeit
def group_images_by(
    images: List[sly.ImageInfo],
    annotations: List[sly.Annotation],
    group_by: str,
):
    grouped_images: List[sly.ImageInfo] = []
    grouped_anns: List[sly.Annotation] = []
    len_images = len(images)
    len_anns = len(annotations)
    if group_by == "class":
        cond_func = lambda img, ann, cls: cls in [label.obj_class for label in ann.labels]
        items = g.task_project_meta.obj_classes
    elif group_by == "tag":
        cond_func = lambda img, ann, tag: tag.sly_id in [tag["tagId"] for tag in img.tags]
        items = g.task_project_meta.tag_metas
    else:
        raise NotImplementedError(f"Invalid group_by value: {group_by}")

    for item in items:
        for idx in range(len(images) - 1, -1, -1):
            img, ann = images[idx], annotations[idx]
            if cond_func(img, ann, item):
                grouped_images.append(img)
                grouped_anns.append(ann)
                images.pop(idx)
                annotations.pop(idx)

    grouped_images.extend(images)
    grouped_anns.extend(annotations)

    if len_images != len(grouped_images) or len_anns != len(grouped_anns):
        text = "Some images or annotations were not grouped."
        sly.app.show_dialog("Warning", text, "warning")
        sly.logger.warn(text)
    return grouped_images, grouped_anns


disable_settings(True)
g.populate_gallery_func = populate_gallery


# ---------------------------------------- Event Handlers --------------------------------------- #
@task_selector.value_changed
def show_task_info(task_id):
    """Handles the Labeling Task selector value change event.
    Showing the dataset thumbnail when the Labeling Task is selected.
    """

    if not task_id or g.on_refresh:
        # If the Labeling Task is not chosen, hiding the dataset thumbnail.
        task_dataset_card.hide()
        task_info_card.hide()
        return

    no_task_message.hide()

    # Changing the values of the global variables to access them from other modules.
    g.selected_task = task_id

    # Showing the dataset thumbnail when the Labeling Task is selected.
    g.task_info = g.api.labeling_job.get_info_by_id(task_id)
    selected_dataset = g.task_info.dataset_id
    selected_project = g.task_info.project_id

    dataset_thumbnail.set(
        g.api.project.get_info_by_id(selected_project),
        g.api.dataset.get_info_by_id(selected_dataset),
    )

    cleaned_classes = [cls.strip("'") for cls in g.task_info.classes_to_label]
    cleaned_tags = [tag.strip("'") for tag in g.task_info.tags_to_label]

    task_info_widgets[0].text = f"ID: {g.task_info.id}"
    task_info_widgets[1].text = f"Created by: {g.task_info.created_by_login}"
    task_info_widgets[2].text = f"Assigned to: {g.task_info.assigned_to_login}"
    task_info_widgets[3].text = f"Reviewer: {g.task_info.reviewer_login}"
    task_info_widgets[4].text = f"Status: {g.task_info.status}"
    task_info_widgets[5].text = f"Finished images: {g.task_info.finished_images_count}"
    task_info_widgets[6].text = f"Classes to label: {', '.join(cleaned_classes)}"
    task_info_widgets[7].text = f"Tags to label: {', '.join(cleaned_tags)}"
    task_info_widgets[8].text = f"Description: {g.task_info.description}"

    g.task_project_meta = g.api.labeling_job.get_project_meta(g.selected_task)
    task_classes_selector.set(g.task_project_meta.obj_classes)
    task_tags_selector.set(g.task_project_meta.tag_metas)

    task_dataset_card.show()
    task_info_card.show()
    disable_settings(False)
    start_review_button.enable()


@change_settings_button.click
def unlock_control_tab():
    card.uncollapse()
    card.unlock()

    task_selector.enable()
    start_review_button.show()
    change_settings_button.hide()
    workbench.image_gallery.clean_up()
    workbench.card.lock()
    workbench.card.collapse()


@start_review_button.click
def load_images_with_annotations():
    """Handles the load button click event.
    Reading values from the Select Labeling Task widget,
    calling the API to get images from dataset with annotations,
    building the table with settings.
    """
    g.current_batch_idx = 0
    if g.selected_task is None:
        no_task_message.show()
        return

    # Disabling the Labeling Task selector and the load button.
    task_selector.disable()
    start_review_button.hide()

    # Showing the button for unlocking the dataset selector and showing start button.
    change_settings_button.show()

    sly.logger.debug(f"Calling API with Labeling Task ID {g.selected_task} to get dataset ID.")
    g.task_info = g.api.labeling_job.get_info_by_id(g.selected_task)
    g.task_project_meta = g.api.labeling_job.get_project_meta(g.selected_task)
    selected_dataset = g.task_info.dataset_id
    selected_project = g.task_info.project_id
    g.images_list = g.task_info.entities

    sly.logger.debug(
        "Recived IDs from the API. "
        f"Selected Project: {selected_project}, "
        f"Selected Dataset: {selected_dataset}"
    )

    g.settings = get_settings()
    workbench.image_gallery.edit_tags(g.settings.tags_editing)

    img_ids = [entity["id"] for entity in g.task_info.entities if entity["reviewStatus"] == "none"]
    if img_ids == []:
        show_dialog_no_images()
        return

    images = g.api.image.get_list(
        g.task_info.dataset_id,
        filters=[{"field": "id", "operator": "in", "value": img_ids}],
    )

    if g.settings.all_images:
        images = filter_images_by_tags(images, g.settings.tags)
        img_ids = [img.id for img in images]

    if img_ids == []:
        show_dialog_no_images()
        return

    anns = g.api.labeling_job.get_annotations(g.task_info.id, img_ids)

    if g.settings.all_images:
        images, anns = filter_image_anns(images, anns, g.settings)
        if images == []:
            show_dialog_no_images()
            return

    images, anns = group_images_by(images, anns, g.settings.group_by)

    # -------------------------------------- Adjust Progress Bar ------------------------------------- #
    g.review_images_cnt = len(images)
    g.progress = workbench.review_progress(message="Reviewing images...", total=g.review_images_cnt)

    g.image_batches = create_image_batches(images, anns, g.settings.batch_size)
    workbench.image_gallery.set_default_review_state(g.settings.default_decision)
    for image in g.image_batches[g.current_batch_idx]:
        workbench.image_gallery.append(image[0], image[1], project_meta=g.task_project_meta)

    workbench.card.unlock()
    workbench.card.uncollapse()

    card.lock()
    card.collapse()


@all_images_switcher.value_changed
def show_filters(switched):
    if not switched:
        filter_container.hide()
    else:
        filter_container.show()


@refresh_button.click
def update_task_selector():
    g.on_refresh = True
    load_labeling_tasks()
    task_selector.set(items=g.tasks_names)
    task_selector.set_value(None)  # TODO fix case if the task not cleared
    task_dataset_card.hide()
    task_info_card.hide()

    disable_settings(True)
    g.on_refresh = False


@tags_editing_switcher.value_changed
def set_tags_editing(switched):
    workbench.image_gallery.edit_tags(switched)


def finish_task():
    update_task_selector()
    unlock_control_tab()
    disable_settings(True)


g.finish_cb = finish_task
