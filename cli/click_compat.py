"""Click-compatible CLI framework using Python standard library."""

import argparse
import sys
from typing import Any, Callable


class Abort(Exception):
    """Exception raised to abort command execution."""

    pass


def echo(message: str, err: bool = False) -> None:
    """Print message to stdout or stderr.

    Args:
        message: Message to print
        err: If True, print to stderr; otherwise print to stdout
    """
    stream = sys.stderr if err else sys.stdout
    print(message, file=stream)


class Choice:
    """Click.Choice equivalent for argument choices."""

    def __init__(self, choices: list[str]):
        """Initialize choice validator.

        Args:
            choices: List of valid choices
        """
        self.choices = choices

    def __call__(self, value: str) -> str:
        """Validate choice value.

        Args:
            value: Value to validate

        Returns:
            Validated value

        Raises:
            ValueError: If value is not in choices
        """
        if value not in self.choices:
            raise ValueError(f"Invalid choice: {value}. Choose from {self.choices}")
        return value


class _Command:
    """Represents a CLI command."""

    def __init__(self, name: str, func: Callable, helpText: str | None = None):
        """Initialize command.

        Args:
            name: Command name
            func: Command handler function
            helpText: Command help text
        """
        self.name = name
        self.func = func
        self.helpText = helpText or func.__doc__ or ""
        self.options: list[dict[str, Any]] = []
        self.arguments: list[dict[str, Any]] = []

    def addOption(self, *flags: str, **kwargs: Any) -> None:
        """Add option to command.

        Args:
            *flags: Option flags
            **kwargs: Option parameters
        """
        self.options.append({"flags": flags, "kwargs": kwargs})

    def addArgument(self, name: str, **kwargs: Any) -> None:
        """Add argument to command.

        Args:
            name: Argument name
            **kwargs: Argument parameters
        """
        self.arguments.append({"name": name, "kwargs": kwargs})

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """Execute command."""
        self.func(*args, **kwargs)


class _Group:
    """Represents a CLI command group."""

    def __init__(self, name: str | None, func: Callable, helpText: str | None = None):
        """Initialize group.

        Args:
            name: Group name
            func: Group handler function
            helpText: Group help text
        """
        self.name = name or ""
        self.func = func
        self.helpText = helpText or func.__doc__ or ""
        self.commands: dict[str, _Command | _Group] = {}
        self.options: list[dict[str, Any]] = []
        self.arguments: list[dict[str, Any]] = []

    def addOption(self, *flags: str, **kwargs: Any) -> None:
        """Add option to group.

        Args:
            *flags: Option flags
            **kwargs: Option parameters
        """
        self.options.append({"flags": flags, "kwargs": kwargs})

    def addArgument(self, name: str, **kwargs: Any) -> None:
        """Add argument to group.

        Args:
            name: Argument name
            **kwargs: Argument parameters
        """
        self.arguments.append({"name": name, "kwargs": kwargs})

    def add_command(self, command: "_Command | _Group") -> None:
        """Add command to group.

        Args:
            command: Command or group to add
        """
        self.commands[command.name] = command

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """Execute group (process CLI arguments)."""
        if args:
            sys.argv = [sys.argv[0]] + list(args)
        else:
            args = sys.argv[1:]

        if not args:
            self._showHelp()
            return

        commandName = args[0]
        if commandName in self.commands:
            cmd = self.commands[commandName]
            if isinstance(cmd, _Group):
                cmd(*args[1:])
            else:
                self._executeCommand(cmd, args[1:])
        else:
            echo(f"Error: Unknown command '{commandName}'", err=True)
            self._showHelp()
            sys.exit(1)

    def _executeCommand(self, command: _Command, args: list[str]) -> None:
        """Execute a command with parsed arguments.

        Args:
            command: Command to execute
            args: Command line arguments
        """
        parser = argparse.ArgumentParser(prog=command.name, description=command.helpText)

        for option in command.options:
            flags = option["flags"]
            kwargs = option["kwargs"].copy()

            optionType = kwargs.get("type", str)
            if optionType == bool:
                kwargs["action"] = "store_true"
                if "default" not in kwargs:
                    kwargs["default"] = False
                kwargs.pop("type", None)
            elif isinstance(optionType, Choice):
                kwargs["choices"] = optionType.choices
                kwargs.pop("type", None)

            if "default" in kwargs and kwargs.get("required", False):
                kwargs.pop("default", None)

            parser.add_argument(*flags, **kwargs)

        for arg in command.arguments:
            argName = arg["name"]
            argKwargs = arg["kwargs"].copy()

            argType = argKwargs.get("type", str)
            if isinstance(argType, Choice):
                argKwargs["choices"] = argType.choices
                argKwargs.pop("type", None)

            if "required" in argKwargs:
                argKwargs.pop("required")

            parser.add_argument(argName, **argKwargs)

        parsed = parser.parse_args(args)
        kwargs = vars(parsed)

        try:
            command.func(**kwargs)
        except Abort:
            sys.exit(1)
        except Exception as e:
            echo(f"Error: {e}", err=True)
            sys.exit(1)

    def _showHelp(self) -> None:
        """Show help message."""
        if self.helpText:
            echo(self.helpText)
        echo("")
        echo("Available commands:")
        for name in sorted(self.commands.keys()):
            echo(f"  {name}")


def command(name: str | None = None, **kwargs: Any) -> Callable:
    """Decorator to register a CLI command.

    Args:
        name: Command name (default: function name)
        **kwargs: Additional command parameters (help, etc.)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> _Command:
        commandName = name or func.__name__
        cmd = _Command(commandName, func, kwargs.get("help"))

        if hasattr(func, "_click_options"):
            for opt in func._click_options:
                cmd.addOption(*opt["flags"], **opt["kwargs"])

        if hasattr(func, "_click_arguments"):
            for arg in func._click_arguments:
                cmd.addArgument(arg["name"], **arg["kwargs"])

        return cmd

    return decorator


def option(*flags: str, **kwargs: Any) -> Callable:
    """Decorator to add option to command.

    Args:
        *flags: Option flags (e.g., "--config", "-c")
        **kwargs: Option parameters (type, default, help, required, etc.)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_click_options"):
            func._click_options = []

        func._click_options.append({"flags": flags, "kwargs": kwargs})
        return func

    return decorator


def argument(name: str, **kwargs: Any) -> Callable:
    """Decorator to add argument to command.

    Args:
        name: Argument name
        **kwargs: Argument parameters (type, required, etc.)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_click_arguments"):
            func._click_arguments = []

        func._click_arguments.append({"name": name, "kwargs": kwargs})
        return func

    return decorator


def group(name: str | None = None, **kwargs: Any) -> Callable:
    """Decorator to register a command group.

    Args:
        name: Group name (default: function name)
        **kwargs: Additional group parameters (help, etc.)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> _Group:
        groupName = name or func.__name__
        grp = _Group(groupName, func, kwargs.get("help"))

        if hasattr(func, "_click_options"):
            for opt in func._click_options:
                grp.addOption(*opt["flags"], **opt["kwargs"])

        if hasattr(func, "_click_arguments"):
            for arg in func._click_arguments:
                grp.addArgument(arg["name"], **arg["kwargs"])

        func._command_group = grp
        return grp

    return decorator
