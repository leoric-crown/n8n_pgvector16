#!/usr/bin/env python3
"""
Enhanced Ollama Model Benchmarking Tool

A comprehensive benchmarking utility for Ollama models with rich terminal output,
memory monitoring, and flexible data export capabilities.
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings

import pandas as pd
import requests
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich.columns import Columns
from rich.rule import Rule

console = Console()


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs"""
    host: str = "localhost"
    port: int = 11434
    num_predict: int = 256
    num_ctx: int = 4096
    temperature: float = 0.2
    prompt: Optional[str] = None
    prompt_file: Optional[Path] = None
    models: List[str] = field(default_factory=list)
    select_pattern: Optional[str] = None
    mem_split: bool = True
    debug: bool = False
    label: Optional[str] = None
    csv_output: Optional[Path] = None
    json_output: Optional[Path] = None
    parquet_output: Optional[Path] = None
    config_file: Optional[Path] = None
    repeat_runs: int = 1
    keep_alive: str = "2s"
    ollama_bin: str = "ollama"
    enable_streaming: bool = True

    @classmethod
    def from_yaml(cls, path: Path) -> 'BenchmarkConfig':
        """Load configuration from YAML file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def merge_args(self, args: argparse.Namespace) -> None:
        """Merge command-line arguments into configuration"""
        for key, value in vars(args).items():
            if value is not None:
                setattr(self, key, value)


@dataclass
class ModelInfo:
    """Information about a model"""
    name: str
    disk_gb: float = 0.0
    size_bytes: int = 0
    digest: str = ""
    modified_at: str = ""

    @property
    def disk_size_str(self) -> str:
        """Format disk size for display"""
        if self.disk_gb > 0:
            return f"{self.disk_gb:.1f}"
        return "n/a"


@dataclass
class MemoryInfo:
    """Memory usage information from ollama ps"""
    ram_percent: int = 0
    vram_percent: int = 0
    size_gb: float = 0.0
    processor: str = ""
    context_length: int = 0
    active: bool = False

    @property
    def split_str(self) -> str:
        """Format RAM/VRAM split for display"""
        if self.ram_percent or self.vram_percent:
            return f"{self.ram_percent}%/{self.vram_percent}%"
        return "n/a"

    @property
    def size_str(self) -> str:
        """Format memory size for display"""
        if self.size_gb > 0:
            if self.size_gb >= 10:
                return f"{self.size_gb:.0f}"  # 10+ GB: no decimal
            else:
                return f"{self.size_gb:.1f}"  # <10 GB: one decimal
        return "n/a"

    @property
    def processor_str(self) -> str:
        """Format processor info for display"""
        if self.processor:
            return self.processor
        if self.vram_percent > 0:
            return f"{self.vram_percent}% GPU"
        return "CPU"


@dataclass
class PartialResult:
    """Partial result while benchmark is running"""
    model: str
    preloaded: bool = False
    model_info: Optional[ModelInfo] = None
    memory_info: Optional[MemoryInfo] = None
    status: str = "RUNNING"  # RUNNING, COMPLETED, ERROR

@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""
    model: str
    timestamp: datetime = field(default_factory=datetime.now)
    preloaded: bool = False
    tokens: int = 0
    load_duration_ns: int = 0
    eval_duration_ns: int = 0
    total_duration_ns: int = 0
    prompt_eval_duration_ns: int = 0
    context_length: int = 0
    memory_info: Optional[MemoryInfo] = None
    model_info: Optional[ModelInfo] = None
    error: Optional[str] = None
    label: Optional[str] = None
    response_text: Optional[str] = None

    @property
    def load_s(self) -> float:
        """Load time in seconds"""
        return self.load_duration_ns / 1e9 if self.load_duration_ns > 0 else 0

    @property
    def eval_s(self) -> float:
        """Evaluation time in seconds"""
        return self.eval_duration_ns / 1e9 if self.eval_duration_ns > 0 else 0

    @property
    def total_s(self) -> float:
        """Total time in seconds"""
        return self.total_duration_ns / 1e9 if self.total_duration_ns > 0 else 0

    @property
    def prompt_eval_s(self) -> float:
        """Prompt evaluation time in seconds"""
        return self.prompt_eval_duration_ns / 1e9 if self.prompt_eval_duration_ns > 0 else 0

    @property
    def tokens_per_second(self) -> float:
        """Tokens per second"""
        if self.eval_s > 0:
            return self.tokens / self.eval_s
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export"""
        d = {
            'model': self.model,
            'timestamp': self.timestamp.isoformat(),
            'preloaded': self.preloaded,
            'tokens': self.tokens,
            'load_s': round(self.load_s, 3),
            'eval_s': round(self.eval_s, 3),
            'total_s': round(self.total_s, 3),
            'prompt_eval_s': round(self.prompt_eval_s, 3),
            'tokens_per_second': round(self.tokens_per_second, 1),
            'context_length': self.context_length,
            'label': self.label,
            'error': self.error,
        }

        if self.model_info:
            d['disk_gb'] = self.model_info.disk_gb

        if self.memory_info:
            d['ram_percent'] = self.memory_info.ram_percent
            d['vram_percent'] = self.memory_info.vram_percent
            d['memory_gb'] = self.memory_info.size_gb
            d['processor'] = self.memory_info.processor

        return d


