# Results summary (synthetic data only; safe to share)

runs: 1854, errored/excluded: 0

ASR/LTCR/FRR = rate [Wilson 95% CI] n.  Bootstrap CIs are in the CSV files.


## by_model_config

| model | config | ASR | PropUnauth | LTCR | FRR |
|---|---|---|---|---|---|
| ollama:llama3.1:8b | prompt_only | 67.1% [60.9, 72.7] n=240 | 67.1% [60.9, 72.7] n=240 | 100.0% [94.7,100.0] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:llama3.1:8b | rbac | 0.0% [ 0.0,  1.6] n=240 | 9.2% [ 6.1, 13.5] n=240 | 95.7% [88.0, 98.5] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:llama3.1:8b | strict_schema | 9.2% [ 6.1, 13.5] n=240 | 9.2% [ 6.1, 13.5] n=240 | 95.7% [88.0, 98.5] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:qwen2.5:7b | prompt_only | 70.8% [64.8, 76.2] n=240 | 70.8% [64.8, 76.2] n=240 | 100.0% [94.7,100.0] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:qwen2.5:7b | rbac | 0.0% [ 0.0,  1.6] n=240 | 39.2% [33.2, 45.5] n=240 | 100.0% [94.7,100.0] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:qwen2.5:7b | strict_schema | 39.6% [33.6, 45.9] n=240 | 39.6% [33.6, 45.9] n=240 | 100.0% [94.7,100.0] n=69 | 0.0% [ 0.0,  5.3] n=69 |

## by_category

| model | config | category | ASR | PropUnauth | LTCR | FRR |
|---|---|---|---|---|---|---|
| ollama:llama3.1:8b | prompt_only | benign | - | - | 100.0% [94.7,100.0] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:llama3.1:8b | prompt_only | direct | 95.0% [86.3, 98.3] n=60 | 95.0% [86.3, 98.3] n=60 | - | - |
| ollama:llama3.1:8b | prompt_only | indirect | 20.0% [11.8, 31.8] n=60 | 20.0% [11.8, 31.8] n=60 | - | - |
| ollama:llama3.1:8b | prompt_only | multistep | 71.1% [56.6, 82.3] n=45 | 71.1% [56.6, 82.3] n=45 | - | - |
| ollama:llama3.1:8b | prompt_only | obfuscation | 80.0% [69.6, 87.5] n=75 | 80.0% [69.6, 87.5] n=75 | - | - |
| ollama:llama3.1:8b | rbac | benign | - | - | 95.7% [88.0, 98.5] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:llama3.1:8b | rbac | direct | 0.0% [ 0.0,  6.0] n=60 | 0.0% [ 0.0,  6.0] n=60 | - | - |
| ollama:llama3.1:8b | rbac | indirect | 0.0% [ 0.0,  6.0] n=60 | 5.0% [ 1.7, 13.7] n=60 | - | - |
| ollama:llama3.1:8b | rbac | multistep | 0.0% [ 0.0,  7.9] n=45 | 0.0% [ 0.0,  7.9] n=45 | - | - |
| ollama:llama3.1:8b | rbac | obfuscation | 0.0% [ 0.0,  4.9] n=75 | 25.3% [16.9, 36.2] n=75 | - | - |
| ollama:llama3.1:8b | strict_schema | benign | - | - | 95.7% [88.0, 98.5] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:llama3.1:8b | strict_schema | direct | 0.0% [ 0.0,  6.0] n=60 | 0.0% [ 0.0,  6.0] n=60 | - | - |
| ollama:llama3.1:8b | strict_schema | indirect | 5.0% [ 1.7, 13.7] n=60 | 5.0% [ 1.7, 13.7] n=60 | - | - |
| ollama:llama3.1:8b | strict_schema | multistep | 0.0% [ 0.0,  7.9] n=45 | 0.0% [ 0.0,  7.9] n=45 | - | - |
| ollama:llama3.1:8b | strict_schema | obfuscation | 25.3% [16.9, 36.2] n=75 | 25.3% [16.9, 36.2] n=75 | - | - |
| ollama:qwen2.5:7b | prompt_only | benign | - | - | 100.0% [94.7,100.0] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:qwen2.5:7b | prompt_only | direct | 95.0% [86.3, 98.3] n=60 | 95.0% [86.3, 98.3] n=60 | - | - |
| ollama:qwen2.5:7b | prompt_only | indirect | 33.3% [22.7, 45.9] n=60 | 33.3% [22.7, 45.9] n=60 | - | - |
| ollama:qwen2.5:7b | prompt_only | multistep | 80.0% [66.2, 89.1] n=45 | 80.0% [66.2, 89.1] n=45 | - | - |
| ollama:qwen2.5:7b | prompt_only | obfuscation | 76.0% [65.2, 84.2] n=75 | 76.0% [65.2, 84.2] n=75 | - | - |
| ollama:qwen2.5:7b | rbac | benign | - | - | 100.0% [94.7,100.0] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:qwen2.5:7b | rbac | direct | 0.0% [ 0.0,  6.0] n=60 | 65.0% [52.4, 75.8] n=60 | - | - |
| ollama:qwen2.5:7b | rbac | indirect | 0.0% [ 0.0,  6.0] n=60 | 8.3% [ 3.6, 18.1] n=60 | - | - |
| ollama:qwen2.5:7b | rbac | multistep | 0.0% [ 0.0,  7.9] n=45 | 31.1% [19.5, 45.7] n=45 | - | - |
| ollama:qwen2.5:7b | rbac | obfuscation | 0.0% [ 0.0,  4.9] n=75 | 48.0% [37.1, 59.1] n=75 | - | - |
| ollama:qwen2.5:7b | strict_schema | benign | - | - | 100.0% [94.7,100.0] n=69 | 0.0% [ 0.0,  5.3] n=69 |
| ollama:qwen2.5:7b | strict_schema | direct | 65.0% [52.4, 75.8] n=60 | 65.0% [52.4, 75.8] n=60 | - | - |
| ollama:qwen2.5:7b | strict_schema | indirect | 10.0% [ 4.7, 20.1] n=60 | 10.0% [ 4.7, 20.1] n=60 | - | - |
| ollama:qwen2.5:7b | strict_schema | multistep | 31.1% [19.5, 45.7] n=45 | 31.1% [19.5, 45.7] n=45 | - | - |
| ollama:qwen2.5:7b | strict_schema | obfuscation | 48.0% [37.1, 59.1] n=75 | 48.0% [37.1, 59.1] n=75 | - | - |

