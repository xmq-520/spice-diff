<#
.SYNOPSIS
  spice-diff one-shot self check (owned by dsh).
.DESCRIPTION
  Three stages: build/install -> unit+golden tests -> e2e against Hermes' examples/.
  Machine facts hard-coded from measurement (see PLAN.md 4/6 and tasks/M0-dsh.md):
    1) use the repo-local .venv, not system Python (no wheel, site-packages not writable)
    2) pip must run with --no-build-isolation --no-cache-dir
       (build isolation hangs reaching pypi.org; pip wheel cache dir is denied by the sandbox)
    3) the shared dir is readable but read-only for dsh, so examples/ is read from there, never copied

  Before M1 (core not implemented) stage 3 MUST fail - that is the expected result, not a broken script.
  Pass/fail rules: README.md section 5 + PLAN.md section 3.

  NOTE: this file is deliberately ASCII-only. Windows PowerShell 5.1 reads
  .ps1 without a BOM as ANSI, so non-ASCII literals here would break parsing.
#>
[CmdletBinding()]
param(
    [string]$Shared = $env:SPICE_DIFF_SHARED,
    [switch]$SkipInstall,
    [switch]$RepoExamples
)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
if (-not $Shared) { $Shared = 'C:\Users\hp\Documents\ClawChat\shared\spice-diff' }
if ($RepoExamples) { $Shared = $Repo }
$Py = Join-Path $Repo '.venv\Scripts\python.exe'
$Exe = Join-Path $Repo '.venv\Scripts\spdiff.exe'
$env:PIP_NO_CACHE_DIR = '1'

$results = New-Object System.Collections.ArrayList

function Step {
    param([string]$Name, [scriptblock]$Body)
    Write-Host ''
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    try {
        . $Body
        Write-Host "--- $Name : PASS" -ForegroundColor Green
        [void]$results.Add($true)
    } catch {
        Write-Host "--- $Name : FAIL  $($_.Exception.Message)" -ForegroundColor Red
        [void]$results.Add($false)
    }
}

# ---------- 1. build + install ----------
if ($SkipInstall) {
    Write-Host '=== install : SKIPPED (-SkipInstall) ===' -ForegroundColor Yellow
    [void]$results.Add($true)
} else {
    Step 'install' {
        if (-not (Test-Path $Py)) { throw 'missing .venv: run  python -m venv .venv ; then pip install setuptools wheel' }
        & $Py -m pip install --no-index --no-build-isolation --disable-pip-version-check -q $Repo
        if ($LASTEXITCODE -ne 0) { throw "pip install . exited $LASTEXITCODE" }
    }
}

# ---------- 2. tests ----------
Step 'unittest (tests/unit)' {
    & $Py -m unittest discover -s (Join-Path $Repo 'tests\unit') -t $Repo
    if ($LASTEXITCODE -ne 0) { throw "unittest exited $LASTEXITCODE" }
}

Step 'golden (tests/golden)' {
    $g = Join-Path $Repo 'tests\golden'
    $runner = @(Get-ChildItem $g -Filter 'test_*.py' -ErrorAction SilentlyContinue)
    if ($runner.Count -eq 0) {
        Write-Host '  no golden runner yet (OpenCode, M3) - skipped'
        return
    }
    & $Py -m unittest discover -s $g -t $Repo
    if ($LASTEXITCODE -ne 0) { throw "golden exited $LASTEXITCODE" }
}

