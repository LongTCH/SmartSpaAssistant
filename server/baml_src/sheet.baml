template_string SheetSystemPrompt(dynamic_system_prompt: string) #"
    From the user's message and provided context, construct SQL query to query more information with sheet data.
    Carefully study the user's message, the context of scripts, sheet columns to provide more information about the customer's needs.
    From published sheets available from database, you need to analyze the sheets including their names, descriptions, especially column's type, description. 
    Dont query too much information from sheets, but also dont make customer to re ask many times.
    Return the valid sql query.
    {{ dynamic_system_prompt }}
    Below are instructions for the you to write sql query:
    Query from {sheet.table_name} when you know the table_name via the sheet you are querying. FROM "{sheet.table_name}" is the table name you need to query from.
    You can use other fields of {table_name} specified in {sheet.column_config}, with normal operations to filter the query.
    You should use &@~ instead of = ,LIKE, ILIKE against string, text field of "{sheet.table_name}" to perform fulltext search, examine 'sheet.column_config' field of that sheet in 'sheets' table to know about these columns.
    In SQL, the correct order of statement is:
    SELECT …
    FROM …
    [WHERE …]
    [GROUP BY …]
    [HAVING …]
    [ORDER BY …]
    [LIMIT …];

    NOTICE: The table to query FROM is "{sheet.table_name}".
    Prefer using normal sql query to filter the data.
    You must enclose the table name and column names in double quotes.
    Carefully try different keywords when using LIKE, ILIKE for fulltext search.
    Dont use single quotes for table name and column names.

    For example:
    SELECT
      "product_name",
      "discounted_price"
    FROM "some_table_name"
    WHERE "product_price" > 100

    How to use PGroonga for text fields
    &@~ operator
    You can use &@~ operator to perform full text search by query syntax such as keyword1 OR keyword2:

    SELECT * FROM memos WHERE content &@~ '"PGroonga" OR "PostgreSQL"';
    --  id |                            content
    -- ----+----------------------------------------------------------------
    --   3 | PGroonga is a PostgreSQL extension that uses Groonga as index.
    --   1 | PostgreSQL is a relational database management system.
    -- (2 rows)
    Query syntax is similar to syntax of Web search engine ( "keyword1" OR "keyword2" means OR search and "keyword1" "keyword2" means AND search ). For example, you can use OR to merge result sets of performing full text search by two or more words. In the above example, you get a merged result set. The merged result set has records that includes "PGroonga" or "PostgreSQL".
    You must always enclose the pgroonga query in parentheses, for example: FROM "some_table_name" WHERE ("data_fts" &@~ 'a OR b')​

    Example 1:
    If the input keyword string is: 'tàn nhang'
    Then the SQL query should be:
    SELECT
      "product_name",
      "discounted_price"
    FROM "some_table_name"
    WHERE ("description" &@~ '"tàn nhang"')

    Normal query without fulltext search.
    Example 2:
    SELECT
      "product_name",
      "discounted_price"
    FROM "some_table_name" as tb
    WHERE tb."product_price" > 100

    NOTE: Also return the sheet_id and limit for the RAG vector database query if not found any data by sql_query.
"#
class SheetAgentOutput {
    sql_query string @description("The valid sql query to query from the sheet.")
    sheet_id string @description("The sheet_id to query from.")
    limit int @description("The maximum number of items to return by using RAG.")
}
function SheetAgent(dynamic_system_prompt: string,
                    user_prompt: string, 
                    message_history: BAMLMessage[]
                    ) -> SheetAgentOutput {
  client OpenaiFallback
  prompt #"
    {{ PrintSystemPrompt(SheetSystemPrompt(dynamic_system_prompt)) }}
    
    {{ PrintMessageHistory(message_history) }}
    {{ PrintUserPrompt(GetUserPrompt(user_prompt, "JSON:")) }}
  "#
}

test TestSheetAgent {
  functions [SheetAgent]
  args {
    dynamic_system_prompt "Khi khách hàng cần mua hàng, hãy truy vấn Bảng sản phẩm để lấy giá, đồng thời giới thiệu khuyến mãi 20% cho khách hàng mới."
    user_prompt #"
      tôi cần mua 1 bộ M66
    "#
    message_history [{
      role "user"
      content "xin chào"
    },
    {
      role "assistant",
      content "Chào bạn, tôi có thể giúp gì cho bạn?"
    }]
  }
}
