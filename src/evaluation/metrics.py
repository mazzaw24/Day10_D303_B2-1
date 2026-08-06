from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
import sys
import time
import types
from typing import Any

from pydantic import BaseModel, Field

from core.config import Settings, normalized_provider
from core.utils import normalize_whitespace, read_json, sha256_file, write_json
from retrieval.index import LocalEmbeddingIndex
from retrieval.llm import build_llm
from retrieval.qa import answer_question


class JudgeVerdict(BaseModel):
    score: int = Field(ge=1, le=5)
    correct: bool
    reasoning: str


@dataclass(frozen=True)
class EvaluationBundle:
    summary: dict[str, Any]
    answers: list[dict[str, Any]]


def _token_f1(reference: str, prediction: str) -> tuple[float, float, float]:
    ref_tokens = normalize_whitespace(reference).lower().split()
    pred_tokens = normalize_whitespace(prediction).lower().split()
    if not ref_tokens or not pred_tokens:
        return 0.0, 0.0, 0.0
    ref_counts = {token: ref_tokens.count(token) for token in set(ref_tokens)}
    pred_counts = {token: pred_tokens.count(token) for token in set(pred_tokens)}
    overlap = sum(min(count, pred_counts.get(token, 0)) for token, count in ref_counts.items())
    if overlap == 0:
        return 0.0, 0.0, 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(ref_tokens)
    return precision, recall, 2 * precision * recall / (precision + recall)


def _judge_answer(settings: Settings, question: str, reference: str, prediction: str) -> JudgeVerdict:
    prompt = (
        "Evaluate the model answer against the reference answer.\n"
        f"Question: {question}\nReference answer: {reference}\nModel answer: {prediction}\n"
        "Return score 1-5, correct boolean, and short reasoning."
    )
    structured_llm = build_llm(settings=settings, temperature=0.0).with_structured_output(JudgeVerdict)
    verdict = structured_llm.invoke(prompt)
    return verdict if isinstance(verdict, JudgeVerdict) else JudgeVerdict.model_validate(verdict)


def _run_ragas(settings: Settings, answers: list[dict[str, Any]]) -> dict[str, Any]:
    from datasets import Dataset

    if "langchain_community.chat_models.vertexai" not in sys.modules:
        shim = types.ModuleType("langchain_community.chat_models.vertexai")
        shim.ChatVertexAI = type("ChatVertexAI", (), {})
        sys.modules["langchain_community.chat_models.vertexai"] = shim

    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
    from retrieval.embeddings import MiniLMEmbeddings

    dataset = Dataset.from_dict(
        {
            "question": [item["question"] for item in answers],
            "answer": [item["answer"] for item in answers],
            "ground_truth": [item["ground_truth"] for item in answers],
            "contexts": [item["retrieved_contexts"] for item in answers],
        }
    )
    result = evaluate(
        dataset,
        metrics=[answer_relevancy, context_precision, context_recall, faithfulness],
        llm=build_llm(settings=settings, temperature=0.0),
        embeddings=MiniLMEmbeddings(settings.embedding_model),
        raise_exceptions=True,
        show_progress=False,
    )
    res_dict = {}
    try:
        import pandas as pd
        df = result.to_pandas()
        
        # Calculate means for the final res_dict that goes into summary["ragas"]
        res_dict["answer_relevancy"] = float(df.get("answer_relevancy", 0.0).mean())
        res_dict["context_precision"] = float(df.get("context_precision", 0.0).mean())
        res_dict["context_recall"] = float(df.get("context_recall", 0.0).mean())
        res_dict["faithfulness"] = float(df.get("faithfulness", 0.0).mean())
        
        for i, row in df.iterrows():
            if i < len(answers):
                answers[i]["ragas_context_precision"] = float(row.get("context_precision", 0.0))
                answers[i]["ragas_context_recall"] = float(row.get("context_recall", 0.0))
                answers[i]["ragas_faithfulness"] = float(row.get("faithfulness", 0.0))
                answers[i]["ragas_answer_relevancy"] = float(row.get("answer_relevancy", 0.0))
                f_val = answers[i]["ragas_faithfulness"]
                answers[i]["hallucination_rate"] = 1.0 - f_val if not pd.isna(f_val) else 0.0
    except Exception as e:
        print(f"Failed to extract ragas results: {e}")
        # Fallback to empty if it fails completely
        res_dict = {
            "answer_relevancy": 0.0,
            "context_precision": 0.0,
            "context_recall": 0.0,
            "faithfulness": 0.0
        }

    return res_dict

