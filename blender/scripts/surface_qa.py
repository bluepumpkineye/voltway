"""Zebra and close-up QA renders - moved to carkit.qa.zebra; kept so old
imports keep working.

    import surface_qa
    surface_qa.render("nose_34", "v5", zebra=True)
"""
from carkit.qa.zebra import *                  # noqa: F401,F403
from carkit.qa.zebra import _camera            # noqa: F401
