#!/usr/bin/env python3
"""
Test script to validate data coverage question capabilities.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the elevator_ai_agent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'elevator_ai_agent'))

def test_data_coverage_questions():
    """Test the new data coverage question capabilities."""
    
    try:
        from agents.orchestrator import query_orchestrator
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv('elevator_ai_agent/.env')
        
        print("🧪 Testing Data Coverage Question Capabilities")
        print("=" * 60)
        
        # Test installation
        installation_id = "4995d395-9b4b-4234-a8aa-9938ef5620c6"
        
        # Test date range (last 3 days for faster testing)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=3)
        
        print(f"Installation: {installation_id}")
        print(f"Date Range: {start_date} to {end_date}")
        print("-" * 60)
        
        # Test questions that should route to data coverage tool
        test_questions = [
            {
                "question": "What's the data coverage for this installation?",
                "expected_tool": "data_coverage_analysis",
                "description": "Basic coverage question"
            },
            {
                "question": "Which elevators are reporting data?",
                "expected_tool": "data_coverage_analysis", 
                "description": "Machine reporting status"
            },
            {
                "question": "Are there any data gaps?",
                "expected_tool": "data_coverage_analysis",
                "description": "Data gaps inquiry"
            },
            {
                "question": "How much data is missing?",
                "expected_tool": "data_coverage_analysis",
                "description": "Missing data quantity"
            },
            {
                "question": "What's the data quality like?",
                "expected_tool": "data_coverage_analysis",
                "description": "Data quality assessment"
            },
            {
                "question": "How many events were recorded?",
                "expected_tool": "data_coverage_analysis",
                "description": "Event count question"
            }
        ]
        
        # Test questions that should still route to other tools
        control_questions = [
            {
                "question": "What was the uptime yesterday?",
                "expected_tool": "uptime_analysis",
                "description": "Uptime question (control)"
            },
            {
                "question": "How many door cycles occurred?",
                "expected_tool": "door_cycle_analysis",
                "description": "Door cycles question (control)"
            }
        ]
        
        all_questions = test_questions + control_questions
        
        print(f"\n🎯 Testing {len(all_questions)} questions:\n")
        
        results = []
        
        for i, test in enumerate(all_questions, 1):
            question = test["question"]
            expected_tool = test["expected_tool"]
            description = test["description"]
            
            print(f"{i}. {description}")
            print(f"   Question: '{question}'")
            print(f"   Expected tool: {expected_tool}")
            
            try:
                # Test tool selection logic directly
                orchestrator = query_orchestrator
                selected_tool = orchestrator._select_appropriate_tool(question.lower())
                
                if selected_tool == expected_tool:
                    print(f"   ✅ Correct tool selected: {selected_tool}")
                    status = "✅ PASS"
                else:
                    print(f"   ❌ Wrong tool selected: {selected_tool} (expected {expected_tool})")
                    status = "❌ FAIL"
                
                results.append({
                    "question": question,
                    "expected": expected_tool,
                    "actual": selected_tool,
                    "status": status,
                    "description": description
                })
                
            except Exception as e:
                print(f"   ❌ Error testing question: {e}")
                results.append({
                    "question": question,
                    "expected": expected_tool,
                    "actual": "ERROR",
                    "status": "❌ ERROR",
                    "description": description
                })
            
            print()
        
        # Summary
        print("=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results if "PASS" in r["status"])
        failed = sum(1 for r in results if "FAIL" in r["status"])
        errors = sum(1 for r in results if "ERROR" in r["status"])
        
        print(f"Total Tests: {len(results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"💥 Errors: {errors}")
        print(f"Success Rate: {passed/len(results)*100:.1f}%")
        
        if failed > 0 or errors > 0:
            print(f"\n🔍 FAILED/ERROR TESTS:")
            for result in results:
                if "FAIL" in result["status"] or "ERROR" in result["status"]:
                    print(f"  • {result['description']}")
                    print(f"    Question: '{result['question']}'")
                    print(f"    Expected: {result['expected']}, Got: {result['actual']}")
        
        print(f"\n🎯 DATA COVERAGE CAPABILITIES:")
        coverage_tests = [r for r in results if r["expected"] == "data_coverage_analysis"]
        coverage_passed = sum(1 for r in coverage_tests if "PASS" in r["status"])
        
        print(f"Data Coverage Questions: {coverage_passed}/{len(coverage_tests)} working correctly")
        
        if coverage_passed == len(coverage_tests):
            print("🚀 All data coverage questions are correctly routed!")
            print("\n💡 Try these example questions in the UI:")
            for test in test_questions[:3]:
                print(f"   • \"{test['question']}\"")
        else:
            print("⚠️ Some data coverage questions need attention")
        
        return results
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
        return None
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return None

if __name__ == "__main__":
    results = test_data_coverage_questions()
    
    if results:
        passed = sum(1 for r in results if "PASS" in r["status"])
        total = len(results)
        
        if passed == total:
            print(f"\n🎉 All tests passed! Data coverage questions are ready to use.")
            sys.exit(0)
        else:
            print(f"\n⚠️ {total - passed} tests failed. Please review the implementation.")
            sys.exit(1)
    else:
        print("❌ Testing failed")
        sys.exit(1)