def evaluate_pipeline(
    settings: Settings,
    index: LocalEmbeddingIndex,
    test_set_path,
    metrics_output_path,
    answers_output_path,
) -> EvaluationBundle:
    test_set = read_json(test_set_path)
    if not isinstance(test_set, list) or not test_set:
        raise ValueError("Evaluation test set must be a non-empty JSON list.")
    answers: list[dict[str, Any]] = []
    for item in test_set:
        start_t = time.perf_counter()
        result = answer_question(item["question"], settings=settings, index=index)
        latency = time.perf_counter() - start_t

        judge = _judge_answer(settings, item["question"], item["ground_truth"], result.answer)
        retrieval_hit = any(doc_id in item["ground_truth_doc_ids"] for doc_id in result.retrieved_doc_ids)
        hit_at_3 = any(doc_id in item["ground_truth_doc_ids"] for doc_id in result.retrieved_doc_ids[:3])
        hit_at_5 = any(doc_id in item["ground_truth_doc_ids"] for doc_id in result.retrieved_doc_ids[:5])
        token_p, token_r, token_f1 = _token_f1(item["ground_truth"], result.answer)

        answers.append(
            {
                "id": item["id"],
                "question_type": item["question_type"],
                "question": item["question"],
                "ground_truth": item["ground_truth"],
                "ground_truth_doc_ids": item["ground_truth_doc_ids"],
                "answer": result.answer,
                "retrieved_doc_ids": result.retrieved_doc_ids,
                "retrieved_contexts": result.retrieved_contexts,
                "retrieval_hit": retrieval_hit,
                "hit_at_3": hit_at_3,
                "hit_at_5": hit_at_5,
                "latency_seconds": latency,
                "token_precision": token_p,
                "token_recall": token_r,
                "token_f1": token_f1,
                "judge": judge.model_dump(),
            }
        )
        write_json(answers_output_path, answers)

    summary = {
        "samples": len(answers),
        "retrieval_hit_rate": mean(1.0 if item.get("retrieval_hit") else 0.0 for item in answers),
        "hit_at_3": mean(1.0 if item.get("hit_at_3") else 0.0 for item in answers),
        "hit_at_5": mean(1.0 if item.get("hit_at_5") else 0.0 for item in answers),
        "mean_token_precision": mean(item.get("token_precision", 0.0) for item in answers),
        "mean_token_recall": mean(item.get("token_recall", 0.0) for item in answers),
        "mean_token_f1": mean(item.get("token_f1", 0.0) for item in answers),
        "judge_accuracy": mean(1.0 if item["judge"]["correct"] else 0.0 for item in answers),
        "mean_judge_score": mean(item["judge"]["score"] for item in answers),
        "mean_latency_seconds": mean(item.get("latency_seconds", 0.0) for item in answers),
        "test_set_sha256": sha256_file(test_set_path),
        "index_backend": index.embedding_backend,
        "embedding_backend": index.embedding_model.backend,
        "answer_backend": "configured_llm",
        "judge_backend": "configured_llm",
        "ragas_backend": "configured_llm",
        "llm_provider": normalized_provider(settings),
        "llm_model": settings.model_name,
    }
    summary["ragas"] = _run_ragas(settings, answers)
    import pandas as pd
    def _safe_float(v): return float(v) if not pd.isna(v) else 0.0
    summary["mean_hallucination_rate"] = mean(_safe_float(item.get("hallucination_rate", 0.0)) for item in answers) if answers else 0.0
    summary["mean_context_precision"] = mean(_safe_float(item.get("ragas_context_precision", 0.0)) for item in answers) if answers else 0.0
    summary["mean_context_recall"] = mean(_safe_float(item.get("ragas_context_recall", 0.0)) for item in answers) if answers else 0.0
    
    write_json(metrics_output_path, summary)
    write_json(answers_output_path, answers)
    return EvaluationBundle(summary=summary, answers=answers)
