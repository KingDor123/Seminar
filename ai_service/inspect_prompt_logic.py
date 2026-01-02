import os
import sys
import types

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

def _ensure_dummy_modules() -> None:
    try:
        import torch  # noqa: F401
    except Exception:
        torch_mod = types.ModuleType("torch")
        torch_mod.cuda = types.SimpleNamespace(is_available=lambda: False)

        def _no_grad():
            class _NoGrad:
                def __enter__(self):
                    return None

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _NoGrad()

        torch_mod.no_grad = _no_grad
        torch_nn_mod = types.ModuleType("torch.nn")
        torch_nn_functional_mod = types.ModuleType("torch.nn.functional")
        torch_nn_functional_mod.softmax = lambda *args, **kwargs: None

        torch_mod.nn = torch_nn_mod
        sys.modules["torch"] = torch_mod
        sys.modules["torch.nn"] = torch_nn_mod
        sys.modules["torch.nn.functional"] = torch_nn_functional_mod

    try:
        import transformers  # noqa: F401
    except Exception:
        transformers_mod = types.ModuleType("transformers")

        class _DummyModel:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return cls()

        transformers_mod.AutoTokenizer = _DummyModel
        transformers_mod.AutoModelForSequenceClassification = _DummyModel
        sys.modules["transformers"] = transformers_mod

    try:
        import openai  # noqa: F401
    except Exception:
        openai_mod = types.ModuleType("openai")

        class AsyncOpenAI:
            def __init__(self, *args, **kwargs):
                pass

        openai_mod.AsyncOpenAI = AsyncOpenAI
        sys.modules["openai"] = openai_mod

    if "app.core.config" not in sys.modules:
        app_mod = sys.modules.get("app") or types.ModuleType("app")
        core_mod = sys.modules.get("app.core") or types.ModuleType("app.core")
        config_mod = types.ModuleType("app.core.config")
        config_mod.settings = types.SimpleNamespace(
            OLLAMA_HOST="http://localhost:11434",
            OLLAMA_MODEL="aya:8b",
        )
        sys.modules["app"] = app_mod
        sys.modules["app.core"] = core_mod
        sys.modules["app.core.config"] = config_mod


_ensure_dummy_modules()

from pipeline import HybridPipeline as AIPipeline


def _build_pipeline() -> AIPipeline:
    return AIPipeline.__new__(AIPipeline)


def main() -> None:
    pipeline = _build_pipeline()
    sentiments = ["anger", "joy", "sadness", "neutral"]

    for sentiment in sentiments:
        instruction = pipeline._get_sentiment_instruction(sentiment, "normal")
        print(f"=== sentiment: {sentiment} ===")
        print(instruction)
        print()

    base_system_prompt = (
        "You are a calm support agent.\n"
        "Stay professional and concise."
    )
    messages = pipeline._construct_messages(
        base_system_prompt=base_system_prompt,
        user_text="I am upset about the delay.",
        history=[{"role": "user", "content": "Hello"}],
        sentiment="anger",
        difficulty="normal",
    )

    print("=== full system prompt (anger) ===")
    print(messages[0]["content"])


if __name__ == "__main__":
    main()
