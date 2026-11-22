$ErrorActionPreference = "Stop"

$texPath = "c:\KHDL K46\TTS\report\main.tex"
$bibPath = "c:\KHDL K46\TTS\report\references.bib"
$pdfPath = "c:\KHDL K46\TTS\report\main.pdf"
$namedPdfPath = "c:\KHDL K46\TTS\report\Tieu_Luan_Text_to_SQL_Cai_Minh_Duy_4654110003.pdf"

$texContent = Get-Content -Raw -Encoding UTF8 $texPath
$bibContent = Get-Content -Raw -Encoding UTF8 $bibPath

# 1. Verify required files and PDF header
foreach ($p in @($texPath, $bibPath, $pdfPath, $namedPdfPath)) {
    if (-not (Test-Path $p)) {
        Write-Error "Missing required output file: $p"
        exit 1
    }
}

$pdfBytes = [System.IO.File]::ReadAllBytes($pdfPath)
$pdfHeader = [System.Text.Encoding]::ASCII.GetString($pdfBytes, 0, 5)
if ($pdfHeader -ne "%PDF-") {
    Write-Error "Invalid PDF header in $pdfPath : $pdfHeader"
    exit 1
}

# 2. Verify balanced \begin{env} and \end{env}
$beginMatches = [regex]::Matches($texContent, '\\begin\{([^}]+)\}')
$endMatches   = [regex]::Matches($texContent, '\\end\{([^}]+)\}')

if ($beginMatches.Count -ne $endMatches.Count) {
    Write-Error "Mismatch between \begin count ($($beginMatches.Count)) and \end count ($($endMatches.Count))"
    exit 1
}

$stack = New-Object System.Collections.Generic.Stack[string]
$tokenMatches = [regex]::Matches($texContent, '\\(begin|end)\{([^}]+)\}')
foreach ($m in $tokenMatches) {
    $type = $m.Groups[1].Value
    $env  = $m.Groups[2].Value
    if ($type -eq "begin") {
        $stack.Push($env)
    } else {
        if ($stack.Count -eq 0) {
            Write-Error "Unexpected \end{$env} with empty stack"
            exit 1
        }
        $top = $stack.Pop()
        if ($top -ne $env) {
            Write-Error "Environment mismatch: expected \end{$top} but found \end{$env}"
            exit 1
        }
    }
}
if ($stack.Count -ne 0) {
    Write-Error "Unclosed LaTeX environments remaining on stack: $($stack -join ', ')"
    exit 1
}

# 3. Verify all \cite{...} keys exist in references.bib
$citeMatches = [regex]::Matches($texContent, '\\cite\{([^}]+)\}')
$uniqueKeys = New-Object System.Collections.Generic.HashSet[string]
foreach ($cm in $citeMatches) {
    $keys = $cm.Groups[1].Value -split ','
    foreach ($k in $keys) {
        $trimmed = $k.Trim()
        [void]$uniqueKeys.Add($trimmed)
        if ($bibContent -notmatch [regex]::Escape($trimmed)) {
            Write-Error "Citation key '$trimmed' used in main.tex not found in references.bib"
            exit 1
        }
    }
}

$lineCount = (Get-Content -Encoding UTF8 $texPath).Count
Write-Output "Verified LaTeX & Compiled PDF:"
Write-Output " - Total lines in report/main.tex: $lineCount"
Write-Output " - Balanced \begin/\end environments: $($beginMatches.Count) pairs"
Write-Output " - Verified unique citation keys: $($uniqueKeys.Count)"
Write-Output " - Compiled PDF size: $($pdfBytes.Length) bytes ($pdfHeader)"
Write-Output "PASS: All LaTeX and PDF verification checks succeeded."
