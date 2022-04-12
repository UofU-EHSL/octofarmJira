from enumDefinitions import GcodeCheckActions


class GcodeCheckItem:
    def __init__(self, command: str, checkAction: GcodeCheckActions, actionValue: str):
        """
        Check to perform on the gcode file.
        param commandType: Type of command to perform.
        param checkAction: Type of action to perform with the commandType. See GcodeCheckActions Enum.
        param actionValue: Value associated with the command and type if required. For example, the string to check for in a comment.
        """
        self.command = command
        self.checkAction = checkAction
        self.actionValue = actionValue
