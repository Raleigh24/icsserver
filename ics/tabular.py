from operator import itemgetter


def print_table(table, header=None, col_sort=0):
    """Print a pretty table"""
    # Determine column width
    max_col_width = {}  # Maximum character width for each column
    col_count = 0

    # Find maximum number of columns
    for row in table:
        row_len = len(row)
        if row_len > col_count:
            col_count = len(row)

    # Initialize maximum column length
    if header is not None:
        for col_num in range(col_count):
            max_col_width[col_num] = len(header[col_num])
    else:
        for col_num in range(col_count):
            max_col_width[col_num] = 0

    # Determine column width
    for row in table:
        for col_num in range(col_count):
            if max_col_width[col_num] < len(str(row[col_num])):
                max_col_width[col_num] = len(str(row[col_num]))

    # Sort table
    sorted_table = sorted(table, key=itemgetter(col_sort))

    # Print Header
    if header is not None:
        header_str = ''
        for col_num in range(col_count):
            header_str = header_str + header[col_num].ljust(max_col_width[col_num] + 4)

        print(header_str.strip(' '))
        print('-' * len(header_str))

    # Print table
    for row in sorted_table:
        table_row = ''
        for col_num in range(col_count):
            table_row = table_row + str(row[col_num]).ljust(max_col_width[col_num] + 4)
        print(table_row.strip(' '))
