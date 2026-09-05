import json
import re
from datasets import Dataset
from ragas import evaluate, RunConfig
from ragas.metrics import faithfulness, context_precision, AnswerRelevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq

from app.pipeline import answer_question
from rag.retriever import retrieve
from rag.embedder import get_embedding_model
from config.settings import settings


class ThinkStrippingChatGroq(ChatGroq):
    """Groq's qwen3.6 model emits <think>...</think> reasoning inline in
    content instead of a separate reasoning field. Strip it so downstream
    consumers (like RAGAS) only see the actual answer."""
    def _generate(self, *args, **kwargs):
        result = super()._generate(*args, **kwargs)
        for generation in result.generations:
            if isinstance(generation.message, AIMessage) and generation.message.content:
                cleaned = re.sub(r"<think>.*?</think>", "", generation.message.content, flags=re.DOTALL).strip()
                generation.message.content = cleaned
        return result


with open("evaluation/eval_dataset.json") as f:
    eval_items = json.load(f)

records = []
for item in eval_items:
    docs = retrieve(item["question"], k=4)
    result = answer_question(item["question"], session_id="eval-run")
    records.append({
        "question": item["question"],
        "answer": result["answer_markdown"],
        "contexts": [d.page_content for d in docs],
        "ground_truth": item["ground_truth"],
    })

dataset = Dataset.from_list(records)


judge_llm = LangchainLLMWrapper(
    ChatGroq(
        model=settings.groq_model,  # same model your app uses (openai/gpt-oss-20b) — this is what actually produced a clean, complete run
        api_key=settings.groq_api_key,
        temperature=0,
        max_tokens=4096,
    )
)


judge_embeddings = LangchainEmbeddingsWrapper(get_embedding_model())

# strictness=1 avoids Groq's n>1 limitation (default strictness=3 requests
# 3 completions in one call, which Groq's API rejects)
answer_relevancy_metric = AnswerRelevancy(strictness=1)

# more generous timeout/retries since Groq free-tier rate limits can cause
# transient slowness under RAGAS's concurrent evaluation calls
run_config = RunConfig(timeout=120, max_retries=3, max_workers=1)

scores = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy_metric, context_precision],
    llm=judge_llm,
    embeddings=judge_embeddings,
    run_config=run_config,
)
print(scores)

with open("evaluation/results.json", "w") as f:
    json.dump(scores.to_pandas().to_dict(orient="records"), f, indent=2)