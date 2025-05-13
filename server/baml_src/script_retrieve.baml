class ScriptRetrieveAgentOutput {
    should_query_sheet bool
    pieces_of_information string[]
}

function ScriptRetrieveAgent(dynamic_system_prompt: string,
                        user_prompt: string, 
                        message_history: BAMLMessage[]
                        ) -> ScriptRetrieveAgentOutput {
  client OpenaiFallback
  prompt #"
    {{ PrintSystemPrompt("
    You are a helpful ai extractor assistant.
    You will be provided with customer's message and a list of scripts.
    Carefully study the scripts to define if we should query more from sheets.
    Rerank and filter relevant information from the scripts.
    Your response will contain the following:
    - A boolean value indicating if we should query more from sheets.
    - A list of pieces of information, each piece of information should be standalone script after rerank and filter. Each piece of information should be a detailed explanation of the customer's needs. Return at least 5 pieces of detailed information.
    NOTE:
    - If you set should_query_sheet to False, it means that you you decided information from scripts are enough to answer the customer's needs, and you need to provide detailed pieces of information that used to answer the customer's needs.
    - If you set should_query_sheet to True, it means that you need to query more from sheets, and you need to provide detailed pieces of information that can instruct other agents to fulfill the customer's needs.
    Response in customer's language.
    ") }}
    
    {{ PrintMessageHistory(message_history) }}
    {{ PrintAssistantPrompt(dynamic_system_prompt)}}
    {{ PrintUserPrompt(GetUserPrompt(user_prompt, "JSON:")) }}

  "#
}

test TestScriptRetrieveAgent {
  functions [ScriptRetrieveAgent]
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
