
function MessageRewriteAgent(user_prompt: string) -> string {
  client OpenaiFallback
  prompt #"
    {{ PrintSystemPrompt("
    You are a helpful ai extractor assistant.
    From customer's message, you will rewrite customer's needs as a string query in customer's language.
    Fix the grammar and spelling errors.
    Just rewrite the message, do not add any additional information.
    Response in customer's language.
    ") }}
    {{ PrintUserPrompt(GetUserPrompt(user_prompt, "RESPONSE:")) }}
  "#
}



// Test the function with a sample resume. Open the VSCode playground to run this.
test TestMessageRewriteAgent {
  functions [MessageRewriteAgent]
  args {
    user_prompt #"
      cho toi 5 sản phẩm trị mụn đang có sale tốt nhứtnhứt
    "#
  }
}
