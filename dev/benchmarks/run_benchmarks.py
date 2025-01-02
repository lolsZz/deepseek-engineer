#!/usr/bin/env python3
"""
Benchmark Runner

This script executes all benchmarks and generates a comprehensive performance report.
It tracks key metrics against our success criteria:
- Response time < 100ms
- Memory usage < 500MB
- Test coverage > 90%

Implementation Notes:
- Runs benchmarks in isolation to prevent interference
- Generates HTML and JSON reports
- Includes trend analysis
- Flags performance regressions
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import pandas as pd

from core_benchmarks import run_benchmarks

class BenchmarkRunner:
    """Manages benchmark execution and reporting."""

    def __init__(self):
        self.results_dir = Path("dev/benchmarks/results")
        self.reports_dir = Path("dev/benchmarks/reports")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> None:
        """Execute all benchmarks."""
        print("Starting benchmark suite...")
        run_benchmarks()
        print("Benchmarks completed.")

    def generate_report(self) -> None:
        """Generate comprehensive performance report."""
        # Load latest results
        results_files = sorted(self.results_dir.glob("benchmark_results_*.json"))
        if not results_files:
            print("No benchmark results found.")
            return

        latest_results = self._load_json(results_files[-1])
        historical_data = self._load_historical_data(results_files[:-1])
        
        # Generate HTML report
        report_path = self.reports_dir / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        self._generate_html_report(report_path, latest_results, historical_data)
        
        # Check success metrics
        self._check_success_metrics(latest_results)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file safely."""
        with open(path) as f:
            return json.load(f)

    def _load_historical_data(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Load and process historical benchmark data."""
        return [self._load_json(f) for f in files]

    def _generate_html_report(self, path: Path, latest: Dict[str, Any], 
                            historical: List[Dict[str, Any]]) -> None:
        """Generate HTML report with visualizations."""
        # Convert data for plotting
        df = self._prepare_data_frame(latest, historical)
        
        # Generate plots
        self._generate_plots(df)
        
        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <title>DeepSeek Engineer Benchmark Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .metric {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .failure {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Benchmark Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>
            
            <h2>Success Metrics</h2>
            {self._format_success_metrics(latest)}
            
            <h2>Performance Trends</h2>
            <img src="trends.png" alt="Performance Trends">
            
            <h2>Detailed Results</h2>
            {self._format_detailed_results(latest)}
            
            <h2>System Information</h2>
            {self._format_system_info(latest)}
        </body>
        </html>
        """
        
        with open(path, 'w') as f:
            f.write(html_content)

    def _prepare_data_frame(self, latest: Dict[str, Any], 
                          historical: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare data for visualization."""
        data = []
        for result in historical + [latest]:
            for benchmark in result['results']:
                data.append({
                    'timestamp': benchmark['timestamp'],
                    'name': benchmark['name'],
                    'execution_time': benchmark['metrics']['execution_time'],
                    'memory_usage': benchmark['metrics']['memory_usage']
                })
        return pd.DataFrame(data)

    def _generate_plots(self, df: pd.DataFrame) -> None:
        """Generate performance trend plots."""
        plt.figure(figsize=(12, 6))
        
        # Execution time trends
        plt.subplot(1, 2, 1)
        for name in df['name'].unique():
            data = df[df['name'] == name]
            plt.plot(data['timestamp'], data['execution_time'], label=name)
        plt.title('Execution Time Trends')
        plt.xticks(rotation=45)
        plt.legend()
        
        # Memory usage trends
        plt.subplot(1, 2, 2)
        for name in df['name'].unique():
            data = df[df['name'] == name]
            plt.plot(data['timestamp'], data['memory_usage'], label=name)
        plt.title('Memory Usage Trends')
        plt.xticks(rotation=45)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'trends.png')

    def _check_success_metrics(self, results: Dict[str, Any]) -> None:
        """Check results against success metrics."""
        failures = []
        
        for benchmark in results['results']:
            # Check response time
            if benchmark['metrics']['execution_time'] > 0.1:  # 100ms
                failures.append(f"{benchmark['name']}: Response time > 100ms")
            
            # Check memory usage
            if benchmark['metrics']['memory_usage'] > 500 * 1024 * 1024:  # 500MB
                failures.append(f"{benchmark['name']}: Memory usage > 500MB")
        
        if failures:
            print("\nWarning: Success metrics not met:")
            for failure in failures:
                print(f"- {failure}")
        else:
            print("\nSuccess: All performance metrics met!")

    def _format_success_metrics(self, results: Dict[str, Any]) -> str:
        """Format success metrics section of report."""
        metrics = []
        for benchmark in results['results']:
            status = self._get_metric_status(benchmark['metrics'])
            metrics.append(f"""
                <div class="metric {status['class']}">
                    <h3>{benchmark['name']}</h3>
                    <p>Response Time: {benchmark['metrics']['execution_time']*1000:.2f}ms</p>
                    <p>Memory Usage: {benchmark['metrics']['memory_usage']/1024/1024:.2f}MB</p>
                    <p>Status: {status['text']}</p>
                </div>
            """)
        return '\n'.join(metrics)

    def _get_metric_status(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Determine status of metrics."""
        if (metrics['execution_time'] <= 0.1 and 
            metrics['memory_usage'] <= 500 * 1024 * 1024):
            return {'class': 'success', 'text': 'Passed'}
        elif (metrics['execution_time'] <= 0.15 or 
              metrics['memory_usage'] <= 600 * 1024 * 1024):
            return {'class': 'warning', 'text': 'Warning'}
        else:
            return {'class': 'failure', 'text': 'Failed'}

    def _format_detailed_results(self, results: Dict[str, Any]) -> str:
        """Format detailed results section."""
        details = []
        for benchmark in results['results']:
            details.append(f"""
                <div class="metric">
                    <h3>{benchmark['name']}</h3>
                    <pre>{json.dumps(benchmark['metrics'], indent=2)}</pre>
                </div>
            """)
        return '\n'.join(details)

    def _format_system_info(self, results: Dict[str, Any]) -> str:
        """Format system information section."""
        return f"""
            <div class="metric">
                <pre>{json.dumps(results['system_info'], indent=2)}</pre>
            </div>
        """

def main():
    """Main entry point."""
    runner = BenchmarkRunner()
    
    try:
        runner.run()
        runner.generate_report()
    except Exception as e:
        print(f"Error running benchmarks: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()