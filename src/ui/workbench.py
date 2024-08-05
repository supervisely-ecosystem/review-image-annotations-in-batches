import supervisely as sly
from supervisely.app.widgets import Button, Card, Container, Field, Progress, Text

import src.globals as g
from src.ui.review_gallery.widget import ReviewGallery

apply_button = Button("Apply to Batch", "success")
apply_button_field = Field(
    content=apply_button,
    title="",
    description="By clicking this button you will apply selected decisions to its images for the current batch.",
)

finish_button = Button("Finish", "primary")
finish_button_field = Field(
    content=finish_button,
    title="",
    description="By clicking this button you will finish review process.",
)

description_text = Text(
    "Displaying pictures in the gallery depends on grouping and filtering settings, allowing you to customize your viewing experience. \n"
    "Tag editing is possible if activated before starting the process. ",
    "info",
)
image_gallery = ReviewGallery(
    columns_number=4,
    empty_message="",
)
review_progress = Progress()
button_container = Container(
    widgets=[apply_button_field, finish_button_field],
    direction="horizontal",
)
gallery_container = Container(
    widgets=[description_text, review_progress, image_gallery, button_container]
)
card = Card(
    title="🔬 Workbench",
    description="A comprehensive interface for reviewing a collection of images with their annotations.",
    content=gallery_container,
    lock_message="Select the Labbeling Task and andjust Settings to start Review.",
    collapsable=True,
)
card.lock()
card.collapse()


@apply_button.click
def apply_decision():
    review_states = image_gallery.get_review_state()
    for image in g.image_batches[g.current_batch_idx]:
        review_state = review_states[str(image[0].id)]
        if review_state == "ignore":
            continue
        g.api.labeling_job.set_entity_review_status(
            g.task_info.id,
            image[0].id,
            review_state,
        )
    g.progress.update(len(g.image_batches[g.current_batch_idx]))
    if g.current_batch_idx < len(g.image_batches) - 1:
        g.current_batch_idx += 1
        g.populate_gallery_func(image_gallery)
    else:
        sly.app.show_dialog(
            "Review process is finished",
            f"{'All' if g.progress.n == g.progress.total else g.progress.n} images have been reviewed",
        )
        g.finish_cb()
        g.progress.close()


@finish_button.click
def finish_review():
    g.finish_cb()
