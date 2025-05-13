template_string SheetRAGSystemPrompt(dynamic_system_prompt: string) #"
    Know that previous SQL queries do not return any results.
    From the user's message and provided context, construct RAG query more information with sheet data.
    Carefully study the user's message, the context of scripts, sheet columns to provide more information about the customer's needs.
    From published sheets available from database, you need to analyze the sheets including their names, descriptions, especially column's type, description, example data.
    After analyzing the sheets, you can define the sheet_id, number of items and RAG query to use.
    {{dynamic_system_prompt}}
    NOTICE: You will query the RAG (Retrieval-Augmented Generation) database.
    Your input query will be converted into sparse embeddings.
    Sparse vector (BM25) captures exact keyword matches and term importance based on token frequency.
    It is effective for precise matches on specific terms or phrases.
    Each row of the knowledge sheet is represented as a vector in the RAG database
    identified by 'sheet.id' in the 'sheet' table of database.
"#
class SheetRAGAgentOutput {
    sheet_id string
    limit int @description(#"Maximum number of items to be returned from the RAG query"#)
    rag_query string
}
function SheetRAGAgent(dynamic_system_prompt: string,
                    user_prompt: string,
                    message_history: BAMLMessage[]
                    ) -> SheetRAGAgentOutput {
  client OpenaiFallback
  prompt #"
    {{ PrintSystemPrompt(SheetRAGSystemPrompt(dynamic_system_prompt)) }}
    
    {{ PrintMessageHistory(message_history) }}
    {{ PrintUserPrompt(GetUserPrompt(user_prompt, "JSON:")) }}
  "#
}

test TestSheetRAGAgent {
  functions [SheetRAGAgent]
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
