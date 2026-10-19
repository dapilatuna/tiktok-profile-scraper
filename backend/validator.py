def validate_username(username: str) -> str:
    username = username.strip().removeprefix("@")

    if not username:
        raise ValueError("Debes ingresar un nombre de usuario.")

    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._"

    if any(character not in allowed for character in username):
        raise ValueError("El nombre de usuario contiene caracteres no válidos.")

    return username