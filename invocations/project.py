import invoke
import saritasa_invocations


@invoke.task
def init(
    context: invoke.Context,
) -> None:
    """Prepare env for working with project."""
    saritasa_invocations.git.setup(context)
    saritasa_invocations.system.copy_vscode_settings(context)
    saritasa_invocations.printing.print_success(
        "Install dependencies with poetry",
    )
    context.run("poetry sync --all-extras")
    saritasa_invocations.docker.up(context)
