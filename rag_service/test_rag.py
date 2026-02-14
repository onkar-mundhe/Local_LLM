"""
RAG Service Test Script
Author: Kanwarraj Singh

Simple tests for the RAG service API.
Run with: python test_rag.py
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    """Test health endpoint"""
    print_header("TEST 1: Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    
    print(f"Status: {data['status']}")
    print(f"Documents: {data['document_count']}")
    print(f"Chunks: {data['chunk_count']}")
    print(f"Embedding Model: {data['embedding_model']}")
    print(f"LLM Server: {data['llama_server_url']}")
    
    return response.status_code == 200

def test_list_documents():
    """Test document listing"""
    print_header("TEST 2: List Documents")
    
    response = requests.get(f"{BASE_URL}/documents")
    data = response.json()
    
    print(f"Total documents: {data['total']}")
    for doc in data['documents']:
        print(f"  - [{doc['id']}] {doc['filename']} ({doc['chunk_count']} chunks)")
    
    return response.status_code == 200

def test_search(query: str):
    """Test search functionality"""
    print_header(f"TEST 3: Search - '{query}'")
    
    response = requests.post(
        f"{BASE_URL}/search",
        json={"query": query, "k": 3}
    )
    data = response.json()
    
    print(f"Query: {data['query']}")
    print(f"Results found: {data['total']}")
    
    for i, result in enumerate(data['results'], 1):
        print(f"\n  Result {i} (score: {result['score']:.3f}):")
        print(f"  Source: {result['source']}, Page: {result['page']}")
        # Show first 200 chars of content
        content_preview = result['content'][:200].replace('\n', ' ')
        print(f"  Content: {content_preview}...")
    
    if data.get('context'):
        print(f"\n  [Context formatted for LLM - {len(data['context'])} chars]")
    
    return response.status_code == 200

def test_chat_with_rag(question: str):
    """Test RAG-enhanced chat"""
    print_header(f"TEST 4: RAG Chat - '{question}'")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": question}
            ],
            "use_rag": True,
            "rag_k": 5,
            "temperature": 0.3,
            "max_tokens": 500
        }
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    
    print(f"RAG Context Used: {data.get('rag_context_used', False)}")
    if data.get('rag_sources'):
        print(f"Sources: {data['rag_sources']}")
    
    # Get assistant response
    if data.get('choices'):
        message = data['choices'][0]['message']['content']
        print(f"\nAssistant Response:")
        print("-" * 40)
        print(message)
    
    return response.status_code == 200

def test_chat_without_rag(question: str):
    """Test chat without RAG (direct to LLM)"""
    print_header(f"TEST 5: Direct Chat (no RAG) - '{question}'")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": question}
            ],
            "use_rag": False,
            "temperature": 0.3,
            "max_tokens": 200
        }
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    
    print(f"RAG Context Used: {data.get('rag_context_used', False)}")
    
    if data.get('choices'):
        message = data['choices'][0]['message']['content']
        print(f"\nAssistant Response:")
        print("-" * 40)
        print(message)
    
    return response.status_code == 200


def main():
    print("\n" + "=" * 60)
    print("       RAG SERVICE TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health
    results.append(("Health Check", test_health()))
    
    # Test 2: List documents
    results.append(("List Documents", test_list_documents()))
    
    # Test 3: Search - customize this query based on your document
    results.append(("Search", test_search("release notes")))
    
    # Test 4: RAG Chat - customize based on your document
    results.append(("RAG Chat", test_chat_with_rag(
        "What are the main features or changes in this release?"
    )))
    
    # Test 5: Direct chat without RAG
    results.append(("Direct Chat", test_chat_without_rag(
        "What is 2 + 2?"
    )))
    
    # Summary
    print_header("TEST SUMMARY")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
    
    passed_count = sum(1 for _, p in results if p)
    print(f"\n  {passed_count}/{len(results)} tests passed")


if __name__ == "__main__":
    main()
