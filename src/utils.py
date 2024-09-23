from collections import defaultdict
from typing import Dict, List

import supervisely as sly
from supervisely.api.api import ApiField
from supervisely.api.entity_annotation.figure_api import FigureApi

import src.globals as g


def handle_exception_dialog(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            title = type(e).__name__
            descr = f'Error occured in "{func.__name__}" function. Description: {str(e)}'
            sly.app.show_dialog(title, descr, status="error")
            sly.logger.error(f"{title}: {descr}")

    return wrapper


def list_light_figures_info(
    dataset_id: int,
) -> Dict[int, List[sly.FigureInfo]]:
    """
    Method returns a dictionary with pairs of image ID and list of FigureInfo for the given dataset ID.
    This FigureInfo does not contain geometry information.
    Conntains only image ID, class ID and figure ID.
    Use it only for filtering and sorting purposes.

    :param dataset_id: Dataset ID in Supervisely.
    :type dataset_id: int
    :return: A dictionary where keys are image IDs and values are lists of FigureInfo.
    :rtype: :class: `Dict[int, List[FigureInfo]]`
    """
    fields = ["id", "imageId", "classId"]
    data = {
        ApiField.DATASET_ID: dataset_id,
        ApiField.FIELDS: fields,
        ApiField.FILTER: [],
    }
    if g.api.headers.get("x-job-id") != str(id):
        g.api.add_header("x-job-id", str(id))
    resp = g.api.post("figures.list", data)
    infos = resp.json()
    images_figures = defaultdict(list)
    total_pages = infos["pagesCount"]
    for page in range(1, total_pages + 1):
        if page > 1:
            data.update({ApiField.PAGE: page})
            resp = g.api.post("figures.list", data)
            infos = resp.json()
        for info in infos["entities"]:
            figure_info = g.api.image.figure._convert_json_info(info, True)
            images_figures[figure_info.entity_id].append(figure_info)

    if g.api.headers.get("x-job-id") == str(id):
        g.api.pop_header("x-job-id")

    return dict(images_figures)
