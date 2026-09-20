"""Public API for the thin CPS launcher package."""

from ._version import version as __version__


def main(argv=None):
    """Run the CPS command-line interface from Python."""
    from .cli import main as cli_main

    return cli_main(argv)


__all__ = ["__version__", "main"]
