import asyncio
from fastapi.testclient import TestClient
from main import app
from services.compression import (
    compress_prompt,
    estimate_tokens,
    remove_duplicate_lines,
    compress_context,
    compress_for_turn,
    sustainability_from_tokens_saved
)
from services.cache import init_cache, store_prompt, get_similar_prompt
from services.llm import evaluate_complexity
from services.metrics import record_metric, get_metrics_summary, calculate_direct_cost, calculate_actual_cost

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✅ /health check passed")

def test_root_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "Semantic Gateway" in response.text
    assert "SuperCompress" in response.text
    assert "Interactive Sandbox" in response.text
    assert "Benchmarks" in response.text
    assert "Coding Agents" in response.text
    print("✅ Dashboard HTML page test passed")

def test_supercompress_engine():
    # 1. Test token estimation
    assert estimate_tokens("hello world") >= 2
    
    # 2. Test duplicate line removal
    text_with_dupes = "Line 1: System info log\nLine 1: System info log\nLine 2: Another unique log entry"
    deduped, removed_count = remove_duplicate_lines(text_with_dupes)
    assert removed_count >= 1
    assert "Line 2: Another unique log entry" in deduped

    # 3. Test SuperCompress query-aware compiler mode
    long_dump = """
    ## Customer Support Ticket History
    User ID: usr_9281742 | Plan: Enterprise Tier | Region: US-East
    [2026-08-16 09:12:00 INFO] Ticket #8841 created: Billing mismatch on invoice INV-2026-08.
    [2026-08-16 09:12:00 INFO] Ticket #8841 created: Billing mismatch on invoice INV-2026-08.
    [2026-08-16 09:15:22 DEBUG] Automated webhook dispatched to Stripe Billing API.
    [2026-08-16 09:15:22 DEBUG] Automated webhook dispatched to Stripe Billing API.

    ### Account Overview
    Account status is active. Payment method ending in 4242 failed due to bank verification hold.
    Refund request of $420.00 approved by billing supervisor on 2026-08-15.

    ### Unrelated Feature Requests
    User requested dark mode for the analytics dashboard and support for export to parquet format.
    """
    query = "What was the supervisor decision regarding the refund request?"
    
    comp_res = compress_context(long_dump, query=query, mode="compiler")
    assert comp_res["original_tokens"] > comp_res["kept_tokens"]
    assert comp_res["tokens_saved"] > 0
    assert comp_res["tokens_saved_pct"] > 0
    assert comp_res["important_kept_pct"] >= 0.95
    assert comp_res["compression_risk"] in ("low", "medium")
    assert len(comp_res["kept_blocks"]) >= 1
    assert "Refund request of $420.00 approved" in comp_res["compressed_text"]

    # 4. Test fixed-ratio mode
    fixed_res = compress_context(long_dump, query=query, mode="fixed", budget_ratio=0.35)
    assert fixed_res["kept_tokens"] <= int(fixed_res["original_tokens"] * 0.70)

    # 5. Test sustainability calculation
    sustain = sustainability_from_tokens_saved(1000)
    assert sustain["co2_kg_avoided"] > 0
    assert sustain["watt_hours_saved"] > 0
    assert sustain["gpu_seconds_avoided"] > 0
    print("✅ SuperCompress neural context compression engine tests passed")

def test_supercompress_http_endpoints():
    # 1. Test POST /v1/compress (JSON)
    req_payload = {
        "context": "System Context:\n[2026-08-16 INFO] Log line 1\n[2026-08-16 INFO] Log line 1\n\n### Database Status\nPostgres connection established.",
        "query": "What is the database status?",
        "mode": "compiler"
    }
    res = client.post("/v1/compress", json=req_payload)
    assert res.status_code == 200
    data = res.json()
    assert "compressed_text" in data
    assert data["original_tokens"] > 0
    assert data["kept_tokens"] > 0
    assert "sustainability" in data
    assert res.headers["X-Compression-Mode"] == "compiler"

    # 2. Test POST /compress alias
    res_alias = client.post("/compress", json=req_payload)
    assert res_alias.status_code == 200

    # 3. Test Form-encoded request
    res_form = client.post("/v1/compress", data={"context": "Sample context with logs\nSample context with logs", "query": "test query"})
    assert res_form.status_code == 200
    assert res_form.json()["original_tokens"] > 0

    # 4. Test missing context validation (400)
    res_err = client.post("/v1/compress", json={"context": ""})
    assert res_err.status_code == 400
    print("✅ SuperCompress HTTP API (POST /v1/compress & POST /compress) passed")

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
    direct = calculate_direct_cost(1000, 100)
    assert direct > 0
    
    actual_8b = calculate_actual_cost("llama-3.1-8b-instant", 1000, 100, is_cache_hit=False)
    assert actual_8b > 0
    assert direct > actual_8b
    
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
    test_supercompress_engine()
    test_supercompress_http_endpoints()
    test_complexity_evaluator()
    test_pricing_and_cost_calculations()
    test_empty_prompt_validation()
    test_end_to_end_gateway_and_cache()
    print("\n🎉 ALL SUPERCOMPRESS & SEMANTIC GATEWAY AUDIT TESTS PASSED SUCCESSFULLY!")
