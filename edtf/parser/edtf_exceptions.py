from pyparsing import ParseException


class EDTFParseException(ParseException):
    """Raised when an input cannot be parsed as an EDTF string.

    Attributes:
    input_string - the input string that could not be parsed
    err -- the original ParseException that caused this one
    """

    def __init__(self, input_string, err=None):
        if input_string is None:
            input_string = ""
        self.input_string = input_string
        if err is None:
            err = ParseException(input_string, 0, "Invalid input or format.")
        self.err = err
        super().__init__(str(err), err.loc if err.loc else 0, self.input_string)

    def __str__(self):
        if not self.input_string:
            return "You must supply some input text"
        near_text = (
            self.input_string[max(self.err.loc - 10, 0) : self.err.loc + 10]
            if hasattr(self.err, "loc")
            else ""
        )
        return f"Error at position {self.err.loc}: Invalid input or format near '{near_text}'. Please provide a valid EDTF string."
