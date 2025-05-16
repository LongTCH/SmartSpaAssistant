template_string SheetGuardSystemPrompt(dynamic_system_prompt: string) #"
    You are a helpful ai routing assistant.
    Read current customer's message, previous history and sheet information.
    Carefully study the user's message, the context of scripts, sheet columns to provide more information about the customer's needs.
    From published sheets available from database, you need to analyze the sheets including their names, descriptions, especially column's type, description.
    Determine if we could find more helpful information by querying more from sheets, OR send these information to next agent who will answer customer's question.
    Dont make too frequent queries to sheets, but also dont make customer to re ask many times.
    
"#

class SheetGuardAgentOutput{
    should_query_sheet bool
}

function SheetGuardAgent(dynamic_system_prompt: string,
                    user_prompt: string,
                    message_history: BAMLMessage[]
                    ) -> SheetGuardAgentOutput {
  client OpenaiFallback
  prompt #"
    {{ PrintSystemPrompt(SheetGuardSystemPrompt(dynamic_system_prompt)) }}
    
    {{ PrintMessageHistory(message_history) }}
    {{ PrintAssistantPrompt(dynamic_system_prompt) }}
    {{ PrintUserPrompt(GetUserPrompt(user_prompt, "JSON:")) }}
    {{ CommonChainOfThoughts() }}
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
