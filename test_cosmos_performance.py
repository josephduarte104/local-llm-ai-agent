#!/usr/bin/env python3
"""
Performance testing script for Cosmos DB optimizations.
Run this to validate performance improvements after implementing optimizations.
"""

import os
import sys
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the elevator_ai_agent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'elevator_ai_agent'))

def test_query_performance():
    """Test and compare query performance before/after optimizations."""
    
    try:
        from services.cosmos import get_cosmos_service
        from services.timezone import timezone_service
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv('elevator_ai_agent/.env')
        
        print("🚀 Cosmos DB Performance Testing")
        print("=" * 50)
        
        # Initialize service
        cosmos_service = get_cosmos_service()
        
        # Test installation
        installation_id = "4995d395-9b4b-4234-a8aa-9938ef5620c6"
        
        # Test time range (last 7 days)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        # Test scenarios
        test_results = {}
        
        print(f"\nTesting with installation: {installation_id}")
        print(f"Time range: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
        print("-" * 50)
        
        # Test 1: Machine IDs lookup (with caching)
        print("\n1. Testing Machine IDs Lookup (with caching)")
        test_results["machine_ids"] = benchmark_machine_ids_lookup(
            cosmos_service, installation_id
        )
        
        # Test 2: Car mode changes query
        print("\n2. Testing Car Mode Changes Query")
        test_results["car_mode_changes"] = benchmark_car_mode_changes(
            cosmos_service, installation_id, start_ts, end_ts
        )
        
        # Test 3: Door events query (optimized filtering)
        print("\n3. Testing Door Events Query (optimized filtering)")
        test_results["door_events"] = benchmark_door_events(
            cosmos_service, installation_id, start_ts, end_ts
        )
        
        # Test 4: Installations lookup (cached)
        print("\n4. Testing Installations Lookup (cached)")
        test_results["installations"] = benchmark_installations_lookup(
            cosmos_service
        )
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("=" * 50)
        
        for test_name, results in test_results.items():
            print(f"\n{test_name.upper()}:")
            print(f"  Average time: {results['avg_time']:.2f} ms")
            print(f"  Best time: {results['min_time']:.2f} ms")
            print(f"  Worst time: {results['max_time']:.2f} ms")
            print(f"  Items returned: {results['items_count']}")
            print(f"  Iterations: {results['iterations']}")
            
            if results.get('cache_benefit'):
                print(f"  Cache benefit: {results['cache_benefit']:.1f}x faster")
        
        print("\n✅ Performance testing completed!")
        print("\n💡 Tips for further optimization:")
        print("   - Apply the composite indexes from cosmos_indexing_policy.json")
        print("   - Monitor RU consumption using Azure Portal")
        print("   - Consider partition key optimization for large datasets")
        print("   - Use performance monitoring to track real-world improvements")
        
        return test_results
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
        return None
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return None

def benchmark_function(func, *args, iterations: int = 3, **kwargs) -> Dict[str, Any]:
    """Benchmark a function with multiple iterations."""
    times = []
    results = []
    
    for i in range(iterations):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            # Convert iterator to list if needed
            if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict)):
                result = list(result)
            results.append(result)
        except Exception as e:
            print(f"    Error in iteration {i+1}: {e}")
            results.append([])
        
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        times.append(execution_time)
        print(f"    Iteration {i+1}: {execution_time:.2f} ms")
    
    # Calculate statistics
    if times:
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
    else:
        avg_time = min_time = max_time = 0
    
    # Count items in the last successful result
    items_count = 0
    for result in reversed(results):
        if result:
            items_count = len(result) if isinstance(result, list) else 1
            break
    
    return {
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "items_count": items_count,
        "iterations": len(times),
        "all_times": times
    }

def benchmark_machine_ids_lookup(cosmos_service, installation_id: str) -> Dict[str, Any]:
    """Test machine IDs lookup with caching benefit."""
    print("  Testing machine IDs lookup...")
    
    # Clear cache first
    if hasattr(cosmos_service, 'clear_cache'):
        cosmos_service.clear_cache()
    
    # First run (cache miss)
    print("  Cache miss:")
    first_run = benchmark_function(
        cosmos_service.get_all_machine_ids, 
        installation_id, 
        iterations=1
    )
    
    # Subsequent runs (cache hits)
    print("  Cache hits:")
    cached_runs = benchmark_function(
        cosmos_service.get_all_machine_ids, 
        installation_id, 
        iterations=3
    )
    
    # Calculate cache benefit
    cache_benefit = first_run["avg_time"] / cached_runs["avg_time"] if cached_runs["avg_time"] > 0 else 1
    
    return {
        **cached_runs,
        "cache_benefit": cache_benefit,
        "first_run_time": first_run["avg_time"]
    }

def benchmark_car_mode_changes(cosmos_service, installation_id: str, start_ts: int, end_ts: int) -> Dict[str, Any]:
    """Test car mode changes query."""
    print("  Testing car mode changes query...")
    return benchmark_function(
        cosmos_service.get_car_mode_changes,
        installation_id,
        start_ts,
        end_ts,
        iterations=3
    )

def benchmark_door_events(cosmos_service, installation_id: str, start_ts: int, end_ts: int) -> Dict[str, Any]:
    """Test door events query (now with SQL-side filtering)."""
    print("  Testing door events query...")
    return benchmark_function(
        cosmos_service.get_door_events,
        installation_id,
        start_ts,
        end_ts,
        iterations=3
    )

def benchmark_installations_lookup(cosmos_service) -> Dict[str, Any]:
    """Test installations lookup (cached)."""
    print("  Testing installations lookup...")
    
    # Clear cache first
    if hasattr(cosmos_service, 'clear_cache'):
        cosmos_service.clear_cache()
    
    # Test with caching
    return benchmark_function(
        cosmos_service.get_installations,
        iterations=5
    )

def generate_performance_report(results: Dict[str, Any]) -> str:
    """Generate a detailed performance report."""
    if not results:
        return "No performance data available."
    
    report = []
    report.append("# Cosmos DB Performance Test Report")
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("")
    
    for test_name, data in results.items():
        report.append(f"## {test_name.replace('_', ' ').title()}")
        report.append(f"- **Average Response Time**: {data['avg_time']:.2f} ms")
        report.append(f"- **Best Response Time**: {data['min_time']:.2f} ms") 
        report.append(f"- **Worst Response Time**: {data['max_time']:.2f} ms")
        report.append(f"- **Items Returned**: {data['items_count']}")
        report.append(f"- **Test Iterations**: {data['iterations']}")
        
        if data.get('cache_benefit'):
            report.append(f"- **Cache Performance Boost**: {data['cache_benefit']:.1f}x faster")
        
        report.append("")
    
    report.append("## Optimization Impact")
    report.append("These results reflect the following optimizations:")
    report.append("- ✅ Query result caching with TTL")
    report.append("- ✅ Optimized field selection in SQL queries") 
    report.append("- ✅ SQL-side filtering instead of Python filtering")
    report.append("- ✅ Better query parameter organization")
    report.append("- ⏳ Composite indexing (requires manual application)")
    report.append("- ⏳ Connection pooling (requires configuration)")
    
    return "\n".join(report)

if __name__ == "__main__":
    # Run performance tests
    results = test_query_performance()
    
    if results:
        # Save detailed report
        report = generate_performance_report(results)
        
        with open("cosmos_performance_test_results.md", "w") as f:
            f.write(report)
        
        print(f"\n📄 Detailed report saved to: cosmos_performance_test_results.md")
    else:
        print("❌ Performance testing failed")
        sys.exit(1)
