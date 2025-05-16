// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

client<llm> Gemini2Flash {
  provider google-ai
  options {
    model "gemini-2.0-flash"
    api_key env.GEMINI_API_KEY
    generationConfig {
      temperature 0
    }
  }
}

client<llm> Gemini2FlashLite {
  provider google-ai
  options {
    model "gemini-2.0-flash-lite"
    api_key env.GEMINI_API_KEY
    generationConfig {
      temperature 0
    }
  }
}

client<llm> Gemma3 {
  provider openai-generic
  retry_policy Exponential
  options {
    model "google/gemma-3-27b-it:free"
    api_key env.OPENROUTER_API_KEY
    base_url https://openrouter.ai/api/v1
    temperature 0
  }
}

client<llm> GPT4oMini {
  provider openai
  retry_policy Exponential
  options {
    model "gpt-4o-mini"
    api_key env.OPENAI_API_KEY
    temperature 0
  }
}

client<llm> DeepSeek {
  provider openai-generic
  retry_policy Exponential
  options {
    model "deepseek-chat"
    api_key env.DEEPSEEK_API_KEY
    base_url https://api.deepseek.com
    temperature 0 
  }
}

client<llm> QwQ3 {
  provider openai-generic
  retry_policy Exponential
  options {
    model "qwen/qwen3-30b-a3b:free"
    api_key env.OPENROUTER_API_KEY
    base_url https://openrouter.ai/api/v1
    temperature 0
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/round-robin
client<llm> CustomFast {
  provider round-robin
  options {
    // This will alternate between the two clients
    strategy [Gemini2Flash, GPT4oMini]
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/fallback
client<llm> OpenaiFallback {
  provider fallback
  options {
    // This will try the clients in order until one succeeds
    strategy [Gemini2FlashLite,GPT4oMini]
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/retry
retry_policy Constant {
  max_retries 3
  // Strategy is optional
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 2
  // Strategy is optional
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}