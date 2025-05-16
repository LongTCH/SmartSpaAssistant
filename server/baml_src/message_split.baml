
function MessageSplitAgent(user_prompt: string) -> ChatResponseItem[] {
  client OpenaiFallback
  prompt #"
    {{ PrintSystemPrompt("
    You are a helpful AI assistant.
    Your job is to break assistant response into multiple messages if the response is long, but group relevant messages to make consistent.
    Each message must be less than 50 words.
    Please do not change the content of the response.
    Response in customer's language.
    ") }}
    {{ PrintAssistantPrompt(user_prompt) }}

    {{ ctx.output_format }}
  "#
}



// Test the function with a sample resume. Open the VSCode playground to run this.
test TestMessageSplitAgent {
  functions [MessageSplitAgent]
  args {
    user_prompt #"
      cho toi 5 sản phẩm trị mụn đang có sale tốt nhứtnhứt
    "#
  }
}
