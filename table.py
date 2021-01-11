from colors import *

class Column():
    def __init__(self, text = '', justification = 'LEFT', min_width = 0):
        if text is None:
            text = ''
        elif not isinstance(text, str):
            text = str(text)
        self.text = text
        self.width = max(min_width, 0 if text is None else len(text.replace(COLOR_ERROR, '').replace(COLOR_RESET, '')) + 2)
        self.justification = justification

    def calculate_width(self, width):
        return max(width, self.width)

    def set_width(self, width):
        self.width = width

    def __str__(self):
        if self.text is None:
            return ' ' * self.width
        extra = 9 if COLOR_RESET in self.text else 0
        if self.justification == 'RIGHT':
            return ' ' + self.text.rjust(self.width - 2 + extra, ' ') + ' '
        return ' ' + self.text.ljust(self.width - 2 + extra, ' ') + ' '


class Row():
    def __init__(self):
        self.columns = []

    def add(self, column):
        self.columns.append(column)

    def calculate_widths(self, widths):
        if widths is None:
            widths = [0] * len(self.columns)
        for i in range(len(widths)):
            try:
                widths[i] = self.columns[i].calculate_width(widths[i])
            except IndexError:
                pass
        return widths

    def set_widths(self, widths):
        for i in range(len(widths)):
            try:
                self.columns[i].set_width(widths[i])
            except IndexError:
                pass

    def __str__(self):
        output = '┃'
        for column in self.columns:
            output += str(column)
            output += '┃'
        return output


class HeaderRow(Row):
    def __init__(self):
        super().__init__()

    def __str__(self):
        output = ''
        for i, column in enumerate(self.columns):
            if i == 0:
                output += '┏'
            else:
                output += '┳'
            output += '━' * column.width
        output += '┓\n'
        output += super().__str__()
        for i, column in enumerate(self.columns):
            if i == 0:
                output += '\n┣'
            else:
                output += '╋'
            output += '━' * column.width
        output += '┫'
        return output


class FooterRow(Row):
    def __init__(self):
        super().__init__()

    def __str__(self):
        output = ''
        for i, column in enumerate(self.columns):
            if i == 0:
                output += '┣'
            else:
                output += '╋'
            output += '━' * column.width
        output += '┫\n'
        output += super().__str__()
        return output


class Table():
    def __init__(self):
        self.rows = []

    def add(self, row):
        self.rows.append(row)

    def __str__(self):
        widths = None
        for row in self.rows:
            widths = row.calculate_widths(widths)
        output = '\n'
        last_row = None
        for row in self.rows:
            row.set_widths(widths)
            output += str(row) + '\n'
            last_row = row
        if last_row is not None:
            for i, column in enumerate(last_row.columns):
                if i == 0:
                    output += '┗'
                else:
                    output += '┻'
                output += '━' * column.width
            output += '┛'
        output += '\n'
        return output

