
from evaluation.run_eval import ThinkStrippingChatGroq
from config.settings import settings

llm = ThinkStrippingChatGroq(
    model="openai/gpt-oss-120b",
    api_key=settings.groq_api_key,
    temperature=0,
    max_tokens=1500,
)

result = llm.invoke("Say hello in one word.")

print(repr(result.content))
