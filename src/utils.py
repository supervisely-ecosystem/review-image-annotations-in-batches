import supervisely as sly


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
