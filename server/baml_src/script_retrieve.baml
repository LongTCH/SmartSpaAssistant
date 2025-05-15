class ScriptRetrieveAgentOutput {
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
    - A list of pieces of information, each piece of information should be standalone script after rerank and filter. Each piece of information should be a detailed explanation of the customer's needs.
    Must not contain information that you can see in the previous chat history. Just contain new information.
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
