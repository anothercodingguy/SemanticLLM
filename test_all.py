import asyncio
from fastapi.testclient import TestClient
from main import app
from services.llm import evaluate_complexity
from services.metrics import record_metric, get_metrics_summary

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("✅ /health check passed")

def test_root_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "Semantic LLM Gateway" in response.text
    assert "Interactive Sandbox" in response.text
    assert "Impact Dashboard" in response.text
    print("✅ Dashboard HTML page test passed")

def test_metrics_api():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    expected_keys = {"total_saved", "total_spent", "total_requests", "cache_hits", "hit_rate", "avg_latency_hit", "avg_latency_miss", "queries"}
    assert expected_keys.issubset(data.keys())
    print("✅ /api/metrics endpoint test passed")

def test_complexity_evaluator():
    simple_prompt = "What is the capital of France?"
    complex_prompt = "Can you write an architecture analysis and debug code for this complex system?"
    
    assert evaluate_complexity(simple_prompt) == "llama-3.1-8b-instant"
    assert evaluate_complexity(complex_prompt) == "llama-3.3-70b-versatile"
    print("✅ Model complexity routing classification test passed")

def test_empty_prompt_validation():
    response = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "   "}]})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty prompt provided."
    print("✅ Empty prompt validation test passed")

def test_metrics_recording():
    async def _test():
        await record_metric(
            prompt="Unit test prompt",
            complexity="SIMPLE",
            model_routed="llama-3.1-8b-instant",
            is_cache_hit=False,
            latency_ms=150.0,
            prompt_tokens=15,
            completion_tokens=25
        )
        summary = await get_metrics_summary()
        assert summary["total_requests"] >= 1
        assert len(summary["queries"]) >= 1
        latest = summary["queries"][0]
        assert latest["prompt"] == "Unit test prompt"
        assert latest["complexity"] == "SIMPLE"

    asyncio.run(_test())
    print("✅ Metrics recording & summary calculation test passed")

if __name__ == "__main__":
    test_health_check()
    test_root_dashboard()
    test_metrics_api()
    test_complexity_evaluator()
    test_empty_prompt_validation()
    test_metrics_recording()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
