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
    Carefully study the scripts and the description of each sheet to define if we should query more from sheets.
    Rerank and filter relevant information from the scripts.
    Your response will contain the following:
    - A boolean value indicating if we should query more from sheets.
    - A list of pieces of information, each piece of information should be standalone script after rerank and filter. Each piece of information should be a detailed explanation of the customer's needs.
    NOTE:
    - If you think information from scripts are enough to answer the customer's needs, OR any information instruct you to prompt more from customers to clarify their needs, so set should_query_sheet to False
    - If you think that customer've provided enough condition data for query sheet and should query sheet for for information, set should_query_sheet to True.    
    if you need to prompt more from customer, please provide a list of pieces of information that you need to ask the customer.
    Must not contain information that you can see in the previous chat history. Just contain new information.
    Response in customer's language.
    ") }}
    
    {{ PrintMessageHistory(message_history) }}
    {{ PrintAssistantPrompt(dynamic_system_prompt)}}
    {{ PrintUserPrompt(GetUserPrompt(user_prompt, "JSON:")) }}
    {{ OutputStructureChainOfThought() }}
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
