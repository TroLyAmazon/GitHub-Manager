# Delete all __pycache__ folders and *.pyc files recursively from current directory
$ErrorActionPreference = "SilentlyContinue"

Write-Host "Cleaning __pycache__ and *.pyc from: $PWD"

Get-ChildItem -Path . -Recurse -Force -Directory -Filter "__pycache__" |
  ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "Removed folder: $($_.FullName)"
  }

Get-ChildItem -Path . -Recurse -Force -File -Include "*.pyc","*.pyo" |
  ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "Removed file: $($_.FullName)"
  }

Write-Host "Done."
