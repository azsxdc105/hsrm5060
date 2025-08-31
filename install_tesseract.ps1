# PowerShell script to download and install Tesseract OCR
Write-Host "Installing Tesseract OCR..." -ForegroundColor Green

# Create temp directory
$tempDir = "$env:TEMP\TesseractInstall"
if (!(Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force
}

# Download Tesseract installer
$tesseractUrl = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.0.20221214/tesseract-ocr-w64-setup-5.3.0.20221214.exe"
$installerPath = "$tempDir\tesseract-installer.exe"

Write-Host "Downloading Tesseract installer..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $tesseractUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "Download completed!" -ForegroundColor Green
} catch {
    Write-Host "Failed to download Tesseract installer: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Install Tesseract silently
Write-Host "Installing Tesseract..." -ForegroundColor Yellow
try {
    Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait
    Write-Host "Tesseract installation completed!" -ForegroundColor Green
} catch {
    Write-Host "Failed to install Tesseract: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Add to PATH
$tesseractPath = "C:\Program Files\Tesseract-OCR"
if (Test-Path $tesseractPath) {
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentPath -notlike "*$tesseractPath*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$tesseractPath", "User")
        Write-Host "Added Tesseract to PATH" -ForegroundColor Green
    }
    
    # Update current session PATH
    $env:PATH += ";$tesseractPath"
    
    # Test installation
    Write-Host "Testing Tesseract installation..." -ForegroundColor Yellow
    try {
        & "$tesseractPath\tesseract.exe" --version
        Write-Host "Tesseract is working correctly!" -ForegroundColor Green
    } catch {
        Write-Host "Tesseract test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "Tesseract installation directory not found!" -ForegroundColor Red
}

# Clean up
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Installation process completed!" -ForegroundColor Green
Write-Host "Please restart your terminal/IDE to use Tesseract OCR." -ForegroundColor Yellow