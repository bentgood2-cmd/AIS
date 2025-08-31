#!/usr/bin/env python3
"""Run comprehensive AIS benchmarks for self-improvement evaluation."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ais.core.benchmark_suite import BenchmarkSuite

async def main():
    """Run comprehensive benchmark evaluation."""
    print("🧪 AIS Self-Improvement Benchmark Suite")
    print("=" * 50)
    
    suite = BenchmarkSuite()
    
    # Run individual benchmarks
    benchmarks = ["gsm8k", "math", "humaneval", "mmlu"]
    
    print("\n📊 Running Core Benchmarks...")
    for benchmark in benchmarks:
        print(f"\n🎯 Running {benchmark.upper()} benchmark...")
        result = suite.run_benchmark(benchmark)
        print(f"✓ {benchmark}: {result['accuracy']:.1%} accuracy ({result['correct']}/{result['total']})")
    
    # Run self-improvement cycle
    print("\n🔄 Running Self-Improvement Cycle...")
    cycle_results = suite.run_self_improvement_cycle(iterations=3)
    
    print("\n📈 Self-Improvement Results:")
    for i, iteration in enumerate(cycle_results["iterations"]):
        avg_acc = iteration["average_accuracy"]
        print(f"  Iteration {i+1}: {avg_acc:.1%} average accuracy")
    
    # Show improvement metrics
    if cycle_results["improvement_metrics"]:
        print("\n🚀 Improvement Analysis:")
        for benchmark, metrics in cycle_results["improvement_metrics"].items():
            improvement = metrics["improvement"]
            relative = metrics["relative_improvement"]
            print(f"  {benchmark}: {improvement:+.3f} ({relative:+.1%} relative)")
    
    # Generate comprehensive report
    print("\n📋 Generating Comprehensive Report...")
    report = suite.get_comprehensive_report()
    
    print(f"\n🎯 Overall Performance:")
    print(f"  Average Accuracy: {report['summary']['overall_accuracy']:.1%}")
    print(f"  Total Problems: {report['summary']['total_problems']}")
    print(f"  Total Correct: {report['summary']['total_correct']}")
    
    print(f"\n💡 Recommendations:")
    for rec in report["recommendations"][:3]:  # Show top 3
        print(f"  • {rec}")
    
    # Save detailed results
    import json
    with open("benchmark_results.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Detailed results saved to benchmark_results.json")
    print(f"🎉 Benchmark evaluation completed!")

if __name__ == "__main__":
    asyncio.run(main())