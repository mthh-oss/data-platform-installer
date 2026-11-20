$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8000"

Write-Host "== health =="
Invoke-RestMethod "$base/api/health" | ConvertTo-Json

Write-Host "== plugins =="
(Invoke-RestMethod "$base/api/plugins") | ForEach-Object { "$($_.id) v$($_.version)" }

$body = @{
  name = "smoke-$(Get-Random -Maximum 9999)"
  platforms = @("mysql", "flink")
  configs = @{
    mysql = @{ host_port = 13306; root_password = "root123"; database = "demo"; user = "demo"; password = "demo123"; image_tag = "8.0" }
    flink = @{ ui_port = 18081; task_slots = 2; tm_memory = "1024m"; image_tag = "1.18.1-scala_2.12-java11" }
  }
} | ConvertTo-Json -Depth 6

$cluster = Invoke-RestMethod -Method Post -Uri "$base/api/clusters" -ContentType "application/json" -Body $body
Write-Host "cluster id=$($cluster.id) project=$($cluster.project_name)"

$job = Invoke-RestMethod -Method Post -Uri "$base/api/clusters/$($cluster.id)/deploy"
Write-Host "job id=$($job.id)"

for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 2
  $j = Invoke-RestMethod "$base/api/jobs/$($job.id)"
  Write-Host "status=$($j.status)"
  if ($j.status -in @("succeeded", "failed")) {
    Write-Host $j.log_text
    if ($j.error) { Write-Host "error=$($j.error)" }
    break
  }
}
