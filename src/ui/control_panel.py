import os
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
    Progress,
    RadioGroup,
    Select,
    Switch,
    TagsListSelector,
    Text,
)

import src.globals as g
import src.ui.workbench as workbench

dataset_thumbnail = DatasetThumbnail()
task_dataset_card = Card(content=dataset_thumbnail, title="Related Dataset")
task_dataset_card.hide()

start_review_button = Button("Start Review")
change_settings_button = Button("Change Settings", icon="zmdi zmdi-lock-open")
change_settings_button.hide()

no_task_message = Text(
    "Please, select a Labeling Task before clicking the button.",
    status="warning",
)
no_task_message.hide()

if g.selected_task:
    # If the app was loaded from a context menu.
    sly.logger.debug("App was loaded from a context menu.")

    # Setting values to the widgets from environment variables.
    task_selector = Select(items=g.tasks_names)
    task_selector.set_value(g.selected_task)

    # Hiding unnecessary widgets.
    task_selector.hide()
    start_review_button.hide()

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
task_info_container = Container(widgets=task_info_widgets)
task_info_card = Card("Task Info", content=task_info_container)
task_info_card.hide()

task_info_container = Container(
    widgets=[
        task_dataset_card,
        task_info_card,
    ]
)

data_container = Container(
    widgets=[
        task_selector,
        task_info_container,
    ],
    style="flex: 1 2 0%;/* display: flex; */",
    fractions=[1, 2],
    direction="horizontal",
    gap=10,
)
data_card = Card("Labeling Task", content=data_container)

# -------------------------------------- Batch Size Settings ------------------------------------- #
batch_size_input = InputNumber(5, min=5, max=100)
batch_size_card = Card("Batch Size", content=batch_size_input)
# --------------------------------------- Group By Settings -------------------------------------- #
group_by_radio_group_items = [
    RadioGroup.Item(value="tag", label="Tags"),
    RadioGroup.Item(value="class", label="Classes"),
]
group_by_radio_group = RadioGroup(items=group_by_radio_group_items, size="large")
group_by_card = Card(content=group_by_radio_group, title="Group By")
# ----------------------------------- Image Filtering Settings ----------------------------------- #
all_images_switcher = Switch(True, on_text="Yes", off_text="No")
task_tags_selector = TagsListSelector()
task_tags_field = Field(title="with Tags", content=task_tags_selector)
task_classes_selector = ClassesListSelector()
task_classes_field = Field(title="with Classes", content=task_classes_selector)
filter_container = Container(widgets=[task_tags_field, task_classes_field], direction="horizontal")
filter_container.hide()
filter_card = Card("All Images", content=Container(widgets=[all_images_switcher, filter_container]))
# ------------------------------------- Tags Editing Settings ------------------------------------ #
tags_editing_switcher = Switch(False, on_text="Yes", off_text="No")
tags_editing_card = Card("Edit Tags", content=tags_editing_switcher)
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
settings_container = Container(widgets=[settings_1st_line_container, settings_2nd_line_container])
settings_card = Card("Review Settings", content=settings_container)


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
    else:
        batch_size_input.enable()
        group_by_radio_group.enable()
        task_tags_field.enable()
        task_classes_field.enable()
        all_images_switcher.enable()
        tags_editing_switcher.enable()
        task_tags_selector.enable()
        task_classes_selector.enable()


disable_settings(True)
# ----------------------------------------------- - ---------------------------------------------- #

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


g.populate_gallery_func = populate_gallery


def get_settings():
    settings = g.Settings(
        batch_size=batch_size_input.value,
        group_by=group_by_radio_group.get_value(),
        tags=task_tags_selector.get_selected_tags(),
        classes=task_classes_selector.get_selected_classes(),
        all_images=all_images_switcher.is_on(),
        tags_editing=tags_editing_switcher.is_on(),
    )
    sly.logger.debug(f"Settings: {settings}")
    return settings


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


