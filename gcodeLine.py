from enumDefinitions import GcodeCommands


class GcodeLine:
    def __init__(self, command: GcodeCommands, params: {}, comment: str):
        """
        Check to perform on the gcode file.
        param commandType: Type of command. See GcodeCommands Enum.
        param params: Dictionary containing any parameters. May be empty.
        param comment: Comment associated with command. If the line is ONLY a comment, the commandType will be COMMENT and this field will be filled.
        """
        self.commandType = command
        self.params = params
        self.comment = comment
