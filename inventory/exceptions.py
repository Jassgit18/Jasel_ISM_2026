from rest_framework.views import exception_handler   # DRF's default error handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)       # let DRF build its normal error response first

    if response is not None:                         # None means it was not a DRF error
        response.data = {                            # wrap every error in the same shape
            "success": False,
            "status_code": response.status_code,     # for example 400, 403, 404
            "errors": response.data,                 # the original error details
        }
    return response