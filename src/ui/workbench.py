from supervisely.app.widgets import Button, Card, Container, Progress, Text

import src.globals as g
from src.ui.review_gallery.widget import ReviewGallery

apply_button = Button("Apply", "primary")
skip_batch_button = Button("Skip Batch", "primary")
finish_button = Button("Finish", "primary")
description_text = Text(
    "Displaying pictures in the gallery depends on grouping and filtering settings, allowing you to customize your viewing experience. \n"
    "Tag editing is possible if activated before starting the process. ",
    "info",
)
image_gallery = ReviewGallery(columns_number=5, empty_message="")
review_progress = Progress()
button_container = Container(
    widgets=[
        skip_batch_button,
        Container(widgets=[apply_button, finish_button]),
    ],
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
    review_state = image_gallery.get_review_state()
    for image in g.image_batches[g.current_batch_idx]:
        status = "accepted" if review_state[str(image[0].id)] else "rejected"
        g.api.labeling_job.set_entity_review_status(g.task_info.id, image[0].id, status)
    g.progress.update(len(g.image_batches[g.current_batch_idx]))
    if g.current_batch_idx < len(g.image_batches) - 1:
        g.current_batch_idx += 1
        g.populate_gallery_func(image_gallery)
    else:
        pass
