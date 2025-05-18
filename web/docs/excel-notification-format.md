# Excel Import/Export Documentation

This document describes the Excel format used for importing and exporting notifications in the system.

## Excel Structure

The Excel file used for importing notifications must follow this specific structure:

### Main Data Sheet

- Sheet name: `data`
- Contains information about all notifications
- Columns:
  - `id`: Integer from 1 to n (required)
  - `label`: Text label for the notification (required)
  - `color`: Color code in hex format (e.g., #FF0000) (required)
  - `status`: Either "published" or "draft" (required)
  - `description`: Text description of the notification (required)
  - `content`: Template content with variable placeholders (required)

### Parameter Sheets

- For each notification in the data sheet, there must be a separate sheet named `n_[id]`
  - Example: For notification with id=1, the sheet name would be `n_1`
- Each parameter sheet contains columns:
  - `index`: Parameter order (0-based index)
  - `param_name`: Name of the parameter (must be valid variable name)
  - `param_type`: Type of parameter (String, Numeric, etc.)
  - `description`: Description of the parameter

## Example

### Sheet: data

| id  | label              | color   | status    | description            | content                                         |
| --- | ------------------ | ------- | --------- | ---------------------- | ----------------------------------------------- |
| 1   | Order Confirmation | #2196F3 | published | New order notification | You have a new order from {{customer_name}}...  |
| 2   | Delivery Update    | #4CAF50 | published | Delivery status update | Your order #{{order_id}} has been {{status}}... |

### Sheet: n_1

| index | param_name    | param_type | description          |
| ----- | ------------- | ---------- | -------------------- |
| 0     | customer_name | String     | Name of the customer |
| 1     | order_id      | String     | Order identifier     |
| 2     | total         | Numeric    | Total order value    |

### Sheet: n_2

| index | param_name | param_type | description             |
| ----- | ---------- | ---------- | ----------------------- |
| 0     | order_id   | String     | Order identifier        |
| 1     | status     | String     | Current delivery status |

## Import Process

1. Upload Excel file
2. System validates the structure
3. Creates notifications based on data sheet
4. Creates parameters for each notification based on parameter sheets

## Export Process

1. System generates an Excel file with same structure
2. Data sheet contains all notifications
3. Parameter sheets are created for each notification
