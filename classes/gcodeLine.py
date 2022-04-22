class GcodeLine:
    def __init__(self, command: str, params: [], comment: str):
        """
        Check to perform on the gcode file.
        param command: String representing the command. For example: 'M73' or ';' for a comment
        param params: List with all params for the command in the order they appear in the .gcode file. May be empty.
        param comment: Comment associated with command. If the line is ONLY a comment, the command will be ';' and this field will be filled.
        """
        self.command = command
        self.params = params
        self.comment = comment
