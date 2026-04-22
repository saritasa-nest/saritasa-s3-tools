import os

import invoke
import saritasa_invocations

import invocations

ns = invoke.Collection(
    invocations.ci,
    invocations.docs,
    invocations.project,
    saritasa_invocations.docker,
    saritasa_invocations.git,
    saritasa_invocations.github_actions,
    saritasa_invocations.pre_commit,
    saritasa_invocations.python,
    saritasa_invocations.system,
    saritasa_invocations.poetry,
    saritasa_invocations.mypy,
    saritasa_invocations.pytest,
    saritasa_invocations.django,
    saritasa_invocations.open_api,
)

# Configurations for run command
ns.configure(
    {
        "run": {
            "pty": os.environ.get("INVOKE_PTY", "true").lower() == "true",
            "echo": True,
        },
        "saritasa_invocations": saritasa_invocations.Config(
            project_name="saritasa-s3-tools",
            docker=saritasa_invocations.DockerSettings(
                main_containers=(
                    "minio",
                    "minio-create-bucket",
                    "postgres",
                ),
            ),
            django=saritasa_invocations.DjangoSettings(
                settings_path="example.settings",
                manage_file_path="example/manage.py",
            ),
        ),
    },
)
