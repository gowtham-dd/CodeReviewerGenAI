import asyncio
import json
from agents.correctness import CorrectnessAgent
from agents.complexity import ComplexityAgent
from config import Config

# Sample code to test
SAMPLE_CODE = """
def calculate_average(numbers):
    '''Calculate the average of a list of numbers'''
    if not numbers:
        return 0
    
    total = 0
    for num in numbers:
        total += num
    
    return total / len(numbers)

def find_max(numbers):
    '''Find the maximum number in a list'''
    if not numbers:
        return None
    
    max_num = numbers[0]
    for num in numbers:
        if num > max_num:
            max_num = num
    
    return max_num
"""

async def test_agents():
    print("=" * 60)
    print("🔍 TESTING AGENT 1: CORRECTNESS")
    print("=" * 60)
    
    # Initialize agent
    correctness = CorrectnessAgent(Config.GROQ_API_KEY, Config.GROQ_MODEL)
    
    # Simple test cases
    test_cases = [
        {
            "input": [1, 2, 3, 4, 5],
            "expected": 3.0,
            "description": "Average of positive numbers"
        },
        {
            "input": [],
            "expected": 0,
            "description": "Empty list"
        },
        {
            "input": [10],
            "expected": 10,
            "description": "Single number"
        }
    ]
    
    try:
        result = await correctness.review(SAMPLE_CODE, "python", test_cases)
        
        print(f"✅ Tests Passed: {result.get('tests_passed', 0)}/{result.get('total_tests', 0)}")
        print("\n📊 Test Results:")
        for test in result.get('test_results', []):
            status = "✅" if test.get('passed') else "❌"
            print(f"  {status} {test.get('name', 'Test')}")
            if not test.get('passed'):
                print(f"     Error: {test.get('error', 'Unknown')}")
        
        print(f"\n📝 Summary: {result.get('summary', 'No summary')}")
        
    except Exception as e:
        print(f"❌ Error in correctness agent: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 TESTING AGENT 2: COMPLEXITY")
    print("=" * 60)
    
    # Initialize agent
    complexity = ComplexityAgent(Config.GROQ_API_KEY, Config.GROQ_MODEL)
    
    try:
        result = await complexity.analyze(SAMPLE_CODE, "python")
        
        print(f"\n⏱️  Time Complexity: {result.get('time_complexity', {}).get('big_o', 'Unknown')}")
        print(f"   {result.get('time_complexity', {}).get('explanation', '')}")
        
        print(f"\n💾 Space Complexity: {result.get('space_complexity', {}).get('big_o', 'Unknown')}")
        print(f"   {result.get('space_complexity', {}).get('explanation', '')}")
        
        print(f"\n🔥 Hotspots:")
        for hotspot in result.get('hotspots', []):
            print(f"   • Line {hotspot.get('line', '?')}: {hotspot.get('function', 'Unknown')} (complexity: {hotspot.get('complexity', '?')})")
        
        print(f"\n💡 Suggestions:")
        for suggestion in result.get('suggestions', []):
            print(f"   • {suggestion}")
            
    except Exception as e:
        print(f"❌ Error in complexity agent: {e}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_agents())