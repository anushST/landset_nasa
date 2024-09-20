"""Exceptions of users app."""


class EmailConfirmationTokenExpiredError(Exception):
    """Raise when email confirmation toke expired."""

    pass


class EmailConfirmationTokenInvalidError(Exception):
    """Raise when email confirmation toke invalid."""

    pass
