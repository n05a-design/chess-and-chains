"""Tk desktop interface for the local Chess & Chains prototype."""


def launch() -> None:
    from .app import launch as run

    run()


__all__ = ["launch"]
