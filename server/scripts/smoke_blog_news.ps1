# server/scripts/smoke_blog_news.ps1
param(
  [string]$BaseUrl = "http://127.0.0.1:8000"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Hit([string]$Url) {
  Write-Host "==> $Url"
  & curl.exe -sS -i $Url | Out-String | Write-Host
  Write-Host ""
}

Hit "$BaseUrl/blog/"
Hit "$BaseUrl/news/"
Hit "$BaseUrl/blog/welcome"
Hit "$BaseUrl/news/release-notes-2026-02"