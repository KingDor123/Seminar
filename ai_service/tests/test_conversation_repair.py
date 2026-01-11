import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.engine.agents import RolePlayAgent
from app.engine.schema import ScenarioState, EvaluationCriteria, AgentOutput

# Mock State
MOCK_STATE = ScenarioState(
    id="ask_amount",
    description="Ask for loan amount",
    actor_instruction="Ask how much money needed.",
    evaluation=EvaluationCriteria(
        criteria=["User gives number"],
        pass_condition="User provides amount.",
        failure_feedback_guidance="Ask for a number."
    )
)

MOCK_PERSONA = "You are a helpful bank clerk."

@pytest.mark.asyncio
async def test_llm_prompt_structure():
    """
    Test that _build_llm_prompt correctly includes context and repair policies.
    """
    context = {
        "decision": {"label": "UNCLEAR"},
        "signals": {"user_confused": True},
        "slots": {"filled": {"purpose": "car"}, "missing": ["amount"]}
    }
    
    prompt = RolePlayAgent._build_llm_prompt(MOCK_PERSONA, MOCK_STATE, context)
    
    assert "--- REPAIR POLICY (User is Unclear/Confused) ---" in prompt
    assert "Ask a clarifying question specifically about the missing info" in prompt
    assert "\"known_info\": {\n    \"purpose\": \"car\"\n  }" in prompt
    assert "\"missing_info\": [\n    \"amount\"\n  ]" in prompt

@pytest.mark.asyncio
async def test_frustration_policy():
    """
    Test that frustration triggers the specific repair policy.
    """
    context = {
        "decision": {"label": "GATE_PASSED"}, # Even if passed, frustration might be present
        "signals": {"user_frustrated": True},
        "slots": {"filled": {"amount": "20000"}, "missing": []}
    }
    
    prompt = RolePlayAgent._build_llm_prompt(MOCK_PERSONA, MOCK_STATE, context)
    
    assert "--- REPAIR POLICY (Frustration Detected) ---" in prompt
    assert "Acknowledge the user's frustration" in prompt
    assert "Do NOT re-ask for: amount" in prompt

@pytest.mark.asyncio
async def test_inappropriate_policy():
    """
    Test handling of inappropriate context.
    """
    context = {
        "decision": {"label": "INAPPROPRIATE_FOR_CONTEXT"},
        "signals": {},
        "slots": {}
    }
    
    prompt = RolePlayAgent._build_llm_prompt(MOCK_PERSONA, MOCK_STATE, context)
    
    assert "--- REPAIR POLICY (Inappropriate Behavior) ---" in prompt
    assert "Politely but firmly address the tone/content" in prompt

@patch("app.engine.agents.llm_client")
@pytest.mark.asyncio
async def test_generate_response_calls_llm(mock_llm_client):
    """
    Test that generate_response calls the LLM with the built prompt.
    """
    # Create a proper async generator for the mock
    async def mock_generator(*args, **kwargs):
        yield "Hello"
        
    mock_llm_client.generate_stream.side_effect = mock_generator
    
    history = [{"role": "assistant", "content": "Hi"}]
    context = {"decision": {"label": "GATE_PASSED"}}
    
    gen = RolePlayAgent.generate_response(
        user_text="User Input",
        base_persona=MOCK_PERSONA,
        state=MOCK_STATE,
        history=history,
        llm_context=context
    )
    
    # Consume generator
    async for _ in gen:
        pass
        
    mock_llm_client.generate_stream.assert_called_once()
    call_args = mock_llm_client.generate_stream.call_args[0][0]
    
    # Check if system prompt is in messages
    assert call_args[0]["role"] == "system"
    assert "--- CONTEXT ---" in call_args[0]["content"]
