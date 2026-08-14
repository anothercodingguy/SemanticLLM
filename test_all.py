import asyncio
from fastapi.testclient import TestClient
from main import app
from services.compression import compress_prompt, estimate_tokens, remove_duplicate_lines
from services.cache import init_cache, store_prompt, get_similar_prompt
from services.llm import evaluate_complexity
from services.metrics import record_metric, get_metrics_summary, calculate_direct_cost, calculate_actual_cost

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("✅ /health check passed")

def test_root_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "Semantic Gateway" in response.text
    assert "Interactive Sandbox" in response.text
    assert "Impact Dashboard" in response.text
    assert "Cut Your LLM API Costs by 65%" in response.text
    print("✅ Dashboard HTML page test passed")

def test_prompt_compression_service():
    # Test token estimation
    assert estimate_tokens("hello world") >= 2
    
    # Test duplicate line removal
    text_with_dupes = "Line 1: System info log\nLine 1: System info log\nLine 2: Another unique log entry"
    deduped, removed_count = remove_duplicate_lines(text_with_dupes)
    assert removed_count >= 1
    assert "Line 2: Another unique log entry" in deduped

    # Test full compress_prompt
    noisy_prompt = """
    2026-08-14 12:00:00 INFO: Initializing application server
    2026-08-14 12:00:00 INFO: Initializing application server
    2026-08-14 12:00:01 DEBUG: Database pool connected
    2026-08-14 12:00:01 DEBUG: Database pool connected
    
    Please explain the query execution plan.
    """
    comp = compress_prompt(noisy_prompt)
    assert comp["original_tokens"] > comp["optimized_tokens"]
    assert comp["tokens_saved"] > 0
    assert comp["compression_percent"] > 0
    assert len(comp["savings_notes"]) > 0
    print("✅ Prompt compression engine tests passed")

def test_complexity_evaluator():
    simple_prompt = "What is the capital of France?"
    complex_prompt = "Can you write an architecture analysis, benchmark algorithm, and debug code for this complex system?"
    
    model_s, tier_s, reason_s = evaluate_complexity(simple_prompt)
    assert model_s == "llama-3.1-8b-instant"
    assert tier_s == "SIMPLE"
    
    model_c, tier_c, reason_c = evaluate_complexity(complex_prompt)
    assert model_c == "llama-3.3-70b-versatile"
    assert tier_c == "COMPLEX"
    print("✅ Model complexity routing classification test passed")

def test_pricing_and_cost_calculations():
    # Direct 70B cost for 1000 prompt tokens + 100 completion tokens
    direct = calculate_direct_cost(1000, 100)
    assert direct > 0
    
    # Actual cost on 8B model
    actual_8b = calculate_actual_cost("llama-3.1-8b-instant", 1000, 100, is_cache_hit=False)
    assert actual_8b > 0
    assert direct > actual_8b # 8B should be substantially cheaper than 70B
    
    # Cached cost must be $0.00
    cached_cost = calculate_actual_cost("llama-3.3-70b-versatile", 1000, 100, is_cache_hit=True)
    assert cached_cost == 0.0
    print("✅ Cost calculation and pricing formulas passed")

def test_empty_prompt_validation():
    response = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "   "}]})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty prompt provided."
    print("✅ Empty prompt validation test passed")

def test_end_to_end_gateway_and_cache():
    async def _test():
        await init_cache()

        # Step 1: Initial query (Cache MISS)
        q1 = "What does fetch_user return when the database row is missing?"
        res1 = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": q1}]})
        assert res1.status_code == 200
        d1 = res1.json()
        assert d1["cache"]["hit"] is False
        assert "choices" in d1
        assert "compression" in d1
        assert "routing" in d1
        assert "cost" in d1
        assert res1.headers["X-Cache-Lookup"] == "MISS"

        # Step 2: Semantically equivalent query (Cache HIT)
        q2 = "What happens if fetch_user cannot find the database row?"
        res2 = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": q2}]})
        assert res2.status_code == 200
        d2 = res2.json()
        assert d2["cache"]["hit"] is True
        assert d2["cache"]["similarity"] >= 80.0
        assert res2.headers["X-Cache-Lookup"] == "HIT"
        assert d2["cost"]["actual_spent"] == 0.0

        # Step 3: Check Metrics Summary
        summary = await get_metrics_summary()
        assert summary["total_requests"] >= 2
        assert summary["cache_hits"] >= 1
        assert summary["total_saved"] > 0
        assert len(summary["queries"]) >= 2

    asyncio.run(_test())
    print("✅ End-to-end Gateway, Semantic Cache & Metrics flow passed")

if __name__ == "__main__":
    test_health_check()
    test_root_dashboard()
    test_prompt_compression_service()
    test_complexity_evaluator()
    test_pricing_and_cost_calculations()
    test_empty_prompt_validation()
    test_end_to_end_gateway_and_cache()
    print("\n🎉 ALL AUDIT & INTEGRATION TESTS PASSED SUCCESSFULLY!")