class OllamaBenchmark:
    """Main benchmarking class"""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.api_base = f"http://{config.host}:{config.port}"
        self.results: List[BenchmarkResult] = []
        self._model_cache: Dict[str, ModelInfo] = {}

    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models from Ollama"""
        try:
            response = requests.get(f"{self.api_base}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get('models', []):
                info = ModelInfo(
                    name=model_data['name'],
                    size_bytes=model_data.get('size', 0),
                    disk_gb=model_data.get('size', 0) / (1024**3),
                    digest=model_data.get('digest', ''),
                    modified_at=model_data.get('modified_at', '')
                )
                models.append(info)
                self._model_cache[info.name] = info

            return models
        except Exception as e:
            if self.config.debug:
                console.print(f"[red]Error fetching models: {e}[/red]")
            return []

    def select_models(self, pattern: Optional[str] = None) -> List[str]:
        """Select models based on pattern or configuration, always sorted with version sort"""
        available = self.get_available_models()
        model_names = [m.name for m in available]

        if pattern:
            if pattern.lower() in ['all', '*']:
                selected = model_names
            else:
                regex = re.compile(pattern, re.IGNORECASE)
                selected = [m for m in model_names if regex.search(m)]
        elif self.config.models:
            selected = self.config.models
            # Filter to only include available models
            selected = [m for m in selected if m in model_names]
        else:
            selected = [
                "phi4-mini:3.8b",
                "gemma3:4b",
                "deepseek-r1:8b",
                "qwen3:8b",
                "gpt-oss:latest",
                "qwen3-coder:30b"
            ]
            selected = [m for m in selected if m in model_names]

        # Always sort using version sort (like ollama ls | sort -V)
        return self.version_sort_models(selected)

    def version_sort_models(self, models: List[str]) -> List[str]:
        """Sort models using version sort (like sort -V)"""
        try:
            # Use subprocess to get proper version sorting like ollama ls | sort -V
            if not models:
                return models

            # Join models with newlines, sort with -V, split back to list
            models_text = '\n'.join(models)
            result = subprocess.run(
                ['sort', '-V'],
                input=models_text,
                text=True,
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                return [line for line in result.stdout.strip().split('\n') if line]
            else:
                # Fallback to regular sort if -V not available
                return sorted(models)

        except Exception:
            # Fallback to regular Python sort
            return sorted(models)

    def is_model_preloaded(self, model: str) -> bool:
        """Check if model is currently loaded in memory"""
        try:
            response = requests.get(f"{self.api_base}/api/ps", timeout=2)
            response.raise_for_status()
            data = response.json()

            for loaded in data.get('models', []):
                if loaded.get('name') == model:
                    return True
            return False
        except:
            return False

    def start_memory_monitor(self, model: str, partial_result: PartialResult, stop_event: threading.Event) -> None:
        """Background thread to continuously monitor memory usage"""
        while not stop_event.is_set():
            memory_info = self.get_memory_info(model)
            if memory_info:
                memory_info.active = True
                partial_result.memory_info = memory_info
            time.sleep(0.5)  # Check every 500ms

    def get_memory_info(self, model: str) -> Optional[MemoryInfo]:
        """Get memory usage information from ollama ps - always try, fail gracefully"""

        try:
            env = os.environ.copy()
            env['OLLAMA_HOST'] = f"{self.config.host}:{self.config.port}"

            result = subprocess.run(
                [self.config.ollama_bin, 'ps'],
                capture_output=True,
                text=True,
                env=env,
                timeout=5
            )

            if result.returncode != 0:
                return None

            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                parts = line.split()
                if parts and parts[0] == model:
                    mem_info = MemoryInfo()

                    # Parse memory size (e.g., "23 GB")
                    for i, part in enumerate(parts):
                        if part == "GB" and i > 0:
                            try:
                                mem_info.size_gb = float(parts[i-1])
                            except:
                                pass

                        # Parse processor info (e.g., "100% GPU" or "3%/97% CPU/GPU")
                        if "%" in part:
                            if "/" in part:
                                # Split format: "3%/97%"
                                splits = part.split('/')
                                try:
                                    mem_info.ram_percent = int(splits[0].strip('%'))
                                    mem_info.vram_percent = int(splits[1].strip('%'))
                                except:
                                    pass
                            elif i+1 < len(parts) and parts[i+1] in ['CPU', 'GPU']:
                                # Single percentage with CPU/GPU
                                try:
                                    percent = int(part.strip('%'))
                                    if parts[i+1] == 'GPU':
                                        mem_info.vram_percent = percent
                                        mem_info.ram_percent = 100 - percent
                                    else:
                                        mem_info.ram_percent = percent
                                        mem_info.vram_percent = 100 - percent
                                except:
                                    pass

                        # Get context length
                        if part.isdigit() and i == len(parts) - 2:
                            try:
                                mem_info.context_length = int(part)
                            except:
                                pass

                    # Set processor string
                    if mem_info.vram_percent > 0:
                        if mem_info.ram_percent > 0:
                            mem_info.processor = f"{mem_info.ram_percent}%/{mem_info.vram_percent}% CPU/GPU"
                        else:
                            mem_info.processor = f"{mem_info.vram_percent}% GPU"
                    else:
                        mem_info.processor = "CPU"

                    return mem_info

            return None
        except Exception as e:
            if self.config.debug:
                console.print(f"[yellow]Warning: Could not get memory info: {e}[/yellow]")
            return None

    def stop_model(self, model: str) -> None:
        """Stop a model to free memory"""
        try:
            env = os.environ.copy()
            env['OLLAMA_HOST'] = f"{self.config.host}:{self.config.port}"

            subprocess.run(
                [self.config.ollama_bin, 'stop', model],
                capture_output=True,
                env=env,
                timeout=5
            )
        except:
            pass

    def load_prompt(self) -> str:
        """Load prompt from file or use default"""
        if self.config.prompt:
            return self.config.prompt

        if self.config.prompt_file and self.config.prompt_file.exists():
            return self.config.prompt_file.read_text()

        # Check for default prompt file
        script_dir = Path(__file__).parent
        default_prompt_file = script_dir / "benchmark_prompt.md"
        if default_prompt_file.exists():
            return default_prompt_file.read_text()

        # Fallback to embedded prompt
        return """Task: Write one neutral, self-contained paragraph explaining how to benchmark small local language models fairly across devices.

