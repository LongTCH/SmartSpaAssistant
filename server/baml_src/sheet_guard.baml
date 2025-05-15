template_string SheetGuardSystemPrompt(dynamic_system_prompt: string) #"
    Read current customer's message, previous history and provided list of items.
    Determine if we should query more from sheets, OR send these information to next agent who will answer customer's question or ask more questions to clarify the customer's needs.
    {{dynamic_system_prompt}}
"#

function SheetGuardAgent(dynamic_system_prompt: string,
                    user_prompt: string,
                    message_history: BAMLMessage[]
                    ) -> bool {
  client OpenaiFallback
  prompt #"
    {{ PrintSystemPrompt(SheetGuardSystemPrompt(dynamic_system_prompt)) }}
    
    {{ PrintMessageHistory(message_history) }}
    {{ PrintUserPrompt(GetUserPrompt(user_prompt, "RESPONSE:")) }}
  "#
}

test TestSheetGuardAgent {
  functions [SheetGuardAgent]
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
