# Ollama Auto Installation Script (CPU Mode)
# For Windows with i5-1155G7 + 16GB RAM

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ollama CPU Mode Installation Script" -ForegroundColor Cyan
Write-Host "For: i5-1155G7 + 16GB RAM" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if Ollama is installed
Write-Host "[Step 1/6] Checking Ollama installation..." -ForegroundColor Yellow
try {
    $version = ollama --version 2>&1
    Write-Host "OK - Ollama already installed: $version" -ForegroundColor Green
    $installed = $true
} catch {
    Write-Host "X - Ollama not installed" -ForegroundColor Red
    $installed = $false
}

# Step 2: Provide download instructions if not installed
if (-not $installed) {
    Write-Host ""
    Write-Host "[Step 2/6] Please download Ollama manually..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Download options:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 1 - Official (Recommended):" -ForegroundColor White
    Write-Host "  Visit: https://ollama.ai/download" -ForegroundColor Cyan
    Write-Host "  Click 'Download for Windows'" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 2 - GitHub:" -ForegroundColor White
    Write-Host "  Visit: https://github.com/ollama/ollama/releases" -ForegroundColor Cyan
    Write-Host "  Download latest OllamaSetup.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 3 - Mirror (For users in China):" -ForegroundColor White
    Write-Host "  Visit: https://ghproxy.com/" -ForegroundColor Cyan
    Write-Host "  Input: https://github.com/ollama/ollama/releases/download/v0.1.26/OllamaSetup.exe" -ForegroundColor White
    Write-Host ""
    
    Write-Host "After downloading, install it and press any key to continue..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    
    # Check again
    try {
        $version = ollama --version 2>&1
        Write-Host "OK - Ollama installed successfully: $version" -ForegroundColor Green
    } catch {
        Write-Host "X - Ollama installation failed, please check" -ForegroundColor Red
        Write-Host "If installed, please restart PowerShell and run this script again" -ForegroundColor Yellow
        exit 1
    }
}

# Step 3: Configure CPU inference environment variables
Write-Host ""
Write-Host "[Step 3/6] Configuring CPU inference environment..." -ForegroundColor Yellow

$env:OLLAMA_GPU = "0"
$env:OLLAMA_MODELS = "D:\ollama_models"
$env:OLLAMA_NUM_PARALLEL = "2"

Write-Host "OK - Environment variables set:" -ForegroundColor Green
Write-Host "  OLLAMA_GPU=0 (Force CPU inference)" -ForegroundColor White
Write-Host "  OLLAMA_MODELS=D:\ollama_models" -ForegroundColor White
Write-Host "  OLLAMA_NUM_PARALLEL=2 (Concurrency)" -ForegroundColor White

# Step 4: Create model storage directory
Write-Host ""
Write-Host "[Step 4/6] Creating model storage directory..." -ForegroundColor Yellow
try {
    New-Item -ItemType Directory -Force -Path "D:\ollama_models" | Out-Null
    Write-Host "OK - Model directory created: D:\ollama_models" -ForegroundColor Green
} catch {
    Write-Host "X - Failed to create directory: $_" -ForegroundColor Red
}

# Step 5: Start Ollama service
Write-Host ""
Write-Host "[Step 5/6] Starting Ollama service..." -ForegroundColor Yellow

$serviceRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $serviceRunning = $true
        Write-Host "OK - Ollama service already running" -ForegroundColor Green
    }
} catch {
    # Service not running
}

if (-not $serviceRunning) {
    Write-Host "Starting Ollama service..." -ForegroundColor Yellow
    
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    
    Write-Host "Waiting for service to start..." -ForegroundColor Yellow
    $maxWait = 10
    $waited = 0
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 1
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "OK - Ollama service started successfully" -ForegroundColor Green
                break
            }
        } catch {
            $waited++
            Write-Host "  Waiting... ($waited/$maxWait)" -ForegroundColor Gray
        }
    }
    
    if ($waited -ge $maxWait) {
        Write-Host "X - Service start timeout, please start manually: ollama serve" -ForegroundColor Red
    }
}

# Step 6: Download model
Write-Host ""
Write-Host "[Step 6/6] Downloading Qwen 1.8B model..." -ForegroundColor Yellow
Write-Host "Model size: ~1.5GB, suitable for CPU inference" -ForegroundColor Cyan
Write-Host ""

try {
    ollama pull qwen:1.8b
    Write-Host "OK - Model downloaded successfully" -ForegroundColor Green
} catch {
    Write-Host "X - Model download failed: $_" -ForegroundColor Red
    Write-Host "Please download manually: ollama pull qwen:1.8b" -ForegroundColor Yellow
}

# Verification
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Installed models:" -ForegroundColor Yellow
ollama list

Write-Host ""
Write-Host "Testing model..." -ForegroundColor Yellow
Write-Host "Input: Hello, please introduce Linux kernel in one sentence" -ForegroundColor Cyan
Write-Host ""

$testResponse = ollama run qwen:1.8b "Hello, please introduce Linux kernel in one sentence" 2>&1
Write-Host "Model response: $testResponse" -ForegroundColor White

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test system: python test_local_llm.py" -ForegroundColor White
Write-Host "2. Get cases: python verify_phase1.py" -ForegroundColor White
Write-Host "3. View docs: type OLLAMA_CPU_DEPLOYMENT.md" -ForegroundColor White

Write-Host ""
Write-Host "Usage example:" -ForegroundColor Cyan
Write-Host "  from cases.acquisition.llm_parser import LLMParser" -ForegroundColor White
Write-Host "  parser = LLMParser(llm_type='ollama', model='qwen:1.8b')" -ForegroundColor White
Write-Host "  case_data = parser.parse(content, use_llm=True)" -ForegroundColor White

Write-Host ""
Write-Host "Expected performance:" -ForegroundColor Cyan
Write-Host "  - Memory usage: ~2GB" -ForegroundColor White
Write-Host "  - Inference speed: ~2-3 seconds/case" -ForegroundColor White
Write-Host "  - Accuracy: ~85%" -ForegroundColor White

Write-Host ""
Write-Host "Note: Ensure Ollama service is running before use (ollama serve)" -ForegroundColor Yellow