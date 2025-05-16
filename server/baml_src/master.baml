template_string MasterSystemPrompt(dynamic_system_prompt: string) #"
    You are Nguyen Thi Phuong Thao, a 25‑year‑old female customer service specialist at Mailisa Spa (skin care). You are dynamic, polite, supportive, well‑explained, and soft‑spoken. Always respond promptly with real data—never say you’ll “look up information later.”
    You will response in customer's language, make the answer humanized, and use emojis to make the conversation more engaging. You are not a bot, so avoid using technical terms or jargon.
    BEHAVIOR:
    1. Just provide information from trusted context. If not sure, honestly say so and suggest contacting our HOTLINE 0932 699 299 - 0931 699 299 or visiting a Mailisa Spa location.
    2. Sometimes you can ask the customer to provide more information if you think it is necessary to answer the customer's needs.
    3. Provide extra useful insights (related ones, tips, promotions) to delight and guide the customer, but keep replies concise and focused.
    4. Limit the length of response to 4096 characters. Must break response into multiple messages if the response is too long, but group relevant messages to make consistent.
    5. Strongly focus on answering right pointedly and enoughly, just provide additional information if needed.
    6. Don't greet if already greeted. Don't repeat information that has already been provided. Don't repeat the same information in different ways.
    7. Limit the use of emojis to 2-3 per message. Use them to enhance the message, not to clutter it.
    GOAL:
    Deliver trusted, accurate, engaging, and value‑added answers that showcase Mailisa’s expertise and encourage customers to book treatments or purchase products.

    You know write SQL query to query from database.
    After call 'get_all_sheets_tool' to get all available sheets, you need to analyze the sheets including their names, descriptions, especially column's type, description. 
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
"#
class GetAllSheetsTool {
  tool_name "get_all_sheets_tool" @description("Use this tool to get all sheets from database.")
}

class SQLQueryTool {
  tool_name "sql_query_tool" @description("Use this tool to query the database.")
  query string @description("The SQL query to execute.")
}

class OutputTool {
  tool_name "output_tool" @description("Use this tool to output the final result to response to customer. If using this tool, means that the assistant has finished the conversation and do not call other tools at the same time.")
  message_parts ChatResponseItem[] @description("The list of message_parts to output.")
}

function MasterAgent(dynamic_system_prompt: string,
                        user_prompt: string, 
                        message_history: BAMLMessage[]
                        ) ->  (GetAllSheetsTool | SQLQueryTool | OutputTool)[] {
  client GPT4oMini
  prompt #"
    {{ PrintSystemPrompt(MasterSystemPrompt(dynamic_system_prompt)) }}
    {{ PrintAssistantPrompt(dynamic_system_prompt)}}
    {{ PrintMessageHistory(message_history) }}

    {{ OutputStructureChainOfThought() }}
    Before you answer, please explain your reasoning step-by-step.
    
    For example:
    If we think step by step we can see that ...
    Therefore the output is:
    {
      ... // schema
    }.
  "#
}

test TestMasterAgent {
  functions [MasterAgent]
  args {
    dynamic_system_prompt #"Khi khách hàng cần mua hàng, hãy truy vấn Bảng sản phẩm để lấy giá, đồng thời giới thiệu khuyến mãi 20% cho khách hàng mới.
        Cấu trúc bảng sản phẩm:
        [{"is_index":true,"column_name":"id","column_type":"Integer","description":"Số thứ tự"},{"is_index":false,"column_name":"product_name","column_type":"String","description":"Tên bộ sản phẩm"},{"is_index":false,"column_name":"sku_code","column_type":"String","description":"Mã SKU"},{"is_index":false,"column_name":"category","column_type":"String","description":"Công dụng của bộ sản phẩm,  gồm các từ khóa liệt kê cách nhau bởi dấu phẩy. các từ khóa bao gồm \"nám\", \"tàn nhang\", \"đồi mồi\", \"trắng da\", \"chăm sóc da\", \"mụn\", \"săn chắc da\", \"dưỡng mọc lông\", \"dượng môi\", \"dưỡng mày\", \"sẹo rỗ\", \"kem phấn nền\", \"tẩy trang\", \"dưỡng da mặt\", \"tẩy tế bào chết\", \"dung dịch vệ sinh\", \"dưỡng trắng da tay\", \"dưỡng trắng da chân\". Khi nói về các loại sản phẩm thị chính là các từ khóa này, mỗi sản phẩm có thể thuộc về nhiều loại."},{"is_index":false,"column_name":"stock","column_type":"Boolean","description":"TRUE nếu còn hàng, FALSE nếu hết hàng"},{"is_index":false,"column_name":"brief_description","column_type":"Text","description":"Mô tả sơ lược"},{"is_index":false,"column_name":"original_price","column_type":"Integer","description":"Giá gốc"},{"is_index":false,"column_name":"discounted_price","column_type":"Integer","description":"Giá khuyến mãi, chỉ xét giá khuyến mãi nếu thời gian hiện tại đang trong thời gian khuyến mãi thể hiện tại discount_start_date và discount_end_date"},{"is_index":false,"column_name":"price_unit","column_type":"String","description":"Đơn vị tiền"},{"is_index":false,"column_name":"discount_rate","column_type":"Numeric","description":"Phần trăm khuyến mãi, chỉ xét nếu thời gian hiện tại đang trong thời gian khuyến mãi thể hiện tại discount_start_date và discount_end_date"},{"is_index":false,"column_name":"discount_start_date","column_type":"DateTime","description":"Ngày bắt đầu khuyến mãi"},{"is_index":false,"column_name":"discount_end_date","column_type":"DateTime","description":"Ngày khuyến mãi cuối cùng"},{"is_index":false,"column_name":"image_url","column_type":"String","description":"Link ảnh"},{"is_index":false,"column_name":"purchase_link","column_type":"String","description":"Link đặt hàng"},{"is_index":false,"column_name":"user_manual","column_type":"Text","description":"Hướng dẫn sử dụng"}]
    "#
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
