"""carkit.jev - the pipeline's decision layer, on Jev (TypeSafe's System One model).

Jev answers typed questions (choice, score, yes/no) about text or JSON state,
with calibrated probabilities, in well under a second and for a fraction of a
cent. It cannot see images and is weak at arithmetic, so the pipeline keeps
geometry, measurement and visual judgement where they are (code and the
agent), and hands Jev the narrow text decisions:

    client    the HTTP client (stdlib only: runs inside Blender too)
    finder    which carkit part / earlier-car builder / manual section fits a need
    triage    which known pipeline failure a traceback is, and its documented fix
    review    route review notes and user feedback to module, action, severity
    onboard   a new car's spec text -> feature checklist and module plan

See docs/3d-pipeline.md, "Decision layer (Jev)", for when to use each one
and when not to.
"""
from . import client  # noqa: F401
