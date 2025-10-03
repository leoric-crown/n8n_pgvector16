#!/usr/bin/env python3
"""
Context Window Matrix Test Runner

Parses context_matrix.yaml and runs benchmarks across all defined context sizes.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()


class MatrixRunner:
    """Run benchmarks based on matrix configuration"""

    def __init__(self, config_path: Path, cli_overrides: Optional[argparse.Namespace] = None):
        self.config_path = config_path
        self.config = self._load_config()
        self.cli_overrides = cli_overrides
        self.benchmark_script = Path(__file__).parent / "benchmark_models.py"
        # Single timestamp for entire matrix run
        self.run_timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

        if not self.benchmark_script.exists():
            raise FileNotFoundError(f"Benchmark script not found: {self.benchmark_script}")

    def _load_config(self) -> Dict[str, Any]:
        """Load matrix configuration from YAML"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get_context_sizes(self) -> List[int]:
        """Get list of context sizes to test"""
        return self.config['matrix']['context_sizes']

    def get_models(self) -> List[str]:
        """Get list of models or pattern"""
        matrix = self.config['matrix']

        # Check if using pattern matching
        if 'model_pattern' in matrix:
            return None  # Return None to indicate pattern usage

        return matrix.get('models', [])

    def get_output_path(self, context_size: int, format: str) -> Path:
        """Generate output file path in timestamped subdirectory (directory created on demand)"""
        output = self.config.get('output', {})
        base_output_dir = Path(output.get('output_dir', './results'))

        # Timestamped subdirectory path (not created yet - created when files are written)
        run_dir = base_output_dir / self.run_timestamp

        context_k = context_size // 1024

        # Filename without timestamp (timestamp is in directory name now)
        filename_template = output.get('filename_template', 'benchmark-{context}k')
        filename = filename_template.format(context=context_k, timestamp=self.run_timestamp)

        return run_dir / f"{filename}.{format}"

    def get_label(self, context_size: int) -> str:
        """Generate label for this benchmark run"""
        output = self.config.get('output', {})
        label_template = output.get('label_template', 'ctx-{context}')
        context_k = context_size // 1024
        return label_template.format(context=context_k)

    def build_command(self, context_size: int) -> List[str]:
        """Build benchmark command for given context size"""
        benchmark = self.config.get('benchmark', {})
        connection = self.config.get('connection', {})
        output_config = self.config.get('output', {})
        advanced = self.config.get('advanced', {})

        cmd = [
            sys.executable,  # Use same Python interpreter
            str(self.benchmark_script),
        ]

        # Connection settings
        cmd.extend([
            '--host', connection.get('host', 'localhost'),
            '--port', str(connection.get('port', 11434)),
        ])

        # Model selection
        models = self.get_models()
        if models is None:
            # Use pattern matching
            pattern = self.config['matrix'].get('model_pattern', 'all')
            cmd.extend(['--select', pattern])
        elif models:
            cmd.extend(['--models', ','.join(models)])

        # Benchmark parameters (apply CLI overrides if provided)
        num_predict = self.cli_overrides.num_predict if (self.cli_overrides and self.cli_overrides.num_predict) else benchmark.get('num_predict', 1024)
        temperature = self.cli_overrides.temperature if (self.cli_overrides and self.cli_overrides.temperature is not None) else benchmark.get('temperature', 0.2)
        repeat_runs = self.cli_overrides.repeat_runs if (self.cli_overrides and self.cli_overrides.repeat_runs) else benchmark.get('repeat_runs', 1)
        keep_alive = self.cli_overrides.keep_alive if (self.cli_overrides and self.cli_overrides.keep_alive) else benchmark.get('keep_alive', '2s')

        cmd.extend([
            '--num-ctx', str(context_size),
            '--num-predict', str(num_predict),
            '--temperature', str(temperature),
            '--repeat-runs', str(repeat_runs),
            '--keep-alive', keep_alive,
        ])

        # Label
        label = self.get_label(context_size)
        cmd.extend(['--label', label])

        # Output directory and formats (new interface)
        formats = output_config.get('formats', ['csv'])

        # Get the base output directory for this context
        output_base = Path(output_config.get('output_dir', './results'))
        run_dir = output_base / self.run_timestamp

        # Create context-specific subdirectory name
        context_k = context_size // 1024
        context_dir = run_dir / f"ctx-{context_k}k"

        # Use the new output interface
        cmd.extend(['-o', str(context_dir)])

        # Add format flags
        for fmt in formats:
            cmd.append(f'--{fmt}')

        # Advanced options
        if advanced.get('debug', False):
            cmd.append('--debug')

        # Ollama binary path
        ollama_bin = connection.get('ollama_bin', 'ollama')
        if ollama_bin != 'ollama':
            cmd.extend(['--ollama-bin', ollama_bin])

        # Prompt configuration
        if 'prompt_file' in self.config and self.config['prompt_file']:
            cmd.extend(['--prompt-file', self.config['prompt_file']])
        elif 'prompt' in self.config and self.config['prompt']:
            cmd.extend(['--prompt', self.config['prompt']])

        return cmd

    def run_matrix(self, dry_run: bool = False) -> None:
        """Run benchmarks for all context sizes in the matrix"""
        context_sizes = self.get_context_sizes()
        advanced = self.config.get('advanced', {})

        # Display matrix summary
        self.display_summary(context_sizes)

        if dry_run:
            console.print("\n[yellow]Dry run mode - showing commands that would be executed:[/yellow]\n")
            for ctx_size in context_sizes:
                cmd = self.build_command(ctx_size)
                console.print(f"[cyan]Context: {ctx_size} tokens[/cyan]")
                console.print(f"  {' '.join(cmd)}\n")
            return

        # Run benchmarks
        console.print(f"\n[green]Starting matrix benchmark run...[/green]")

        total_tests = len(context_sizes)
        created_files = []  # Track actual created files

        for idx, ctx_size in enumerate(context_sizes, 1):
            console.print("\n" + "="*80)
            console.print(f"[bold cyan]Test {idx}/{total_tests}: Context Size = {ctx_size:,} tokens ({ctx_size // 1024}K)[/bold cyan]")
            console.print("="*80 + "\n")

            cmd = self.build_command(ctx_size)

            # Show command
            if advanced.get('debug', False):
                console.print(f"[dim]Command: {' '.join(cmd)}[/dim]\n")

            try:
                # Track files that should be created from this command
                output_config = self.config.get('output', {})
                formats = output_config.get('formats', ['csv'])
                expected_files = []

                # Files are now in context-specific subdirectories
                output_base = Path(output_config.get('output_dir', './results'))
                run_dir = output_base / self.run_timestamp
                context_k = ctx_size // 1024
                context_dir = run_dir / f"ctx-{context_k}k"

                for fmt in formats:
                    expected_files.append(context_dir / f"benchmark.{fmt}")

                # Also track system_info.json
                expected_files.append(context_dir / "system_info.json")

                # Run the benchmark
                result = subprocess.run(
                    cmd,
                    check=True,
                    text=True
                )

                # Only add files that actually exist (benchmark may have failed to create them)
                for file_path in expected_files:
                    if file_path.exists():
                        created_files.append(file_path)

                console.print(f"\n[green]✓ Completed test {idx}/{total_tests}[/green]")

            except subprocess.CalledProcessError as e:
                console.print(f"\n[red]✗ Test failed with exit code {e.returncode}[/red]")
                if not self._continue_on_error():
                    console.print("[yellow]Matrix run aborted[/yellow]")
                    self._cleanup_empty_directory(created_files)
                    return

            except KeyboardInterrupt:
                console.print("\n[yellow]Matrix run interrupted by user[/yellow]")
                self._cleanup_empty_directory(created_files)
                return

            # Stop models between contexts if configured
            if advanced.get('stop_between_contexts', True) and idx < total_tests:
                self._stop_all_models()

        console.print("\n" + "="*80)
        console.print("[bold green]🎉 Matrix Benchmark Complete![/bold green]")
        console.print("="*80 + "\n")

        # Clean up empty timestamped directory if no files were created
        self._cleanup_empty_directory(created_files)

        # Show output summary with actual created files
        self.display_output_summary_from_files(created_files)

    def display_summary(self, context_sizes: List[int]) -> None:
        """Display matrix configuration summary"""
        table = Table(title="Matrix Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Source", style="dim")

        # Matrix info
        models = self.get_models()
        if models is None:
            model_info = f"Pattern: {self.config['matrix'].get('model_pattern')}"
        else:
            model_info = f"{len(models)} models: {', '.join(models[:3])}" + ("..." if len(models) > 3 else "")

        table.add_row("Context Sizes", f"{len(context_sizes)} sizes: {', '.join(f'{c//1024}K' for c in context_sizes)}", "YAML")
        table.add_row("Models", model_info, "YAML")

        # Benchmark settings with override indicators
        benchmark = self.config.get('benchmark', {})

        # Check for CLI overrides
        num_predict_val = self.cli_overrides.num_predict if (self.cli_overrides and self.cli_overrides.num_predict) else benchmark.get('num_predict', 1024)
        num_predict_src = "CLI override" if (self.cli_overrides and self.cli_overrides.num_predict) else "YAML"

        temperature_val = self.cli_overrides.temperature if (self.cli_overrides and self.cli_overrides.temperature is not None) else benchmark.get('temperature', 0.2)
        temperature_src = "CLI override" if (self.cli_overrides and self.cli_overrides.temperature is not None) else "YAML"

        repeat_runs_val = self.cli_overrides.repeat_runs if (self.cli_overrides and self.cli_overrides.repeat_runs) else benchmark.get('repeat_runs', 1)
        repeat_runs_src = "CLI override" if (self.cli_overrides and self.cli_overrides.repeat_runs) else "YAML"

        keep_alive_val = self.cli_overrides.keep_alive if (self.cli_overrides and self.cli_overrides.keep_alive) else benchmark.get('keep_alive', '2s')
        keep_alive_src = "CLI override" if (self.cli_overrides and self.cli_overrides.keep_alive) else "YAML"

        table.add_row("Tokens to Generate", str(num_predict_val), num_predict_src)
        table.add_row("Repeat Runs", str(repeat_runs_val), repeat_runs_src)
        table.add_row("Temperature", str(temperature_val), temperature_src)
        table.add_row("Keep Alive", str(keep_alive_val), keep_alive_src)

        # Output settings
        output = self.config.get('output', {})
        formats = ', '.join(output.get('formats', ['csv']))
        table.add_row("Output Formats", formats, "YAML")
        output_path = f"{output.get('output_dir', './results')}/{self.run_timestamp}/"
        table.add_row("Output Directory", output_path, "Auto")

        console.print(table)

        # Calculate total benchmarks
        models_count = len(models) if models else "?"
        repeat_runs = benchmark.get('repeat_runs', 1)
        if models:
            total = len(context_sizes) * len(models) * repeat_runs
            console.print(f"\n[yellow]Total benchmarks to run: {total:,}[/yellow]")

    def display_output_summary_from_files(self, created_files: List[Path]) -> None:
        """Display summary of created output files"""
        if not created_files:
            console.print("[yellow]No output files were created - all benchmarks may have failed[/yellow]")
            return

        # Show base directory path from first file (go up to run dir)
        first_file = created_files[0]
        # Files are in ctx-8k/benchmark.csv, so go up 2 levels to get run dir
        output_dir = first_file.parent.parent
        console.print(f"[cyan]Results saved to:[/cyan] [white]{output_dir}/[/white]\n")

        # Group files by context directory
        from collections import defaultdict
        by_context = defaultdict(list)

        for file_path in created_files:
            # Extract context from parent directory name (e.g., ctx-8k -> 8)
            import re
            dir_match = re.search(r'ctx-(\d+)k', file_path.parent.name)
            if dir_match:
                context_k = int(dir_match.group(1))
                by_context[context_k].append(file_path)

        # Display sorted by context size
        for context_k in sorted(by_context.keys()):
            console.print(f"  [white]Context {context_k}K:[/white] [dim](ctx-{context_k}k/)[/dim]")
            for file_path in by_context[context_k]:
                if file_path.exists():
                    console.print(f"    [green]✓[/green] {file_path.name}")
                else:
                    console.print(f"    [yellow]⚠[/yellow] {file_path.name} [dim](expected but not found)[/dim]")

    def display_output_summary(self, context_sizes: List[int]) -> None:
        """Display summary of output files (legacy - scans directory)"""
        output = self.config.get('output', {})
        output_dir = Path(output.get('output_dir', './results'))

        if not output_dir.exists():
            console.print("[yellow]No output directory found[/yellow]")
            return

        console.print("[cyan]Output Files:[/cyan]\n")

        # Scan for actual files
        for ctx_size in context_sizes:
            context_k = ctx_size // 1024
            pattern = f"benchmark-{context_k}k-*.csv"
            matches = list(output_dir.glob(pattern))

            if matches:
                console.print(f"  [white]Context {context_k}K:[/white]")
                for file_path in sorted(matches):
                    # Find corresponding json file
                    json_file = file_path.with_suffix('.json')
                    console.print(f"    [green]✓[/green] {file_path}")
                    if json_file.exists():
                        console.print(f"    [green]✓[/green] {json_file}")

    def _cleanup_empty_directory(self, created_files: List[Path]) -> None:
        """Remove timestamped directory if no files were created"""
        if not created_files:
            output = self.config.get('output', {})
            base_output_dir = Path(output.get('output_dir', './results'))
            run_dir = base_output_dir / self.run_timestamp

            # Remove directory if it exists and is empty (recursively check subdirs)
            if run_dir.exists():
                try:
                    # Remove empty context subdirectories first
                    for subdir in run_dir.iterdir():
                        if subdir.is_dir() and not any(subdir.iterdir()):
                            subdir.rmdir()

                    # Remove main directory if now empty
                    if not any(run_dir.iterdir()):
                        run_dir.rmdir()
                        console.print("[dim]Cleaned up empty results directory[/dim]")
                except:
                    pass

    def _stop_all_models(self) -> None:
        """Stop all running models"""
        connection = self.config.get('connection', {})
        ollama_bin = connection.get('ollama_bin', 'ollama')

        try:
            console.print("\n[dim]Stopping all models...[/dim]")
            subprocess.run(
                [ollama_bin, 'stop', '*'],
                capture_output=True,
                timeout=10
            )
        except:
            pass

    def _continue_on_error(self) -> bool:
        """Ask user if they want to continue after error"""
        response = console.input("[yellow]Continue with remaining tests? [y/N]: [/yellow]")
        return response.lower() in ['y', 'yes']


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Run context window matrix benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--config',
        type=Path,
        default=Path(__file__).parent / 'config' / 'context_matrix.yaml',
        help='Matrix configuration file (default: config/context_matrix.yaml)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show commands that would be executed without running them'
    )

    # Parameter overrides (highest precedence)
    override_group = parser.add_argument_group("Parameter Overrides")
    override_group.add_argument(
        '--num-predict',
        type=int,
        help='Override num_predict from YAML config'
    )
    override_group.add_argument(
        '--temperature',
        type=float,
        help='Override temperature from YAML config'
    )
    override_group.add_argument(
        '--repeat-runs',
        type=int,
        help='Override repeat_runs from YAML config'
    )
    override_group.add_argument(
        '--keep-alive',
        type=str,
        help='Override keep_alive from YAML config (e.g., "5m", "2s")'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()

    if not args.config.exists():
        console.print(f"[red]Error: Configuration file not found: {args.config}[/red]")
        sys.exit(1)

    try:
        # Pass CLI overrides to runner for parameter precedence
        runner = MatrixRunner(args.config, cli_overrides=args)
        runner.run_matrix(dry_run=args.dry_run)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
