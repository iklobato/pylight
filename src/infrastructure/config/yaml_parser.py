"""Manual YAML parser for configuration files using Python standard library."""

import re
from typing import Any

from src.domain.errors import ConfigurationError


class YAMLParser:
    """Minimal YAML parser for configuration files."""

    @staticmethod
    def parse(content: str) -> dict[str, Any]:
        """Parse YAML content into dictionary.

        Args:
            content: YAML file content as string

        Returns:
            Parsed configuration dictionary

        Raises:
            ConfigurationError: If YAML syntax is invalid (with line number and context)
            ConfigurationError: If content cannot be parsed
        """
        if not content.strip():
            return {}

        lines = content.split("\n")
        parser = YAMLParser._Parser(lines)
        try:
            result = parser.parse()
            if not isinstance(result, dict):
                raise ConfigurationError("YAML root must be a dictionary")
            return result
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"YAML parsing error: {e}") from e

    class _Parser:
        """Internal YAML parser implementation."""

        def __init__(self, lines: list[str]):
            """Initialize parser with lines.

            Args:
                lines: List of YAML file lines
            """
            self.lines = lines
            self.currentLine = 0
            self.lineNumber = 0

        def parse(self) -> Any:
            """Parse YAML content starting from current position.

            Returns:
                Parsed value (dict, list, or scalar)
            """
            result = self._parseValue(0)
            if self.currentLine < len(self.lines):
                self._raiseError("Unexpected content after root element")
            return result

        def _parseValue(self, indent: int) -> Any:
            """Parse a YAML value at given indentation level.

            Args:
                indent: Current indentation level

            Returns:
                Parsed value
            """
            if self.currentLine >= len(self.lines):
                return None

            line = self.lines[self.currentLine]
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                self.currentLine += 1
                return self._parseValue(indent)

            currentIndent = len(line) - len(stripped)

            if currentIndent < indent:
                return None

            if currentIndent > indent:
                self._raiseError(f"Unexpected indentation at line {self.lineNumber + 1}")

            if stripped.startswith("-"):
                return self._parseList(indent)
            if ":" in stripped:
                return self._parseDict(indent)
            return self._parseScalar()

        def _parseDict(self, indent: int) -> dict[str, Any]:
            """Parse YAML dictionary.

            Args:
                indent: Current indentation level

            Returns:
                Parsed dictionary
            """
            result: dict[str, Any] = {}
            startLine = self.currentLine

            while self.currentLine < len(self.lines):
                line = self.lines[self.currentLine]
                stripped = line.lstrip()
                if not stripped or stripped.startswith("#"):
                    self.currentLine += 1
                    continue

                currentIndent = len(line) - len(stripped)
                if currentIndent < indent:
                    break
                if currentIndent > indent:
                    self._raiseError(f"Unexpected indentation at line {self.lineNumber + 1}")

                if ":" not in stripped:
                    break

                keyValue = stripped.split(":", 1)
                key = keyValue[0].strip()
                valueStr = keyValue[1].strip() if len(keyValue) > 1 else ""

                if not key:
                    self._raiseError(f"Empty key at line {self.lineNumber + 1}")

                self.lineNumber = self.currentLine
                self.currentLine += 1

                if valueStr:
                    value = self._parseScalarValue(valueStr)
                else:
                    nextValue = self._parseValue(indent + 2)
                    if nextValue is None:
                        value = None
                    else:
                        value = nextValue
                        self.currentLine -= 1

                result[key] = value

            if not result and startLine == self.currentLine:
                self._raiseError(f"Empty dictionary at line {self.lineNumber + 1}")

            return result

        def _parseList(self, indent: int) -> list[Any]:
            """Parse YAML list.

            Args:
                indent: Current indentation level

            Returns:
                Parsed list
            """
            result: list[Any] = []

            while self.currentLine < len(self.lines):
                line = self.lines[self.currentLine]
                stripped = line.lstrip()
                if not stripped or stripped.startswith("#"):
                    self.currentLine += 1
                    continue

                currentIndent = len(line) - len(stripped)
                if currentIndent < indent:
                    break

                if not stripped.startswith("-"):
                    break

                itemStr = stripped[1:].strip()
                self.lineNumber = self.currentLine
                self.currentLine += 1

                if itemStr:
                    item = self._parseScalarValue(itemStr)
                else:
                    item = self._parseValue(indent + 2)
                    if item is None:
                        item = None
                    else:
                        self.currentLine -= 1

                result.append(item)

            return result

        def _parseScalar(self) -> Any:
            """Parse scalar value from current line.

            Returns:
                Parsed scalar value
            """
            line = self.lines[self.currentLine]
            stripped = line.lstrip()
            self.lineNumber = self.currentLine
            self.currentLine += 1
            return self._parseScalarValue(stripped)

        def _parseScalarValue(self, value: str) -> Any:
            """Parse scalar value string.

            Args:
                value: Scalar value string

            Returns:
                Parsed value (string, number, boolean, null)
            """
            value = value.strip()

            if value == "":
                return None

            if value == "null" or value == "~" or value == "Null" or value == "NULL":
                return None

            if value == "true" or value == "True" or value == "TRUE":
                return True

            if value == "false" or value == "False" or value == "FALSE":
                return False

            if value.startswith('"') and value.endswith('"'):
                return value[1:-1].replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")

            if value.startswith("'") and value.endswith("'"):
                return value[1:-1]

            if re.match(r"^-?\d+$", value):
                return int(value)

            if re.match(r"^-?\d+\.\d+$", value):
                return float(value)

            return value

        def _raiseError(self, message: str) -> None:
            """Raise configuration error with line number and context.

            Args:
                message: Error message

            Raises:
                ConfigurationError: Always raises
            """
            lineNum = self.lineNumber + 1
            context = ""
            if 0 <= self.lineNumber < len(self.lines):
                context = f" Context: {self.lines[self.lineNumber].strip()}"
            raise ConfigurationError(f"YAML syntax error at line {lineNum}: {message}.{context}")


