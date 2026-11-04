# The class registry

Every tool built for Assignment 3 lives here, one folder per implementation:

    registry/tools/<tool_name>/<your_id>/
        tool.py
        tool.json
        README.md
        tests/test_<tool_name>.py   (at least five tests)

To add yours: copy `template/` to that folder, fill it in, then from the repository root run:

    python -m graphkit.validate registry/tools/<tool_name>/<your_id>
    python -m pytest registry/tools/<tool_name>/<your_id>/tests

Package your `registry/tools/<tool_name>/<your_id>/` folder alongside your `bootcamp/` folder into your submission zip file.
After the deadline, the course staff will collect and combine all student tool folders into a shared toolbox for the group project.
