#!/usr/bin/env python3
"""
Integration test to verify connection to actual GPT-OSS:120b server
and test reasoning extraction with real responses.
"""

from llm_client import LLMClient
from config import get_llm_config
import sys

def test_server_connection():
    """Test basic connection to the server."""

    print("=" * 60)
    print("Testing Connection to GPT-OSS:120b Server")
    print("=" * 60)

    config = get_llm_config()
    print(f"\nServer: {config['base_url']}")
    print(f"Model: {config['model']}")
    print(f"Extract Final Answer: {config['extract_final_answer']}")
    print()

    try:
        client = LLMClient(**config)
        print("[OK] LLMClient initialized successfully")
        return client
    except Exception as e:
        print(f"[ERROR] Failed to initialize client: {e}")
        return None

def test_simple_prompt(client):
    """Test with a simple prompt to see response format."""

    print("\n" + "=" * 60)
    print("Test 1: Simple Prompt")
    print("=" * 60)

    try:
        print("\nSending prompt: 'What is 2+2?'")

        response = client.chat(
            messages=[
                {"role": "user", "content": "What is 2+2? Please answer concisely."}
            ]
        )

        content = response['message']['content']
        reasoning_extracted = response.get('reasoning_extracted', False)

        print(f"\n[OK] Received response")
        print(f"Reasoning Extracted: {reasoning_extracted}")
        print(f"Response Length: {len(content)} chars")
        print(f"\nResponse Content:")
        print("-" * 60)
        print(content[:500])  # Show first 500 chars
        if len(content) > 500:
            print(f"... ({len(content) - 500} more chars)")
        print("-" * 60)

        if reasoning_extracted:
            print("\n[SUCCESS] Reasoning was detected and extracted!")
            print("The framework correctly identified and extracted the final answer.")
        else:
            print("\n[INFO] No reasoning marker found in response")
            print("This could mean:")
            print("  1. Model didn't use reasoning format for this simple query")
            print("  2. Marker is different than expected")
            print("  3. Model is not a reasoning model")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to get response: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_complex_prompt(client):
    """Test with a more complex prompt that should trigger reasoning."""

    print("\n" + "=" * 60)
    print("Test 2: Complex Prompt (Should Trigger Reasoning)")
    print("=" * 60)

    try:
        print("\nSending complex reasoning prompt...")

        response = client.chat(
            messages=[
                {"role": "user", "content": """You are a Python expert. Create a simple function that checks if a number is prime.
Think through the algorithm step by step, then provide the final implementation."""}
            ]
        )

        content = response['message']['content']
        reasoning_extracted = response.get('reasoning_extracted', False)

        print(f"\n[OK] Received response")
        print(f"Reasoning Extracted: {reasoning_extracted}")
        print(f"Response Length: {len(content)} chars")
        print(f"\nResponse Content (first 300 chars):")
        print("-" * 60)
        print(content[:300])
        print("...")
        print("-" * 60)

        if reasoning_extracted:
            print("\n[SUCCESS] Reasoning extraction working correctly!")
            print("The model provided reasoning, and only the final answer was extracted.")
        else:
            print("\n[INFO] No reasoning extraction occurred")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to get response: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_raw_response(client):
    """Test with extraction disabled to see raw server response."""

    print("\n" + "=" * 60)
    print("Test 3: Raw Response (Extraction Disabled)")
    print("=" * 60)

    try:
        # Create new client with extraction disabled
        config = get_llm_config()
        config['extract_final_answer'] = False

        raw_client = LLMClient(**config)

        print("\nSending prompt with extraction DISABLED...")
        print("This will show the raw response including any reasoning markers.")

        response = raw_client.chat(
            messages=[
                {"role": "user", "content": "What is the capital of France?"}
            ]
        )

        content = response['message']['content']

        print(f"\n[OK] Received raw response")
        print(f"Response Length: {len(content)} chars")
        print(f"\nRaw Response:")
        print("-" * 60)
        print(content[:800])  # Show more of raw response
        if len(content) > 800:
            print(f"\n... ({len(content) - 800} more chars)")
        print("-" * 60)

        # Check if marker is present
        marker = "<|start|>assistant<|channel|>final<|message|>"
        if marker in content:
            print(f"\n[FOUND] Reasoning marker detected in raw response!")
            print(f"Marker position: {content.find(marker)}")
            print("\nThis confirms the server uses reasoning format.")
        else:
            print(f"\n[NOT FOUND] Reasoning marker not found in raw response")
            print("The server might:")
            print("  1. Not use reasoning format for simple queries")
            print("  2. Use a different marker format")
            print("  3. Only use reasoning for complex queries")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to get raw response: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""

    print("\n" + "=" * 60)
    print("GPT-OSS:120b Server Integration Test Suite")
    print("=" * 60)

    # Test 1: Connection
    client = test_server_connection()
    if not client:
        print("\n[FATAL] Could not connect to server")
        print("\nTroubleshooting:")
        print("  1. Check server is running: curl http://192.168.1.95:8000/v1/models")
        print("  2. Verify network connectivity")
        print("  3. Check firewall settings")
        print("  4. Verify config.py has correct URL")
        return 1

    # Test 2: Simple prompt
    if not test_simple_prompt(client):
        print("\n[WARNING] Simple prompt test failed")
        print("Continuing with other tests...")

    # Test 3: Complex prompt
    if not test_complex_prompt(client):
        print("\n[WARNING] Complex prompt test failed")

    # Test 4: Raw response
    if not test_raw_response(client):
        print("\n[WARNING] Raw response test failed")

    # Summary
    print("\n" + "=" * 60)
    print("Integration Test Summary")
    print("=" * 60)
    print("\nIf you saw responses above, the integration is working!")
    print("\nNext steps:")
    print("  1. Review the 'Reasoning Extracted' flags")
    print("  2. Check if the raw response contains the marker")
    print("  3. Verify final answers are clean and concise")
    print("\nIf reasoning extraction is working, you're ready to use the framework!")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