## by_role

| model | config | role | ASR | PropUnauth | LTCR | FRR |
|---|---|---|---|---|---|---|
| ollama:llama3.1:8b | prompt_only | admin | - | - | 100.0% [89.6,100.0] n=33 | 0.0% [ 0.0, 10.4] n=33 |
| ollama:llama3.1:8b | prompt_only | analyst | 59.4% [49.4, 68.7] n=96 | 59.4% [49.4, 68.7] n=96 | 100.0% [84.5,100.0] n=21 | 0.0% [ 0.0, 15.5] n=21 |
| ollama:llama3.1:8b | prompt_only | guest | 72.2% [64.4, 78.9] n=144 | 72.2% [64.4, 78.9] n=144 | 100.0% [79.6,100.0] n=15 | 0.0% [ 0.0, 20.4] n=15 |
| ollama:llama3.1:8b | rbac | admin | - | - | 100.0% [89.6,100.0] n=33 | 0.0% [ 0.0, 10.4] n=33 |
| ollama:llama3.1:8b | rbac | analyst | 0.0% [ 0.0,  3.8] n=96 | 9.4% [ 5.0, 16.9] n=96 | 100.0% [84.5,100.0] n=21 | 0.0% [ 0.0, 15.5] n=21 |
| ollama:llama3.1:8b | rbac | guest | 0.0% [ 0.0,  2.6] n=144 | 9.0% [ 5.4, 14.8] n=144 | 80.0% [54.8, 93.0] n=15 | 0.0% [ 0.0, 20.4] n=15 |
| ollama:llama3.1:8b | strict_schema | admin | - | - | 100.0% [89.6,100.0] n=33 | 0.0% [ 0.0, 10.4] n=33 |
| ollama:llama3.1:8b | strict_schema | analyst | 9.4% [ 5.0, 16.9] n=96 | 9.4% [ 5.0, 16.9] n=96 | 100.0% [84.5,100.0] n=21 | 0.0% [ 0.0, 15.5] n=21 |
| ollama:llama3.1:8b | strict_schema | guest | 9.0% [ 5.4, 14.8] n=144 | 9.0% [ 5.4, 14.8] n=144 | 80.0% [54.8, 93.0] n=15 | 0.0% [ 0.0, 20.4] n=15 |
| ollama:qwen2.5:7b | prompt_only | admin | - | - | 100.0% [89.6,100.0] n=33 | 0.0% [ 0.0, 10.4] n=33 |
| ollama:qwen2.5:7b | prompt_only | analyst | 77.1% [67.7, 84.4] n=96 | 77.1% [67.7, 84.4] n=96 | 100.0% [84.5,100.0] n=21 | 0.0% [ 0.0, 15.5] n=21 |
| ollama:qwen2.5:7b | prompt_only | guest | 66.7% [58.6, 73.8] n=144 | 66.7% [58.6, 73.8] n=144 | 100.0% [79.6,100.0] n=15 | 0.0% [ 0.0, 20.4] n=15 |
| ollama:qwen2.5:7b | rbac | admin | - | - | 100.0% [89.6,100.0] n=33 | 0.0% [ 0.0, 10.4] n=33 |
| ollama:qwen2.5:7b | rbac | analyst | 0.0% [ 0.0,  3.8] n=96 | 45.8% [36.2, 55.8] n=96 | 100.0% [84.5,100.0] n=21 | 0.0% [ 0.0, 15.5] n=21 |
| ollama:qwen2.5:7b | rbac | guest | 0.0% [ 0.0,  2.6] n=144 | 34.7% [27.4, 42.8] n=144 | 100.0% [79.6,100.0] n=15 | 0.0% [ 0.0, 20.4] n=15 |
| ollama:qwen2.5:7b | strict_schema | admin | - | - | 100.0% [89.6,100.0] n=33 | 0.0% [ 0.0, 10.4] n=33 |
| ollama:qwen2.5:7b | strict_schema | analyst | 44.8% [35.2, 54.7] n=96 | 44.8% [35.2, 54.7] n=96 | 100.0% [84.5,100.0] n=21 | 0.0% [ 0.0, 15.5] n=21 |
| ollama:qwen2.5:7b | strict_schema | guest | 36.1% [28.7, 44.2] n=144 | 36.1% [28.7, 44.2] n=144 | 100.0% [79.6,100.0] n=15 | 0.0% [ 0.0, 20.4] n=15 |
