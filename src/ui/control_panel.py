import os

import supervisely as sly
from supervisely.app.widgets import (
    Button,
    Card,
    ClassesListSelector,
    Container,
    DatasetThumbnail,
    Field,
    Progress,
    Select,
    TagsListSelector,
    Text,
)

import src.globals as g
import src.ui.workbench as workbench

dataset_thumbnail = DatasetThumbnail()
# dataset_thumbnail.hide()
labeling_task_dataset_card = Card(content=dataset_thumbnail, title="Related Dataset")
labeling_task_dataset_card.hide()

start_review_button = Button("Start Review")
change_labeling_task_button = Button("Change Labeling Task", icon="zmdi zmdi-lock-open")
change_labeling_task_button.hide()

no_labeling_task_message = Text(
    "Please, select a Labeling Task before clicking the button.",
    status="warning",
)
no_labeling_task_message.hide()

if g.selected_labeling_task:
    # If the app was loaded from a context menu.
    sly.logger.debug("App was loaded from a context menu.")

    # Setting values to the widgets from environment variables.
    select_labeling_task = Select(items=g.labeling_task_names)
    select_labeling_task.set_value(g.selected_labeling_task)

    # Hiding unnecessary widgets.
    select_labeling_task.hide()
    start_review_button.hide()

    # Creating a dataset thumbnail to show.
    g.labeling_task_info = g.api.labeling_job.get_info_by_id(g.selected_labeling_task)

    dataset_thumbnail.set(
        g.api.project.get_info_by_id(g.labeling_task_info.project_id),
        g.api.dataset.get_info_by_id(g.labeling_task_info.dataset_id),
    )
    labeling_task_dataset_card.show()

    workbench.card.unlock()
    workbench.card.uncollapse()
else:
    # If the app was loaded from ecosystem: showing the Labeling Task selector in full mode.
    sly.logger.debug("App was loaded from ecosystem.")
    select_labeling_task = Select(g.labeling_task_names, placeholder="Select Labeling Task")
    select_labeling_task.set_value(None)


# TODO add more info to the card
labeling_task_info_widgets = [
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
labeling_task_info_container = Container(widgets=labeling_task_info_widgets)
labeling_task_info_card = Card("Task Info", content=labeling_task_info_container)
labeling_task_info_card.hide()

labeling_task_info_container = Container(
    widgets=[
        labeling_task_dataset_card,
        labeling_task_info_card,
    ]
)

data_container = Container(
    widgets=[
        select_labeling_task,
        labeling_task_info_container,
    ],
    style="flex: 1 2 0%;/* display: flex; */",
    fractions=[1, 2],
    direction="horizontal",
    gap=10,
)
data_card = Card("Labeling Task", content=data_container)

settings_container = Container()
settings_card = Card("Review Settings", content=settings_container)

input_container = Container(
    widgets=[
        data_card,
        settings_card,
    ],
    fractions=[2, 3],
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
            no_labeling_task_message,
            start_review_button,
        ]
    ),
    content_top_right=change_labeling_task_button,
    collapsable=True,
)


def create_image_batches(img_infos, anns, batch_size):
    paired_list = list(zip(img_infos, anns))
    batches = [paired_list[i : i + batch_size] for i in range(0, len(paired_list), batch_size)]
    return batches


def populate_gallery(gallery_widget: workbench.GridGallery):
    gallery_widget.clean_up()
    for image in g.image_batches[g.current_batch_idx]:
        gallery_widget.append(image[0].preview_url, image[1])


g.populate_gallery_func = populate_gallery


