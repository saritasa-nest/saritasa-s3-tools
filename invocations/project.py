import invoke
import saritasa_invocations


@invoke.task
def build(
    context: invoke.Context,
) -> None:
    """Build python environment."""
    saritasa_invocations.poetry.install(context)


@invoke.task
def init(
    context: invoke.Context,
) -> None:
    """Prepare env for working with project."""
    saritasa_invocations.git.setup(context)
    saritasa_invocations.system.copy_vscode_settings(context)
    build(context)
    saritasa_invocations.docker.up(context)
