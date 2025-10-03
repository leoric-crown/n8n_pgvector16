# Context Window Matrix Testing

Automated benchmark testing across multiple context window sizes.

## Quick Start

```bash
# Run the full matrix (uses context_matrix.yaml)
./run_matrix.py

# Dry run to see what commands would be executed
./run_matrix.py --dry-run

# Use custom configuration file
./run_matrix.py --config my_matrix.yaml
```

## Configuration File: `context_matrix.yaml`

### Structure

```yaml
matrix:
  # Context window sizes to test (in tokens)
  context_sizes:
    - 8192      # 8K
    - 16384     # 16K
    - 32768     # 32K
    - 65536     # 64K
    - 102400    # 100K

  # Models to test - explicit list
  models:
    - phi4-mini:3.8b
    - gemma3:4b
    - deepseek-r1:8b

  # OR use pattern matching
  # model_pattern: "deepseek|gemma"

benchmark:
  num_predict: 1024      # Tokens to generate per test
  temperature: 0.2
  repeat_runs: 1
  keep_alive: "2s"
  mem_split: true

connection:
  host: localhost
  port: 11434

output:
  label_template: "ctx-{context}"
  formats:
    - csv
    - json
  output_dir: "./results"
  filename_template: "benchmark-{context}k-{timestamp}"

advanced:
  debug: false
  stop_between_contexts: true
  stop_between_models: true
```

## Matrix Configuration

### Context Sizes

Test from 8K up to 100K tokens (100 * 1024 = 102,400):

```yaml
context_sizes:
  - 8192      # 8K  - small context
  - 16384     # 16K - medium context
  - 32768     # 32K - large context
  - 65536     # 64K - very large context
  - 102400    # 100K - maximum context (100 * 1024)
```

### Model Selection

#### Option 1: Explicit list

```yaml
models:
  - phi4-mini:3.8b
  - gemma3:4b
  - deepseek-r1:8b
```

#### Option 2: Pattern matching

```yaml
model_pattern: "deepseek|gemma|phi4"
```

#### Option 3: All available models

```yaml
model_pattern: "all"
```

### Output Configuration

Files are generated using templates:

```yaml
output_dir: "./results"
filename_template: "benchmark-{context}k-{timestamp}"
label_template: "ctx-{context}"
```

**Example output files:**

- `results/benchmark-8k-20250930-120000.csv`
- `results/benchmark-16k-20250930-120500.json`
- `results/benchmark-32k-20250930-121000.csv`

### Supported Formats

- **CSV**: Best for spreadsheet analysis and plotting
- **JSON**: Structured data for programmatic processing
- **Parquet**: Efficient columnar format (requires pyarrow)

```yaml
formats:
  - csv
  - json
  - parquet
```

## Usage Examples

### Basic Matrix Test

```bash
# Test all context sizes with default models
./run_matrix.py
```

### Dry Run (Preview Commands)

```bash
# See what would be executed without running
./run_matrix.py --dry-run
```

### Custom Configuration

```bash
# Use a different configuration file
./run_matrix.py --config custom_matrix.yaml
```

### Quick Matrix Templates

**Small models, quick test:**

```yaml
matrix:
  context_sizes: [8192, 16384, 32768]
  models: [phi4-mini:3.8b, gemma3:4b]
benchmark:
  num_predict: 512
  repeat_runs: 1
```

**Large context stress test:**

```yaml
matrix:
  context_sizes: [32768, 65536, 102400]
  models: [deepseek-r1:8b, qwen3:8b]
benchmark:
  num_predict: 1024
  repeat_runs: 3
```

**All models, all contexts:**

```yaml
matrix:
  context_sizes: [8192, 16384, 32768, 65536, 102400]
  model_pattern: "all"
benchmark:
  num_predict: 1024
  repeat_runs: 1
```

## Understanding Results

### Output Files

Each context size generates separate files:

```text
results/
├── benchmark-8k-20250930-120000.csv
├── benchmark-8k-20250930-120000.json
├── benchmark-16k-20250930-120100.csv
├── benchmark-16k-20250930-120100.json
├── benchmark-32k-20250930-120200.csv
└── ...
```

### CSV Format

```csv
model,timestamp,preloaded,tokens,load_s,eval_s,tokens_per_second,context_length,label,...
phi4-mini:3.8b,2025-09-30T12:00:00,False,1024,0.123,6.234,164.2,8192,ctx-8k,...
```

### Analyzing Results

**Combine all results:**

```bash
# Concatenate all CSV files
cat results/benchmark-*.csv | grep -v "^model," | \
  cat <(head -1 results/benchmark-8k-*.csv) - > combined_results.csv
```

**Plot performance vs context size:**

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('combined_results.csv')
for model in df['model'].unique():
    data = df[df['model'] == model]
    plt.plot(data['context_length'], data['tokens_per_second'], label=model)
plt.xlabel('Context Size (tokens)')
plt.ylabel('Tokens/Second')
plt.legend()
plt.savefig('context_performance.png')
```

## Advanced Options

### Stop Between Tests

Clean memory between tests:

```yaml
advanced:
  stop_between_contexts: true   # Stop models when changing context size
  stop_between_models: true     # Stop models when changing model
  cold_start: true              # Unload all models before starting
```

### Custom Prompts

Use a custom prompt for all tests:

```yaml
prompt_file: /path/to/prompt.md
# OR
prompt: "Your custom prompt text here"
```

### Debug Mode

Enable verbose output:

```yaml
advanced:
  debug: true
```

## Best Practices

1. **Start Small**: Test with smaller context sizes first
2. **Use Repeat Runs**: Add `repeat_runs: 3` for statistical analysis
3. **Monitor Resources**: Watch GPU/RAM usage during large context tests
4. **Stop Between Tests**: Enable `stop_between_contexts` for clean benchmarks
5. **Label Your Runs**: Use meaningful labels for comparison

## Troubleshooting

**Matrix runner not found:**

```bash
# Ensure you're in the benchmark directory
cd ollama/benchmark
```

**Models not loading:**

```bash
# Check Ollama is running
ollama ps

# Test manual benchmark first
python benchmark_models.py --num-ctx 8192
```

**Out of memory errors:**

```bash
# Reduce context sizes or use smaller models
# Enable model stopping between tests
```

**Configuration errors:**

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('context_matrix.yaml'))"
```

## Example Workflow

```bash
# 1. Review configuration
cat context_matrix.yaml

# 2. Dry run to preview
./run_matrix.py --dry-run

# 3. Run matrix
./run_matrix.py

# 4. Check results
ls -lh results/

# 5. Analyze
python -c "
import pandas as pd
df = pd.read_csv('results/benchmark-8k-*.csv')
print(df.groupby('model')['tokens_per_second'].describe())
"
```

## Tips

- Use `--label` to differentiate between baseline and optimized runs
- Export to multiple formats for flexibility
- Test incrementally: start with 1-2 context sizes
- Monitor system resources during large context tests
- Combine results from multiple runs for statistical significance