def group_images_by(
    images: List[sly.ImageInfo],
    annotations: List[sly.Annotation],
    group_by: str,
):
    grouped_images: Dict[str, List[sly.ImageInfo]] = {}
    grouped_anns: Dict[str, List[sly.Annotation]] = {}

    for img, ann in zip(images, annotations):
        tags = [label.tags[0].items() for label in ann.labels if label.tags != []]
        for tag in tags:
            if tag not in grouped_images:
                grouped_images[tag] = []
            grouped_images[tag].append(img)


def show_dialog_no_images():
    text = "No images found with the specified filters."
    sly.app.show_dialog("Warning", text, "warning")
    sly.logger.warn(text)
    # TODO click change_settings_button


@task_selector.value_changed
def show_dataset_thumbnail(labeling_task_id):
    """Handles the Labeling Task selector value change event.
    Showing the dataset thumbnail when the Labeling Task is selected.
    """

    if not labeling_task_id:
        # If the Labeling Task is not chosen, hiding the dataset thumbnail.
        task_dataset_card.hide()
        return

    no_task_message.hide()

    # Changing the values of the global variables to access them from other modules.
    g.selected_task = labeling_task_id

    # Showing the dataset thumbnail when the Labeling Task is selected.
    g.task_info = g.api.labeling_job.get_info_by_id(labeling_task_id)
    selected_dataset = g.task_info.dataset_id
    selected_project = g.task_info.project_id

    dataset_thumbnail.set(
        g.api.project.get_info_by_id(selected_project),
        g.api.dataset.get_info_by_id(selected_dataset),
    )
    task_dataset_card.show()
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

    task_info_card.show()

    g.task_project_meta = g.api.labeling_job.get_project_meta(g.selected_task)
    task_classes_selector.set(g.task_project_meta.obj_classes)
    task_tags_selector.set(g.task_project_meta.tag_metas)
    disable_settings(False)


@start_review_button.click
def load_images_with_annotations():
    """Handles the load button click event.
    Reading values from the Select Labeling Task widget,
    calling the API to get images from dataset with annotations,
    building the table with settings.
    """

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
    g.task_meta = g.api.labeling_job.get_project_meta(g.selected_task)
    selected_dataset = g.task_info.dataset_id
    selected_project = g.task_info.project_id
    g.images_list = g.task_info.entities

    sly.logger.debug(
        "Recived IDs from the API. "
        f"Selected Project: {selected_project}, "
        f"Selected Dataset: {selected_dataset}"
    )

    g.settings = get_settings()

    img_ids = [entity["id"] for entity in g.task_info.entities if entity["reviewStatus"] == "none"]

    images = g.api.image.get_list(
        g.task_info.dataset_id,
        filters=[{"field": "id", "operator": "in", "value": img_ids}],
    )

    if not g.settings.all_images:
        images = filter_images_by_tags(images, g.settings.tags)
        img_ids = [img.id for img in images]

    if img_ids == []:
        show_dialog_no_images()
        return

    g.review_images_cnt = len(img_ids)

    g.progress = workbench.review_progress(message="Reviewing items...", total=g.review_images_cnt)

    anns = g.api.labeling_job.get_annotations(g.task_info.id, img_ids)

    if not g.settings.all_images:
        images, anns = filter_image_anns(images, anns, g.settings)
        if images == []:
            show_dialog_no_images()
            return
    # images, anns = group_images_by(images, anns, g.settings.group_by)

    g.image_batches = create_image_batches(images, anns, g.settings.batch_size)
    for image in g.image_batches[g.current_batch_idx]:
        workbench.image_gallery.append(image[0], image[1], project_meta=g.task_project_meta)

    workbench.card.unlock()
    workbench.card.uncollapse()

    card.lock()
    card.collapse()


@change_settings_button.click
def handle_input():
    card.uncollapse()
    card.unlock()
    task_selector.enable()
    start_review_button.show()
    change_settings_button.hide()
    workbench.image_gallery.clean_up()
    workbench.card.lock()
    workbench.card.collapse()


@all_images_switcher.value_changed
def show_filters(switched):
    if switched:
        filter_container.hide()
    else:
        filter_container.show()