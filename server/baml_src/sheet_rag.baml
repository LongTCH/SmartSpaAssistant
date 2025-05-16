class GetLocation {
  tool_name "get_location" @description("Use this tool to get the current location including city.")
}

class GetTimezone {
  tool_name "get_timezone" @description("Use this tool to find the current timezone of a specific city.")
  city string @description("The city for which to find the timezone.")
}

function ChooseTool(query: string) -> (GetLocation | GetTimezone)[] {
  client "openai/gpt-4o"
  prompt #"
    Given the user query, determine the primary intent and select the appropriate tool to call.

    {# special macro to add tool structures + descriptions here #}
    {{ ctx.output_format }} 

    {{ _.role('user') }}
    {{ query }}
    {{ _.role('assistant') }}
    Executed tool: [get_location]
    Result: ["Current location: Da Nang, Vietnam"]

    {{ CommonChainOfThoughts() }}
    {{ OutputStructureChainOfThought() }}
  "#
}
test TestName {
  functions [ChooseTool]
  args {
    query #"
      What's the weather like and current time here?
    "#
  }
}
