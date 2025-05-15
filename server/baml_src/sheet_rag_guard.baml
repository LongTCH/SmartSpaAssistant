template_string SheetRAGGuardSystemPrompt(dynamic_system_prompt: string) #"
    Read current customer's message, previous history and provided list of items.
    Carefully study the data to give information that can help to answer the customer's need.
    You must base on the relevance of customer's message and provided items to determine if suggest or not.
    If you cannot see any helpful information, please say "I don't know" and do not provide any information.
    {{dynamic_system_prompt}}
"#

function SheetRAGGuardAgent(dynamic_system_prompt: string,
                    user_prompt: string,
                    message_history: BAMLMessage[]
                    ) -> string {
  client OpenaiFallback
  prompt #"
    {{ PrintSystemPrompt(SheetRAGGuardSystemPrompt(dynamic_system_prompt)) }}
    
    {{ PrintMessageHistory(message_history) }}
    {{ PrintUserPrompt(GetUserPrompt(user_prompt, "JSON:")) }}
  "#
}

test TestSheetRAGGuardAgent {
  functions [SheetRAGGuardAgent]
  args {
    dynamic_system_prompt "Provided items: bộ B17, có giá là 1 triệu đồng, có khuyến mãi 20% cho khách hàng mới, giúp dưỡng trắng da tay chân và da body cực tốt"
    user_prompt #"
      tôi cần mua sản phẩm N3
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
