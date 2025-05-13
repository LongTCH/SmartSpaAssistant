function MemoryAgent(user_prompt: string) -> string {
  client OpenaiFallback
  prompt #"
    {{ PrintSystemPrompt("
    You are a helpful ai extractor assistant.
    You will be given an interval of chat history between the customer and the assistant.
    Your task is to extract the most important keywords to describe customer's insight and information, mainly using latest messages, into a string.
    Please write in customer's language.
    This string will be stored in database as long-term memory, so keep it short, concise and relevant.
    ") }}
    {{ PrintUserPrompt(GetUserPrompt(user_prompt, "RESPONSE:")) }}
  "#
}

test TestMemoryAgent {
  functions [MemoryAgent]
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