@select_labeling_task.value_changed
def show_dataset_thumbnail(labeling_task_id):
    """Handles the Labeling Task selector value change event.
    Showing the dataset thumbnail when the Labeling Task is selected.
    """

    if not labeling_task_id:
        # If the Labeling Task is not chosen, hiding the dataset thumbnail.
        labeling_task_dataset_card.hide()
        return

    no_labeling_task_message.hide()

    # Changing the values of the global variables to access them from other modules.
    g.selected_labeling_task = labeling_task_id

    # Showing the dataset thumbnail when the Labeling Task is selected.
    g.labeling_task_info = g.api.labeling_job.get_info_by_id(labeling_task_id)
    selected_dataset = g.labeling_task_info.dataset_id
    selected_project = g.labeling_task_info.project_id

    dataset_thumbnail.set(
        g.api.project.get_info_by_id(selected_project),
        g.api.dataset.get_info_by_id(selected_dataset),
    )
    labeling_task_dataset_card.show()

    labeling_task_info_widgets[0].text = f"ID: {g.labeling_task_info.id}"
    labeling_task_info_widgets[1].text = f"Created by: {g.labeling_task_info.created_by_login}"
    labeling_task_info_widgets[2].text = f"Assigned to: {g.labeling_task_info.assigned_to_login}"
    labeling_task_info_widgets[3].text = f"Reviewer: {g.labeling_task_info.reviewer_login}"
    labeling_task_info_widgets[4].text = f"Status: {g.labeling_task_info.status}"
    labeling_task_info_widgets[5].text = (
        f"Finished images: {g.labeling_task_info.finished_images_count}"
    )
    cleaned_classes = [cls.strip("'") for cls in g.labeling_task_info.classes_to_label]
    labeling_task_info_widgets[6].text = f"Classes to label: {', '.join(cleaned_classes)}"
    cleaned_tags = [tag.strip("'") for tag in g.labeling_task_info.tags_to_label]
    labeling_task_info_widgets[7].text = f"Tags to label: {', '.join(cleaned_tags)}"
    labeling_task_info_widgets[8].text = f"Description: {g.labeling_task_info.description}"

    labeling_task_info_card.show()


@start_review_button.click
def load_images_with_annotations():
    """Handles the load button click event.
    Reading values from the Select Labeling Task widget,
    calling the API to get images from dataset with annotations,
    building the table with settings.
    """

    if g.selected_labeling_task is None:
        no_labeling_task_message.show()
        return

    # Disabling the Labeling Task selector and the load button.
    select_labeling_task.disable()
    start_review_button.hide()

    # Showing the button for unlocking the dataset selector and showing start button.
    change_labeling_task_button.show()

    sly.logger.debug(
        f"Calling API with Labeling Task ID {g.selected_labeling_task} to get dataset ID."
    )
    g.labeling_task_info = g.api.labeling_job.get_info_by_id(g.selected_labeling_task)
    selected_dataset = g.labeling_task_info.dataset_id
    selected_project = g.labeling_task_info.project_id
    g.images_list = g.labeling_task_info.entities

    sly.logger.debug(
        "Recived IDs from the API. "
        f"Selected Project: {selected_project}, "
        f"Selected Dataset: {selected_dataset}"
    )

    img_ids = [
        entity["id"] for entity in g.labeling_task_info.entities if entity["reviewStatus"] == "none"
    ]
    g.review_images_cnt = len(img_ids)
    workbench.review_progress(total=g.review_images_cnt)
    # TODO add filter for tags or classes
    img_infos = g.api.image.get_list(
        g.labeling_task_info.dataset_id,
        filters=[{"field": "id", "operator": "in", "value": img_ids}],
    )
    anns = g.api.labeling_job.get_annotations(g.labeling_task_info.id, img_ids)

    g.image_batches = create_image_batches(img_infos, anns, 15)
    for image in g.image_batches[g.current_batch_idx]:
        workbench.image_gallery.append(image[0].preview_url, image[1])

    workbench.card.unlock()
    workbench.card.uncollapse()

    card.lock()
    card.collapse()


@change_labeling_task_button.click
def handle_input():
    card.uncollapse()
    card.unlock()
    select_labeling_task.enable()
    start_review_button.show()
    change_labeling_task_button.hide()
    workbench.image_gallery.clean_up()
    workbench.card.lock()
    workbench.card.collapse()
