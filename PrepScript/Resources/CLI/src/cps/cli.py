"""Thin command-line entry point for the existing CPS script."""

from .bootstrap import Run_CPS


def main(argv=None):
    """Forward all arguments to the existing CRESM_Preprocessing_System.py."""
    return Run_CPS(argv)
