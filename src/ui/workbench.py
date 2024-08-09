import supervisely as sly
from supervisely.app.widgets import Button, Card, Container, Field, Progress, Text

import src.globals as g
from src.ui.review_gallery.widget import ReviewGallery

apply_button = Button("Apply to batch", "success")
apply_button_text = Text(
    "By clicking this button you will apply selected decisions to its images for the current batch",
    color="#5a6772",
)
apply_button_container = Container(
    widgets=[apply_button_text, apply_button], style="align-items: flex-end;"
)

finish_button = Button("Complete", "success")
finish_button_text_l1 = Text(
    'By clicking this button you will set review status "Complete" for the curren Labeling Job and close the workbench',
    color="#5a6772",
)
finish_button_text_l2 = Text(
    'If you want to review more images or just end without setting "Complete" status, click on the "Change Settings" button',
    color="#5a6772",
)
finish_button_container = Container(
    widgets=[finish_button_text_l1, finish_button_text_l2, finish_button],
    style="align-items: flex-end;",
)
finish_button_container.hide()
finish_button.disable()

description_text = Text(
    "Displaying pictures in the gallery depends on grouping and filtering settings, allowing you to customize your viewing experience. \n"
    "Tag editing is possible if activated before starting the process. ",
    "info",
)
g.image_gallery = ReviewGallery(
    columns_number=4,
    empty_message="",
)
review_progress = Progress()
button_container = Container(
    widgets=[apply_button_container, finish_button_container],
    style="margin-top: 20px; align-items: flex-end;  border-top: 1px solid #5a6772; padding-top: 10px;",
)
gallery_container = Container(
    widgets=[description_text, review_progress, g.image_gallery, button_container]
)
card = Card(
    title="🔬 Workbench",
    description="A comprehensive interface for reviewing a collection of images with their annotations",
    content=gallery_container,
    lock_message="Select the Labeling Job and andjust settings to start review process",
    collapsable=True,
    overflow="unset",
)
card.lock()
card.collapse()


@sly.timeit
@apply_button.click
def apply_decision():
    g.change_settings_button.disable()
    review_states: dict = g.image_gallery.get_review_states()
    tag_values: dict = g.image_gallery.get_tag_values()
    tag_change_states: dict = g.image_gallery.get_tag_change_states()
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
            g.job_info.id,
            image[0].id,
            review_state,
        )

    g.progress.update(len(g.image_batches[g.current_batch_idx]))
    if g.current_batch_idx < len(g.image_batches) - 1:
        g.current_batch_idx += 1
        g.image_gallery.clean_states()
        g.populate_gallery_func(g.image_gallery)
    else:
        g.image_gallery.clean_states()
        g.image_gallery.clean_up()
        sly.app.show_dialog(
            "Review process is finished",
            f"{'All' if g.progress.n == g.progress.total else g.progress.n} images have been reviewed. Now you can set \"Complete\" status for the Labeling Job or just choose another one by clicking on the \"Change Settings\" button",
            status="success",
        )
        if g.progress is not None:
            g.progress.close()
        finish_button.enable()
        finish_button_container.show()
        apply_button_container.hide()
    g.change_settings_button.enable()


@finish_button.click
def finish_review():
    g.finish_cb()
    finish_button.disable()
    apply_button_container.show()
