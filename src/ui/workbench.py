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


@sly.handle_exceptions
@sly.timeit
@apply_button.click
def apply_decision():
    review_states: dict = image_gallery.get_review_states()
    tag_values: dict = image_gallery.get_tag_values()
    tag_change_states: dict = image_gallery.get_tag_change_states()
    for image in g.image_batches[g.current_batch_idx]:
        try:
            review_state = review_states[str(image[0].id)]
        except KeyError:
            title = "Error in getting review status"
            descr = f"Please check review status for image {image[0].name} before applying the decision. For now, it will be skipped."
            sly.app.show_dialog(title, descr, status="error")
            sly.logger.error(
                f"Error in getting review status for image {image[0].name}: {image[0].id}. Will be skipped"
            )
            continue
        if review_state == "ignore":
            continue
        elif review_state == "accepted":
            changed_tag_ids = list(tag_change_states.keys())
            for tag_id in changed_tag_ids:
                if any(d.get("id") == int(tag_id) for d in image[0].tags):
                    respones = g.api.image.update_tag_value(int(tag_id), value=tag_values[tag_id])
                    if respones.get("success", False):
                        sly.logger.info(f"Tag {tag_id} updated successfully")
                    else:
                        sly.logger.error(f"Error in updating tag {tag_id}")
        g.api.labeling_job.set_entity_review_status(
            g.task_info.id,
            image[0].id,
            review_state,
        )

    g.progress.update(len(g.image_batches[g.current_batch_idx]))
    if g.current_batch_idx < len(g.image_batches) - 1:
        g.current_batch_idx += 1
        image_gallery.clean_states()
        g.populate_gallery_func(image_gallery)
    else:
        image_gallery.clean_states()
        sly.app.show_dialog(
            "Review process is finished",
            f"{'All' if g.progress.n == g.progress.total else g.progress.n} images have been reviewed",
        )
        g.finish_cb()
        g.progress.close()


@finish_button.click
def finish_review():
    g.finish_cb()
