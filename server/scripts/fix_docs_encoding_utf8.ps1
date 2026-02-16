$ErrorActionPreference = "Stop"

$targets = @(
  "docs/99_MASTER_CHECKPOINT.md",
  "docs/01_DECISIONS.md"
)

function Replace-Bytes([byte[]]$data, [byte[]]$from, [byte[]]$to) {
  $ms = New-Object System.IO.MemoryStream
  $i = 0
  while ($i -le $data.Length - $from.Length) {
    $match = $true
    for ($j = 0; $j -lt $from.Length; $j++) {
      if ($data[$i + $j] -ne $from[$j]) { $match = $false; break }
    }
    if ($match) {
      $ms.Write($to, 0, $to.Length) | Out-Null
      $i += $from.Length
    } else {
      $ms.WriteByte($data[$i])
      $i++
    }
  }
  # rest
  while ($i -lt $data.Length) { $ms.WriteByte($data[$i]); $i++ }
  return $ms.ToArray()
}

# from = UTF-8 bytes of mojibake sequences (e.g. "???"), to = UTF-8 bytes of intended chars (e.g. "?")
$map = @(
  @{ from = [byte[]](0xC3,0xA2,0xE2,0x82,0xAC,0xE2,0x80,0x93); to = [byte[]](0xE2,0x80,0x93) }, # ??? -> ?
  @{ from = [byte[]](0xC3,0xA2,0xE2,0x82,0xAC,0xE2,0x80,0x94); to = [byte[]](0xE2,0x80,0x94) }, # ??? -> ?
  @{ from = [byte[]](0xC3,0xA2,0xE2,0x82,0xAC,0xC5,0xBE);       to = [byte[]](0xE2,0x80,0x9E) }, # ??? -> ?
  @{ from = [byte[]](0xC3,0xA2,0xE2,0x82,0xAC,0xC5,0x93);       to = [byte[]](0xE2,0x80,0x9C) }, # ??? -> ?
  @{ from = [byte[]](0xC3,0xA2,0xE2,0x82,0xAC,0xC5,0x9D);       to = [byte[]](0xE2,0x80,0x9D) }, # ?? -> ?
  @{ from = [byte[]](0xC3,0xA2,0xE2,0x80,0xA0,0xE2,0x80,0x99);  to = [byte[]](0xE2,0x80,0x99) }, # ??? -> ?  (common variant)
  @{ from = [byte[]](0xC3,0xA2,0xE2,0x80,0xA0,0xE2,0x80,0x98);  to = [byte[]](0xE2,0x80,0x98) }, # ??? -> ?  (common variant)
  @{ from = [byte[]](0xC3,0xA2,0xE2,0x80,0xA0,0xC2,0xA6);       to = [byte[]](0xE2,0x86,0x92) }, # ??? -> ?
  @{ from = [byte[]](0xC3,0xA2,0xC5,0x93,0xE2,0x80,0xA6);       to = [byte[]](0xE2,0x9C,0x85) }, # ??? -> ?
  @{ from = [byte[]](0xC3,0x83,0xC2,0xBC);                      to = [byte[]](0xC3,0xBC) },     # ?? -> ?
  @{ from = [byte[]](0xC3,0x83,0xC2,0xB6);                      to = [byte[]](0xC3,0xB6) },     # ?? -> ?
  @{ from = [byte[]](0xC3,0x83,0xC2,0xA4);                      to = [byte[]](0xC3,0xA4) },     # ?? -> ?
  @{ from = [byte[]](0xC3,0x83,0xC2,0x9F);                      to = [byte[]](0xC3,0x9F) },     # ?? -> ?
  @{ from = [byte[]](0xC3,0x83,0xC2,0x9C);                      to = [byte[]](0xC3,0x9C) },     # ?? -> ?
  @{ from = [byte[]](0xC3,0x83,0xC2,0x96);                      to = [byte[]](0xC3,0x96) },     # ?? -> ?
  @{ from = [byte[]](0xC3,0x83,0xC2,0x84);                      to = [byte[]](0xC3,0x84) }      # ?? -> ?
)

$changedAny = $false

foreach ($p in $targets) {
  if (-not (Test-Path -LiteralPath $p)) { throw "Missing: $p" }

  $data = [System.IO.File]::ReadAllBytes($p)
  $orig = $data

  foreach ($m in $map) {
    $data = Replace-Bytes $data $m.from $m.to
  }

  # Write back only if changed
  if ($data.Length -ne $orig.Length -or ($data -join ',') -ne ($orig -join ',')) {
    [System.IO.File]::WriteAllBytes($p, $data)
    Write-Host ("OK: fixed bytes in " + $p)
    $changedAny = $true
  } else {
    Write-Host ("OK: no changes needed " + $p)
  }
}

if ($changedAny) { Write-Host "DONE: repaired docs (byte-level), UTF-8 safe." }
else { Write-Host "DONE: nothing to repair." }
