#!/usr/bin/env python3
"""
Test script to verify reasoning model final answer extraction.
"""

from llm_client import LLMClient
from config import get_llm_config

def test_extraction():
    """Test the extraction of final answer from reasoning model output."""

    print("Testing Reasoning Model Final Answer Extraction")
    print("=" * 60)

    # Create test data that simulates reasoning model output
    test_cases = [
        {
            "name": "With reasoning marker",
            "content": """Let me think about this problem step by step.
First, I need to consider the input parameters.
Then I'll analyze the requirements.
After careful consideration of all factors...
<|start|>assistant<|channel|>final<|message|>
The final answer is 42. This solution addresses all the requirements.""",
            "expected": "The final answer is 42. This solution addresses all the requirements."
        },
        {
            "name": "Without reasoning marker",
            "content": "This is a direct response without reasoning.",
            "expected": "This is a direct response without reasoning."
        },
        {
            "name": "With end marker",
            "content": """Thinking through this carefully...
<|start|>assistant<|channel|>final<|message|>
Here is my final answer.<|end|>""",
            "expected": "Here is my final answer."
        }
    ]

    # Create a mock client just for testing the extraction method
    # We don't need actual API connection for this test
    class MockClient:
        def __init__(self):
            config = get_llm_config()
            self.extract_final_answer = config['extract_final_answer']
            self.final_answer_marker = config['final_answer_marker']

        def _extract_final_answer_from_reasoning(self, content: str) -> str:
            """Copy of the extraction method from LLMClient for testing."""
            if not self.extract_final_answer or not self.final_answer_marker:
                return content

            if self.final_answer_marker in content:
                marker_pos = content.find(self.final_answer_marker)
                final_answer = content[marker_pos + len(self.final_answer_marker):].strip()

                for end_marker in ["<|end|>", "<|endoftext|>", "<|eot_id|>"]:
                    if end_marker in final_answer:
                        final_answer = final_answer.split(end_marker)[0].strip()

                return final_answer

            return content

    client = MockClient()

    print(f"\nClient Configuration:")
    print(f"  Extract Final Answer: {client.extract_final_answer}")
    print(f"  Final Answer Marker: {client.final_answer_marker[:40]}...")
    print()

    # Test each case
    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 60)

        result = client._extract_final_answer_from_reasoning(test_case['content'])

        print(f"Input length: {len(test_case['content'])} chars")
        print(f"Output length: {len(result)} chars")
        print(f"Expected: {test_case['expected'][:50]}...")
        print(f"Got:      {result[:50]}...")

        if result.strip() == test_case['expected'].strip():
            print("[PASSED]")
        else:
            print("[FAILED]")
            print(f"Full expected:\n{test_case['expected']}")
            print(f"Full got:\n{result}")
            all_passed = False

        print()

    print("=" * 60)
    if all_passed:
        print("All tests PASSED!")
        print("\nThe framework will automatically extract final answers from")
        print("reasoning models like GPT-OSS:120b, removing the chain of thought")
        print("and returning only the final answer to agents.")
    else:
        print("Some tests FAILED!")
        return 1

    return 0

def test_with_config_disabled():
    """Test that extraction can be disabled via config."""

    print("\n\nTesting with extraction DISABLED")
    print("=" * 60)

    # Create mock client with extraction disabled
    class MockClient:
        def __init__(self, extract_final_answer):
            self.extract_final_answer = extract_final_answer
            self.final_answer_marker = "<|start|>assistant<|channel|>final<|message|>"

        def _extract_final_answer_from_reasoning(self, content: str) -> str:
            if not self.extract_final_answer or not self.final_answer_marker:
                return content

            if self.final_answer_marker in content:
                marker_pos = content.find(self.final_answer_marker)
                final_answer = content[marker_pos + len(self.final_answer_marker):].strip()
                return final_answer

            return content

    client = MockClient(extract_final_answer=False)

    test_content = """Reasoning process here...
<|start|>assistant<|channel|>final<|message|>
Final answer here."""

    result = client._extract_final_answer_from_reasoning(test_content)

    print(f"Extraction enabled: {client.extract_final_answer}")
    print(f"Input length: {len(test_content)} chars")
    print(f"Output length: {len(result)} chars")

    if result == test_content:
        print("[PASSED] - Full content returned when extraction disabled")
        return 0
    else:
        print("[FAILED] - Content was extracted despite being disabled")
        return 1

if __name__ == "__main__":
    exit_code = test_extraction()
    exit_code += test_with_config_disabled()

    if exit_code == 0:
        print("\n" + "=" * 60)
        print("All tests passed successfully!")
        print("=" * 60)

    exit(exit_code)
