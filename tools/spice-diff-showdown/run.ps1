param([Parameter(Mandatory=$true)][string]$Ver)
# Referee script: run ACCEPTANCE five cases + determinism + JSON contract for one entry.
# Usage:  powershell -File run.ps1 -Ver A     (A = Codex, B = Hermes)
$base = "C:\Users\hp\Documents\ClawChat\deepseek_harness\spice-diff"
$ex   = Join-Path $base "examples"
$exe  = Join-Path $env:TEMP "referee-$Ver\Scripts\spdiff.exe"
if (-not (Test-Path $exe)) { Write-Error "no installed build for $Ver"; exit 9 }

function RC([array]$a) {
  $o = & $exe @a 2>&1
  [pscustomobject]@{ rc = $LASTEXITCODE; out = ($o -join "`n") }
}

$cases = @(
  @{ n='pair_a';           a=@("$ex\pair_a_before.sp","$ex\pair_a_after.sp");     want=0 }
  @{ n='pair_b';           a=@("$ex\pair_b_before.sp","$ex\pair_b_after.sp");     want=1 }
  @{ n='pair_c';           a=@("$ex\pair_c_before.sp","$ex\pair_c_after.sp");     want=1 }
  @{ n='pair_d';           a=@("$ex\pair_d_before.sp","$ex\pair_d_after.sp");     want=2 }
  @{ n='error_bad_syntax'; a=@("$ex\error_bad_syntax.sp","$ex\pair_a_after.sp");  want=3 }
)
foreach ($c in $cases) {
  $r = RC $c.a
  # A stub that happens to return rc=3 must NOT count as a pass (error_bad_syntax false hit).
  $stub = $r.out -match 'not implemented'
  $ok = if (($r.rc -eq $c.want) -and -not $stub) { 'PASS' } else { 'FAIL' }
  "{0,-18} want rc={1}  got rc={2}  {3}" -f $c.n, $c.want, $r.rc, $ok
  "    first line: " + (($r.out -split "`n")[0])
}

$b1 = RC @("$ex\pair_b_before.sp","$ex\pair_b_after.sp")
$b2 = RC @("$ex\pair_b_before.sp","$ex\pair_b_after.sp")
"DETERMINISM pair_b twice : " + $(if ($b1.out -ceq $b2.out) { 'PASS' } else { 'FAIL' })

$j = RC @("$ex\pair_b_before.sp","$ex\pair_b_after.sp","--json")
$keys = 'n/a'
if ($j.rc -in 0,1,2) {
  try { $keys = ((($j.out | ConvertFrom-Json).PSObject.Properties.Name) -join ',') } catch { $keys = 'UNPARSEABLE' }
}
"JSON rc={0}  top-level keys = {1}" -f $j.rc, $keys
