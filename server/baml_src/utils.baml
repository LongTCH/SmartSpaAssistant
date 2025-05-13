class BAMLMessage {
  role "user" | "assistant"
  content string
}

// Inject a list of "assistant" or "user" messages into the prompt.
template_string PrintMessageHistory(messages: BAMLMessage[]) #"
  {% if messages|length > 0 %}
    {% if "notexist" in ctx.client.name|lower %}
      {% for m in messages %}
        {% if m.role == "user" %}
        <start_of_turn>user
        {{ m.content }}<end_of_turn>\n
        {% else %}
        <start_of_turn>model
        {{ m.content }}<end_of_turn>\n
        {% endif %}
      {% endfor %}
    {% else %}
      Here is the previous chat history:
      {% for m in messages %}
        {{ _.role(m.role) }}
        {{ m.content }}
      {% endfor %}
    {% endif %}
  {% endif %}
"#

template_string PrintSystemPrompt(system_prompt: string) #"
  {% if system_prompt %}
    {% if "notexist" in ctx.client.name|lower %}
      <start_of_turn>user
      {{ system_prompt }}<end_of_turn>\n
    {% else %}
      {{ _.role("system") }}
      {{ system_prompt }}
    {% endif %}
  {% endif %}
"#

template_string GetUserPrompt(user_prompt: string, response: string) #"
    ---------------
    {{ user_prompt }}
    ---------------

    {{ ctx.output_format }}
    {{ response }}
"#

template_string PrintUserPrompt(user_prompt: string) #"
  {% if user_prompt %}
    {% if "notexist" in ctx.client.name|lower %}
      <start_of_turn>user
      Current customer's message:
      {{ user_prompt }}<end_of_turn>\n
    {% else %}
      {{ _.role("user") }}
      Current customer's message:
      {{ user_prompt }}
    {% endif %}
  {% endif %}
"#

template_string PrintAssistantPrompt(assistant_prompt: string) #"
  {% if assistant_prompt %}
    {% if "notexist" in ctx.client.name|lower %}
      <start_of_turn>model
      {{ assistant_prompt }}<end_of_turn>\n
    {% else %}
      {{ _.role("assistant") }}
      {{ assistant_prompt }}
    {% endif %}
  {% endif %}
"#

// function GenericQuery(systemPrompt: string, userPrompt: string) -> string {
//   client Gemini2FlashLite

//   prompt #"
//     {{ _.role("system") }}

//     {{ systemPrompt }}

//     {{ _.role("user") }}
//     {{ userPrompt }}
//   "#
// }

// test generic_query {
//   functions [GenericQuery]
//   args {
//     systemPrompt "Anwser in the voice of Pikachu."
//     userPrompt "What's the capital of France?"
//   }
// }

// class GenericStructuredResponse {
//   @@dynamic
// }

// function GenericStructuredOutputCall(systemPrompt: string, userPrompt: string, messages: Message[]) -> GenericStructuredResponse{
//   client Gemini2FlashLite

//   prompt #"
//     {{ _.role("system") }}

//     {{ systemPrompt }}

//     {{ _.role("user") }}
//     {{ userPrompt }}

//     {{ ctx.output_format }}
//     Give step by step reasoning before giving the final answer in JSON format.
//     Make sure to provide all fields required by the schema unless otherwise specified.

//     {{ PrintMessages(messages) }}
//   "#
// }

// test generic_structured_output_call {
//   functions [GenericStructuredOutputCall]
//   args {
//     systemPrompt "Anwser in the voice of Pikachu."
//     userPrompt "What's the capital of France?"
//     messages [{
//         role "user"
//         message "hello world"
//       },
//       {
//         role "assistant",
//         message "The capital of France is Paris."
//       }
//     ]
//   }
// }