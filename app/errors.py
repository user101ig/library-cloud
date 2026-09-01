"""Κοινά σφάλματα του service layer."""


class AppError(Exception):
    status_code = 500
    detail = "Internal server error"


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409