Requirements:
- Output exactly five sentences.
- Each sentence must contain 14-16 words.
- Use plain English; avoid brand names, URLs, or platform-specific details.
- Do not include lists, headings, code, markdown, apologies, or meta commentary.
- Provide only the paragraph content; no title, no introduction, no closing."""

    def run_benchmark_streaming(self, model: str, prompt: str, live_display, all_results, progress_text, next_model, current_last_response: Optional[str] = None, current_last_response_model: Optional[str] = None) -> BenchmarkResult:
        """Run a streaming benchmark test with live response display and memory monitoring"""
        preloaded = self.is_model_preloaded(model)
        model_info = self._model_cache.get(model)

        # Create partial result immediately and add to results for display
        partial_result = PartialResult(
            model=model,
            preloaded=preloaded,
            model_info=model_info,
            status="RUNNING"
        )
        all_results.append(partial_result)

        # Start background memory monitoring (always try)
        stop_event = threading.Event()
        memory_thread = threading.Thread(
            target=self.start_memory_monitor,
            args=(model, partial_result, stop_event)
        )
        memory_thread.daemon = True
        memory_thread.start()

        # Build request payload for streaming
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.num_predict,
                "num_ctx": self.config.num_ctx
            },
            # Try to disable thinking mode like --think false
            "think": False
        }

        # Always use keep_alive for memory monitoring
        payload["keep_alive"] = self.config.keep_alive

        # Track metrics
        response_text = ""
        tokens = 0
        load_duration_ns = 0
        eval_duration_ns = 0
        total_duration_ns = 0
        prompt_eval_duration_ns = 0
        error_msg = None

        try:
            # Initial display update with partial result - keep previous response visible
            live_display.update(self.create_live_layout(
                all_results,
                model,
                current_last_response,  # Keep showing previous response
                progress_text,
                streaming=False,  # Not yet streaming
                last_response_model=current_last_response_model
            ))

            response = requests.post(
                f"{self.api_base}/api/generate",
                json=payload,
                stream=True,
                timeout=300
            )
            response.raise_for_status()

            # Process streaming response
            last_update_time = time.time()
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        chunk = json.loads(line)

                        # Extract response text
                        if 'response' in chunk:
                            response_text += chunk['response']

                        # Update display on every chunk or every 0.1 seconds (whichever comes first)
                        current_time = time.time()
                        should_update = (
                            'response' in chunk or  # Always update when we get new content
                            (current_time - last_update_time) > 0.1  # Force update every 100ms
                        )

                        if should_update:
                            display_response = response_text if response_text else current_last_response
                            response_model = model if response_text else current_last_response_model
                            live_display.update(self.create_live_layout(
                                all_results,
                                model,
                                display_response,
                                progress_text,
                                streaming=bool(response_text),  # Only show as streaming when we have new text
                                last_response_model=response_model
                            ))
                            last_update_time = current_time

                        # Extract metrics from final chunk
                        if chunk.get('done', False):
                            tokens = chunk.get('eval_count', 0)
                            load_duration_ns = chunk.get('load_duration', 0)
                            eval_duration_ns = chunk.get('eval_duration', 0)
                            total_duration_ns = chunk.get('total_duration', 0)
                            prompt_eval_duration_ns = chunk.get('prompt_eval_duration', 0)
                            break

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            error_msg = str(e)

        # Stop memory monitoring
        stop_event.set()
        memory_thread.join(timeout=1.0)

        # Remove partial result from all_results
        all_results.remove(partial_result)

        # Create final result
        result = BenchmarkResult(
            model=model,
            preloaded=preloaded,
            tokens=tokens,
            load_duration_ns=load_duration_ns,
            eval_duration_ns=eval_duration_ns,
            total_duration_ns=total_duration_ns,
            prompt_eval_duration_ns=prompt_eval_duration_ns,
            context_length=self.config.num_ctx,
            model_info=model_info,
            label=self.config.label,
            response_text=response_text,
            error=error_msg
        )

        # Get final memory info
        if not error_msg:
            time.sleep(0.5)  # Brief pause to let ollama ps update
            result.memory_info = self.get_memory_info(model)
        elif partial_result.memory_info:
            # Use last known memory info if there was an error
            result.memory_info = partial_result.memory_info

        return result

    def run_benchmark(self, model: str, prompt: str) -> BenchmarkResult:
        """Run a single benchmark test"""
        preloaded = self.is_model_preloaded(model)

        # Build request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.num_predict,
                "num_ctx": self.config.num_ctx
            },
            # Try to disable thinking mode like --think false
            "think": False
        }

        # Always use keep_alive for memory monitoring
        payload["keep_alive"] = self.config.keep_alive

        # Get model info from cache
        model_info = self._model_cache.get(model)

        # Run the benchmark
        try:
            response = requests.post(
                f"{self.api_base}/api/generate",
                json=payload,
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            data = response.json()

            # Extract metrics
            result = BenchmarkResult(
                model=model,
                preloaded=preloaded,
                tokens=data.get('eval_count', 0),
                load_duration_ns=data.get('load_duration', 0),
                eval_duration_ns=data.get('eval_duration', 0),
                total_duration_ns=data.get('total_duration', 0),
                prompt_eval_duration_ns=data.get('prompt_eval_duration', 0),
                context_length=self.config.num_ctx,
                model_info=model_info,
                label=self.config.label,
                response_text=data.get('response', '')
            )

            # Get actual context from response if available
            if 'context_length' in data:
                result.context_length = data['context_length']

            # Get memory info after the run
            time.sleep(0.5)  # Brief pause to let ollama ps update
            result.memory_info = self.get_memory_info(model)

            return result

        except Exception as e:
            return BenchmarkResult(
                model=model,
                preloaded=preloaded,
                error=str(e),
                model_info=model_info,
                label=self.config.label
            )

    def create_live_layout(self, results: List[BenchmarkResult], current_model: Optional[str] = None,
                          last_response: Optional[str] = None, progress_text: str = "",
                          streaming: bool = False, last_response_model: Optional[str] = None) -> Layout:
        """Create a live updating layout with results and response"""
        layout = Layout()

        # Split into top (results table) and bottom (response panel)
        layout.split_column(
            Layout(name="main", size=None),
            Layout(name="response", size=15)
        )

        # Create results table
        results_table = self.create_results_table(results)
        if current_model:
            results_table.title = f"Live Results - Currently Testing: [cyan]{current_model}[/cyan]"

        # Add progress info if available
        if progress_text:
            progress_panel = Panel(progress_text, title="Progress", border_style="blue")
            layout["main"].split_column(
                Layout(progress_panel, size=4),
                Layout(results_table)
            )
        else:
            layout["main"].update(results_table)

        # Create response panel
        if last_response:
            # For streaming, show the tail end to see live generation
            # For completed responses, show from the beginning and collapse <think> tags
            display_response = last_response
            max_chars = 3000 if streaming else 2000

            # Collapse <think> tags in completed responses
            if not streaming:
                display_response = self.collapse_think_tags(display_response)

            # Handle scrolling for long responses
            if streaming:
                # For streaming, show the last ~8 lines to make scrolling more visible
                display_response = self.get_scrolled_text(display_response, max_lines=8, from_end=True)
            elif len(display_response) > max_chars:
                # For completed responses, truncate from beginning
                display_response = display_response[:max_chars] + "\n\n... (truncated)"

            # Clean response text to remove [dim] tags and other unwanted markup
            clean_response = self.clean_response_text(display_response)

            # Add typing indicator for streaming and show model name
            if streaming and current_model:
                title = f"[green]🟢 {current_model} (streaming...)[/green]"
                clean_response += " ▋"  # Add cursor for streaming effect (no dim tags)
            elif last_response_model:
                title = f"[green]Last Model ({last_response_model}) Response[/green]"
            else:
                title = "[green]Last Model Response[/green]"

            response_panel = Panel(
                Text(clean_response, style="white"),
                title=title,
                border_style="green" if streaming else "blue"
            )
        else:
            response_panel = Panel(
                "[dim]Waiting for first response...[/dim]",
                title="Model Response",
                border_style="dim"
            )

        layout["response"].update(response_panel)
        return layout

    def collapse_think_tags(self, text: str) -> str:
        """Collapse <think> tags and show character count"""
        import re

        def replace_think_block(match):
            think_content = match.group(1)
            char_count = len(think_content)
            return f"[dim]<think> ({char_count} chars) ... </think>[/dim]"

        # Find and replace <think>...</think> blocks (case insensitive, multiline)
        pattern = r'<think>(.*?)</think>'
        collapsed = re.sub(pattern, replace_think_block, text, flags=re.IGNORECASE | re.DOTALL)

        return collapsed

    def clean_response_text(self, text: str) -> str:
        """Clean response text for display by removing Rich markup tags like [dim]"""
        import re
        if not text:
            return text

        # Remove [dim] and [/dim] tags specifically
        cleaned = re.sub(r'\[/?dim\]', '', text)
        return cleaned

    def create_progress_bar(self, completed: int, total: int, width: Optional[int] = None) -> str:
        """Create a visual progress bar that adapts to terminal width"""
        # Calculate available width based on terminal size
        if width is None:
            terminal_width = console.size.width
            # Reserve space for percentage and count text (e.g., " 100% (13/13)")
            reserved_space = 15
            # Account for panel borders and padding
            panel_padding = 6
            width = max(20, terminal_width - reserved_space - panel_padding)

        if total == 0:
            return "[green]" + "█" * width + "[/green] 100%"

        progress_ratio = completed / total
        filled_width = int(width * progress_ratio)
        empty_width = width - filled_width

        # Use █ (full block) for filled and ░ (light shade) for empty - more visible
        filled_bar = "█" * filled_width
        empty_bar = "░" * empty_width
        percentage = int(progress_ratio * 100)

        return f"[green]{filled_bar}[/green][dim]{empty_bar}[/dim] {percentage}% ({completed}/{total})"

    def get_scrolled_text(self, text: str, max_lines: int = 8, from_end: bool = True) -> str:
        """Get scrolled view of text showing the most recent lines"""
        if not text:
            return text

        lines = text.split('\n')

        if len(lines) <= max_lines:
            return text

        if from_end:
            # Show the last N lines (auto-scroll effect)
            visible_lines = lines[-max_lines:]
            # Add indicator that we're showing the tail (no dim tags for output panel)
            if len(lines) > max_lines:
                scroll_info = f"... (showing last {max_lines} lines of {len(lines)}) ▼"
                return scroll_info + '\n' + '\n'.join(visible_lines)
            return '\n'.join(visible_lines)
        else:
            # Show the first N lines
            visible_lines = lines[:max_lines]
            if len(lines) > max_lines:
                return '\n'.join(visible_lines) + f"\n... ({len(lines) - max_lines} more lines) ▼"
            return '\n'.join(visible_lines)

    def create_results_table(self, results: List[Union[BenchmarkResult, PartialResult]]) -> Table:
        """Create a rich table with benchmark results"""
        table = Table(
            title="Benchmark Results",
            show_header=True,
            header_style="bold magenta",
            show_lines=False,
            expand=True
        )

        # Add columns that will expand to fill horizontal space
        table.add_column("Model", style="cyan", no_wrap=True, min_width=18)
        table.add_column("Disk GB", justify="right", style="white", min_width=6)
        table.add_column("Preloaded", justify="center", style="white", min_width=8)
        table.add_column("Context", justify="right", style="white", min_width=6)

        # Always show memory columns (graceful fallback for remote benchmarks)
        table.add_column("RAM/VRAM", justify="right", style="yellow", min_width=8)
        table.add_column("MEM GB", justify="right", style="cyan", min_width=6)

        table.add_column("Load (s)", justify="right", style="white", min_width=7)
        table.add_column("Eval (s)", justify="right", style="white", min_width=7)
        table.add_column("Tok/s", justify="right", style="green", min_width=10)
        table.add_column("Total (s)", justify="right", style="white", min_width=8)

        # Add rows
        for result in results:
            if isinstance(result, PartialResult):
                # Partial result (still running)
                row = [
                    result.model,
                    result.model_info.disk_size_str if result.model_info else "n/a",
                    "[green]YES[/green]" if result.preloaded else "[yellow]NO[/yellow]",
                    "..."  # Context unknown while running
                ]

                # Memory info (always try to show)
                if result.memory_info and result.memory_info.active:
                    row.append(f"[bright_yellow]{result.memory_info.split_str}[/bright_yellow]")
                    row.append(f"[bright_cyan]{result.memory_info.size_str}[/bright_cyan]")
                else:
                    row.extend(["[dim]loading...[/dim]", "[dim]loading...[/dim]"])

                # Show running status for metrics
                if result.status == "RUNNING":
                    row.extend([
                        "[yellow]⏳[/yellow]",  # Load
                        "[yellow]⏳[/yellow]",  # Eval
                        "[yellow]STREAMING...[/yellow]",  # Tok/s
                        "[yellow]⏳[/yellow]"   # Total
                    ])
                else:
                    row.extend(["...", "...", "...", "..."])

            elif hasattr(result, 'error') and result.error:
                # Error row
                row = [
                    result.model,
                    result.model_info.disk_size_str if result.model_info else "n/a",
                    "YES" if result.preloaded else "NO",
                    str(result.context_length) if result.context_length else "n/a",
                ]

                # Memory columns (always shown)
                row.extend(["n/a", "n/a"])

                row.extend([
                    "[red]ERROR[/red]",
                    "[red]ERROR[/red]",
                    "[red]ERROR[/red]",
                    "[red]ERROR[/red]"
                ])

            else:
                # Complete result
                row = [
                    result.model,
                    result.model_info.disk_size_str if result.model_info else "n/a",
                    "[green]YES[/green]" if result.preloaded else "[yellow]NO[/yellow]",
                    str(result.context_length) if result.context_length else "n/a",
                ]

                # Memory info (always shown, graceful fallback)
                if result.memory_info:
                    row.append(result.memory_info.split_str)
                    row.append(result.memory_info.size_str)
                else:
                    row.extend(["n/a", "n/a"])

                # Performance metrics with color coding
                load_s = f"{result.load_s:.3f}"
                eval_s = f"{result.eval_s:.3f}"

                # Color code tokens/sec
                tps = result.tokens_per_second
                if tps > 100:
                    tps_str = f"[bright_green]{tps:.1f}[/bright_green]"
                elif tps > 50:
                    tps_str = f"[green]{tps:.1f}[/green]"
                elif tps > 25:
                    tps_str = f"[yellow]{tps:.1f}[/yellow]"
                else:
                    tps_str = f"[red]{tps:.1f}[/red]"

                total_s = f"{result.total_s:.3f}"

                row.extend([load_s, eval_s, tps_str, total_s])

            table.add_row(*row)

        return table

    def export_results(self, results: List[BenchmarkResult]) -> None:
        """Export results to configured formats"""
        if not results:
            return

        # Convert to DataFrame for easy export
        df = pd.DataFrame([r.to_dict() for r in results])

        # CSV export
        if self.config.csv_output:
            df.to_csv(self.config.csv_output, index=False)
            console.print(f"[green]✓[/green] Results saved to {self.config.csv_output}")

        # JSON export
        if self.config.json_output:
            with open(self.config.json_output, 'w') as f:
                json.dump([r.to_dict() for r in results], f, indent=2, default=str)
            console.print(f"[green]✓[/green] Results saved to {self.config.json_output}")

        # Parquet export
        if self.config.parquet_output:
            df.to_parquet(self.config.parquet_output, index=False)
            console.print(f"[green]✓[/green] Results saved to {self.config.parquet_output}")

    def run(self) -> None:
        """Run the complete benchmark suite with live updates"""
        # Print initial header
        console.print(Panel.fit(
            f"[bold cyan]Ollama Model Benchmarking Tool[/bold cyan]\n"
            f"Endpoint: {self.api_base}/api/generate\n"
            f"Context: {self.config.num_ctx} | Tokens: {self.config.num_predict} | "
            f"Temperature: {self.config.temperature}",
            title="Configuration",
            border_style="cyan"
        ))

        # Print environment variables if set
        env_vars = ['OLLAMA_NUM_PARALLEL', 'OLLAMA_MAX_LOADED_MODELS',
                   'OLLAMA_FLASH_ATTENTION', 'OLLAMA_KV_CACHE_TYPE',
                   'OLLAMA_KEEP_ALIVE', 'CUDA_VISIBLE_DEVICES']

        env_table = Table(show_header=False, box=None)
        env_table.add_column("Variable", style="dim")
        env_table.add_column("Value", style="white")

        has_env = False
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                env_table.add_row(var, value)
                has_env = True

        if has_env:
            console.print(Panel(env_table, title="Environment", border_style="dim"))

        # Load prompt
        prompt = self.load_prompt()

        # Select models
        models = self.select_models(self.config.select_pattern)

        if not models:
            console.print("[red]No models found matching criteria[/red]")
            return

        console.print(f"\n[cyan]Selected {len(models)} models for benchmarking[/cyan]")
        console.print("[yellow]Starting live benchmark display...[/yellow]\n")

        # Run benchmarks with live display
        all_results = []
        last_response = None
        last_response_model = None

        # Create initial layout
        initial_layout = self.create_live_layout([], models[0] if models else None)

        with Live(initial_layout, refresh_per_second=2, screen=True) as live:
            prev_model = None
            total_runs = len(models) * self.config.repeat_runs
            completed = 0

            for model_idx, model in enumerate(models):
                # Always stop previous model for consistent benchmarking
                if prev_model:
                    self.stop_model(prev_model)

                for run_idx in range(self.config.repeat_runs):
                    completed += 1
                    run_label = f"Run {run_idx+1}/{self.config.repeat_runs}" if self.config.repeat_runs > 1 else ""
                    progress_bar = self.create_progress_bar(completed, total_runs)
                    progress_text = f"[white]Testing:[/white] {model} {run_label}\n{progress_bar}"

                    # Run the benchmark (streaming or non-streaming)
                    next_model = models[model_idx + 1] if model_idx + 1 < len(models) else None
                    if self.config.enable_streaming:
                        # Pass current last_response to streaming method
                        result = self.run_benchmark_streaming(model, prompt, live, all_results, progress_text, next_model, last_response, last_response_model)
                    else:
                        # Update layout for non-streaming
                        live.update(self.create_live_layout(
                            all_results,
                            model,
                            last_response,
                            progress_text,
                            streaming=False,
                            last_response_model=last_response_model
                        ))
                        result = self.run_benchmark(model, prompt)
                    all_results.append(result)
                    self.results.append(result)

                    # Update last response if successful
                    if result.response_text and not result.error:
                        last_response = result.response_text
                        last_response_model = model

                    # Update layout with completed result
                    progress_bar = self.create_progress_bar(completed, total_runs)
                    progress_text = f"[green]Completed:[/green] {model} {run_label}\n{progress_bar}"
                    live.update(self.create_live_layout(
                        all_results,
                        next_model,
                        last_response,
                        progress_text,
                        streaming=False,
                        last_response_model=last_response_model
                    ))

                    # Brief pause to show result before next test
                    time.sleep(1)

                prev_model = model

        # Show final results
        console.print("\n" + "="*80)
        console.print("[bold green]🎉 Benchmark Complete![/bold green]")
        console.print("="*80 + "\n")

        # Display final results table
        table = self.create_results_table(all_results)
        console.print(table)

        # Calculate and display statistics if multiple runs
        if self.config.repeat_runs > 1:
            self.display_statistics(all_results)

        # Export results
        self.export_results(all_results)

        # Print tips
        console.print("\n[dim]💡 Tip: Use --label and --csv to compare baseline vs optimized runs[/dim]")
        console.print("[dim]📊 Try --repeat-runs for statistical analysis[/dim]")

    def display_statistics(self, results: List[BenchmarkResult]) -> None:
        """Display statistical summary for multiple runs"""
        df = pd.DataFrame([r.to_dict() for r in results if not r.error])

        if df.empty:
            return

        stats_table = Table(
            title="Statistical Summary",
            show_header=True,
            header_style="bold blue"
        )

        stats_table.add_column("Model", style="cyan")
        stats_table.add_column("Metric", style="white")
        stats_table.add_column("Mean", justify="right", style="green")
        stats_table.add_column("Std Dev", justify="right", style="yellow")
        stats_table.add_column("Min", justify="right", style="red")
        stats_table.add_column("Max", justify="right", style="bright_green")

        for model in df['model'].unique():
            model_df = df[df['model'] == model]

            for metric in ['tokens_per_second', 'total_s', 'eval_s']:
                if metric in model_df.columns:
                    values = model_df[metric]
                    stats_table.add_row(
                        model if metric == 'tokens_per_second' else "",
                        metric.replace('_', ' ').title(),
                        f"{values.mean():.2f}",
                        f"{values.std():.2f}",
                        f"{values.min():.2f}",
                        f"{values.max():.2f}"
                    )

        console.print("\n")
        console.print(stats_table)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Enhanced Ollama Model Benchmarking Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Model selection
    model_group = parser.add_argument_group("Model Selection")
    model_group.add_argument(
        'models', nargs='*',
        help='Models to benchmark (positional)'
    )
    model_group.add_argument(
        '-m', '--models', dest='model_list',
        help='Comma-separated list of models'
    )
    model_group.add_argument(
        '-s', '--select',
        help='Select models by regex pattern (use "all" for all models)'
    )

    # Benchmark parameters
    bench_group = parser.add_argument_group("Benchmark Parameters")
    bench_group.add_argument(
        '-p', '--prompt',
        help='Prompt text to use'
    )
    bench_group.add_argument(
        '--prompt-file', type=Path,
        help='File containing prompt text'
    )
    bench_group.add_argument(
        '--num-predict', type=int, default=256,
        help='Number of tokens to generate (default: 256)'
    )
    bench_group.add_argument(
        '--num-ctx', type=int, default=4096,
        help='Context window size (default: 4096)'
    )
    bench_group.add_argument(
        '--temperature', type=float, default=0.2,
        help='Temperature for generation (default: 0.2)'
    )
    bench_group.add_argument(
        '--repeat-runs', type=int, default=1,
        help='Number of times to run each model (default: 1)'
    )

    # Connection settings
    conn_group = parser.add_argument_group("Connection Settings")
    conn_group.add_argument(
        '--host', default='localhost',
        help='Ollama host (default: localhost)'
    )
    conn_group.add_argument(
        '--port', type=int, default=11434,
        help='Ollama port (default: 11434)'
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        '--label',
        help='Label for this benchmark run'
    )
    output_group.add_argument(
        '--csv', dest='csv_output', type=Path,
        help='Export results to CSV file'
    )
    output_group.add_argument(
        '--json', dest='json_output', type=Path,
        help='Export results to JSON file'
    )
    output_group.add_argument(
        '--parquet', dest='parquet_output', type=Path,
        help='Export results to Parquet file'
    )

    # Advanced options
    adv_group = parser.add_argument_group("Advanced Options")
    adv_group.add_argument(
        '--keep-alive', default='2s',
        help='Keep-alive duration for models (default: 2s)'
    )
    adv_group.add_argument(
        '--ollama-bin', default='ollama',
        help='Path to ollama binary (default: ollama)'
    )
    adv_group.add_argument(
        '--config', dest='config_file', type=Path,
        help='Load configuration from YAML file'
    )
    adv_group.add_argument(
        '--no-streaming', dest='enable_streaming', action='store_false',
        help='Disable streaming responses (use static display)'
    )
    adv_group.add_argument(
        '--debug', action='store_true',
        help='Enable debug output'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()

    # Create configuration
    if args.config_file and args.config_file.exists():
        config = BenchmarkConfig.from_yaml(args.config_file)
    else:
        config = BenchmarkConfig()

    # Handle model arguments
    if args.model_list:
        args.models = args.model_list.split(',')
    elif not args.models:
        args.models = []

    # Update select pattern
    if args.select:
        args.select_pattern = args.select
        delattr(args, 'select')

    # Merge command-line arguments
    config.merge_args(args)

    # Run benchmark
    try:
        benchmark = OllamaBenchmark(config)
        benchmark.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Benchmark interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if config.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
