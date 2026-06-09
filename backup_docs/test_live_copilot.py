#!/usr/bin/env python3
"""
Live Interview Copilot Test - Real AI Responses
Tests with actual Gemini or free HuggingFace models
"""

import os
import sys
import time
from datetime import datetime

# Optimized system prompts
SYSTEM_PROMPT = """You are an INTERVIEW COPILOT - an ultra-fast expert assistant designed to help during live technical interviews.

⚡ CRITICAL RULES:
1. Respond INSTANTLY without overthinking
2. Be CONCISE - max 2-3 sentences for quick answers
3. For coding: Show only ESSENTIAL code (5-10 lines max)
4. NO EXPLANATIONS unless asked - just the answer
5. Use bullet points for multiple concepts

🎯 ANSWER FORMAT:
[Direct Answer - 1-2 sentences]
[Key Points - if needed]
[Optional: One concrete example]"""

QUICK_SYSTEM = """Answer in under 30 words with practical examples. Be specific, not generic. No fluff."""

CODING_SYSTEM = """Provide concise solution: Approach (1 sentence) → Code (5-10 lines) → Complexity."""

# Test questions
LIVE_TESTS = [
    {
        "name": "⚡ Quick Tech Q&A",
        "system": QUICK_SYSTEM,
        "question": "What is React's virtual DOM?",
    },
    {
        "name": "💻 Coding Problem",
        "system": CODING_SYSTEM,
        "question": "Reverse a linked list in O(1) space",
    },
    {
        "name": "🧠 Concept Explanation",
        "system": SYSTEM_PROMPT,
        "question": "Explain REST vs GraphQL in 2 sentences",
    },
]


def test_with_gemini():
    """Test with Google Gemini API (Free)"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("⚠️  No GOOGLE_API_KEY - trying fallback...")
            return False
        
        print("✅ Gemini API Key detected!")
        genai.configure(api_key=api_key)
        
        print("\n" + "="*80)
        print("🚀 LIVE INTERVIEW COPILOT TEST - GOOGLE GEMINI")
        print("="*80 + "\n")
        
        results = []
        
        for i, test in enumerate(LIVE_TESTS, 1):
            print(f"Test {i}: {test['name']}")
            print(f"Question: {test['question']}\n")
            
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=test['system'],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=300,
                )
            )
            
            start_time = time.time()
            response = model.generate_content(test['question'], stream=True)
            
            print("Response: ", end="", flush=True)
            full_response = ""
            
            for chunk in response:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    full_response += chunk.text
            
            elapsed = time.time() - start_time
            print(f"\n\n⏱️  Latency: {elapsed:.2f}s")
            
            token_count = len(full_response.split()) * 1.3
            results.append({
                "test": test['name'],
                "latency": elapsed,
                "tokens": token_count,
            })
            
            print("-" * 80 + "\n")
        
        # Summary
        print("\n" + "="*80)
        print("📊 LIVE TEST SUMMARY - GEMINI")
        print("="*80)
        
        avg_latency = sum(r['latency'] for r in results) / len(results)
        total_tokens = sum(r['tokens'] for r in results)
        
        print(f"\n✅ All {len(results)} tests completed!")
        print(f"⏱️  Average Latency: {avg_latency:.2f}s")
        print(f"📝 Total Tokens: {total_tokens:.0f}")
        print(f"💰 Estimated Cost/100 questions: $0.00 (Gemini Free Tier)\n")
        
        for result in results:
            print(f"  {result['test']}: {result['latency']:.2f}s (~{result['tokens']:.0f} tokens)")
        
        print("\n" + "="*80)
        if avg_latency < 2.0:
            print("🏆 Grade: A+ (Excellent) - Ultra-fast responses!")
        else:
            print("🏆 Grade: B+ (Good) - Solid performance!")
        print("="*80 + "\n")
        
        return True
        
    except ImportError:
        print("⚠️  google-generativeai not installed")
        return False
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


def test_with_free_inference_api():
    """Test with HuggingFace Inference API (Free but slower)"""
    try:
        import requests
        
        print("\n" + "="*80)
        print("🚀 LIVE INTERVIEW COPILOT TEST - HUGGINGFACE INFERENCE API")
        print("="*80 + "\n")
        
        # Using a public free model
        api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
        results = []
        
        for i, test in enumerate(LIVE_TESTS, 1):
            print(f"Test {i}: {test['name']}")
            print(f"Question: {test['question']}\n")
            
            prompt = f"{test['system']}\n\nQuestion: {test['question']}\n\nAnswer:"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 300,
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "return_full_text": False
                }
            }
            
            start_time = time.time()
            
            try:
                response = requests.post(api_url, json=payload, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                else:
                    generated_text = str(result)
                
                elapsed = time.time() - start_time
                
                print("Response: ", generated_text[:300])
                if len(generated_text) > 300:
                    print("...")
                
                print(f"\n⏱️  Latency: {elapsed:.2f}s")
                
                token_count = len(generated_text.split()) * 1.3
                results.append({
                    "test": test['name'],
                    "latency": elapsed,
                    "tokens": token_count,
                })
                
            except requests.exceptions.RequestException as e:
                print(f"API Error: {e}")
                results.append({
                    "test": test['name'],
                    "latency": 0,
                    "tokens": 0,
                })
            
            print("-" * 80 + "\n")
        
        # Summary
        print("\n" + "="*80)
        print("📊 LIVE TEST SUMMARY - HUGGINGFACE")
        print("="*80)
        
        valid_results = [r for r in results if r['latency'] > 0]
        if valid_results:
            avg_latency = sum(r['latency'] for r in valid_results) / len(valid_results)
            total_tokens = sum(r['tokens'] for r in valid_results)
            
            print(f"\n✅ {len(valid_results)}/{len(results)} tests completed!")
            print(f"⏱️  Average Latency: {avg_latency:.2f}s")
            print(f"📝 Total Tokens: {total_tokens:.0f}")
            print(f"💰 Cost: FREE (HuggingFace Free Tier)\n")
            
            for result in valid_results:
                print(f"  {result['test']}: {result['latency']:.2f}s (~{result['tokens']:.0f} tokens)")
        
        print("\n" + "="*80)
        print("="*80 + "\n")
        
        return len(valid_results) > 0
        
    except Exception as e:
        print(f"❌ HuggingFace test failed: {e}")
        return False


def main():
    """Run live tests"""
    print("\n🎯 Interview Copilot - Real-Time Performance Test\n")
    
    # Try Gemini first (fastest and free)
    gemini_success = test_with_gemini()
    
    if not gemini_success:
        print("Trying HuggingFace Inference API as fallback...\n")
        test_with_free_inference_api()
    
    print("\n✅ Live test suite completed!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