# ---------- 3. e2e against shared examples/ ----------
Step 'e2e examples (shared)' {
    $ex = Join-Path $Shared 'examples'
    if (-not (Test-Path $ex)) { throw "shared examples not found: $ex (set -Shared or SPICE_DIFF_SHARED)" }
    if (-not (Test-Path $Exe)) { throw "spdiff entry point not found: $Exe" }

    # expected exit codes: README section 5 + examples/expected_*.md
    $cases = @(
        [pscustomobject]@{ n = 'pair_a'; code = 0; note = 'zero diff - ANY diff = false positive = FAIL' },
        [pscustomobject]@{ n = 'pair_b'; code = 1; note = 'must match expected_b.md line by line' },
        [pscustomobject]@{ n = 'pair_c'; code = 1; note = 'scope=buf, hierarchy must not be flattened' },
        [pscustomobject]@{ n = 'pair_d'; code = 2; note = 'uncertain: refdes=null + candidates' }
    )
    $schema = @('tool', 'version', 'summary', 'changes', 'exit_code')
    $bad = New-Object System.Collections.ArrayList

    # Core-unimplemented sentinel (src/spice_diff/cli.py). While the core is absent
    # every case legitimately exits 3; reporting that as four schema failures would
    # hide the real message. Detect it once and fail the stage with one clean line.
    # NOTE: ErrorActionPreference is Stop, so a native command writing to stderr must
    # be probed inside try/catch - otherwise the call raises before we can read $LASTEXITCODE.
    $probe = ''
    try { $probe = (& $Exe (Join-Path $ex 'pair_a_before.sp') (Join-Path $ex 'pair_a_after.sp') 2>&1 | Out-String) } catch { $probe = $_.Exception.Message }
    if ($probe -match 'spdiff [0-9.]+: core not implemented') { throw 'core not implemented yet (M1, Codex) - e2e cannot run' }

    foreach ($c in $cases) {
        $b = Join-Path $ex ($c.n + '_before.sp')
        $a = Join-Path $ex ($c.n + '_after.sp')
        if (-not (Test-Path $b) -or -not (Test-Path $a)) {
            [void]$bad.Add($c.n + ': missing input netlist')
            continue
        }

        $md1 = ''
        $md2 = ''
        try { $md1 = (& $Exe $b $a 2>&1 | Out-String) } catch { $md1 = $_.Exception.Message }
        $rc1 = $LASTEXITCODE
        try { $md2 = (& $Exe $b $a 2>&1 | Out-String) } catch { $md2 = $_.Exception.Message }
        $rc2 = $LASTEXITCODE
        $j1 = ''
        try { $j1 = (& $Exe $b $a --json 2>&1 | Out-String) } catch { $j1 = '' }

        if ($rc1 -ne $c.code) { [void]$bad.Add($c.n + ': exit ' + $rc1 + ', expected ' + $c.code) }
        if ($rc2 -ne $rc1) { [void]$bad.Add($c.n + ': exit code differs between runs') }
        if ($md1 -ne $md2) { [void]$bad.Add($c.n + ': output not byte-identical across runs') }

        if ($j1) {
            try {
                $o = $j1 | ConvertFrom-Json
                $names = @($o.PSObject.Properties.Name)
                foreach ($k in $schema) {
                    if ($names -notcontains $k) { [void]$bad.Add($c.n + ': JSON missing field ' + $k) }
                }
                $extra = @($names | Where-Object { $schema -notcontains $_ })
                if ($extra.Count) { [void]$bad.Add($c.n + ': JSON extra field(s) ' + ($extra -join ',') + ' - adding fields = FAIL') }
                if ($o.exit_code -ne $rc1) { [void]$bad.Add($c.n + ': JSON exit_code ' + $o.exit_code + ' != actual ' + $rc1) }
            } catch {
                [void]$bad.Add($c.n + ': --json output is not valid JSON')
            }
        }
        Write-Host ('  {0}: rc={1} (want {2})  {3}' -f $c.n, $rc1, $c.code, $c.note)
    }

    # negative case: bad syntax must exit 3, never silently emit a report
    $badFile = Join-Path $ex 'error_bad_syntax.sp'
    if (Test-Path $badFile) {
        try { & $Exe $badFile $badFile 2>&1 | Out-Null } catch { }
        if ($LASTEXITCODE -ne 3) { [void]$bad.Add('error_bad_syntax: exit ' + $LASTEXITCODE + ', expected 3') }
        Write-Host ('  error_bad_syntax: rc={0} (want 3)' -f $LASTEXITCODE)
    }

    if ($bad.Count) { throw ($bad -join ' | ') }
}

# ---------- summary ----------
$failed = @($results | Where-Object { -not $_ }).Count
$total = $results.Count
$ok = $total - $failed
if ($failed) {
    Write-Host ''
    Write-Host ("=== SUMMARY: {0}/{1} stages passed ===" -f $ok, $total) -ForegroundColor Red
    exit 1
} else {
    Write-Host ''
    Write-Host ("=== SUMMARY: {0}/{1} stages passed ===" -f $ok, $total) -ForegroundColor Green
    exit 0
}
