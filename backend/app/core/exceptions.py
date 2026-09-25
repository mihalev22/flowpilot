class AppError(Exception):
    status_code = 400
    message = "Ошибка запроса"

    def __init__(self, message: str | None = None, status_code: int | None = None):
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code


class AuthError(AppError):
    status_code = 401
    message = "Требуется авторизация"


class ForbiddenError(AppError):
    status_code = 403
    message = "Недостаточно прав"


class NotFoundError(AppError):
    status_code = 404
    message = "Объект не найден"


class ConflictError(AppError):
    status_code = 409
    message = "Конфликт данных"
