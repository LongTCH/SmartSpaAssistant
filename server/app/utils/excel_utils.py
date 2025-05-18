import pandas as pd


def adjust_column_widths_in_worksheet(worksheet, dataframe):
    for idx, col_name_str in enumerate(dataframe.columns):
        column_letter = chr(65 + idx)
        header_len = len(str(col_name_str))

        if not dataframe[col_name_str].empty:
            try:
                data_max_len = dataframe[col_name_str].astype(str).map(len).max()
            # Handle potential errors if astype(str) fails for some complex types
            except TypeError:
                data_max_len = header_len
        else:
            data_max_len = 0

        if pd.isna(data_max_len):
            data_max_len = 0

        data_max_len = int(data_max_len)
        max_len = max(header_len, data_max_len)
        # Min width 10, Max width 50
        adjusted_width = min(max(max_len + 2, header_len + 2, 10), 50)
        worksheet.column_dimensions[column_letter].width = adjusted_width
