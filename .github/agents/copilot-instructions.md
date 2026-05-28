# my-photo-app Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-26

## Active Technologies
- C# 12 / .NET 8.0 + Blazor Server (ASP.NET Core 8), Bootstrap 5.x (wwwroot/bootstrap/)、bUnit 1.29.5（テスト） (002-modern-ui-codebehind)
- N/A（本機能は UI 層のみ。データアクセスは Application/Infrastructure 層に委譲） (002-modern-ui-codebehind)
- C# 12 / .NET 8.0 + Blazor Server (ASP.NET Core 8), Bootstrap 5.x, ApexCharts.Blazor（グラフ表示） (003-management-summary-dashboard)
- SQL Server — 既存 `SalesForecasts` テーブルを GROUP BY 集計クエリで参照 (003-management-summary-dashboard)
- [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION] (main)
- [if applicable, e.g., PostgreSQL, CoreData, files or N/A] (main)
- Azure SQL Database（スキーマ変更なし — Employees / SystemSettings テーブルは DB に既存） (004-env-vars-and-master-maintenance)
- Azure SQL Database（スキーマ変更なし — Pipeline / CodeMasterItems テーブルは DB に既存） (006-pipeline-crud)
- Azure SQL Database（PipelineImportStaging テーブルは DB に既存） (007-pipeline-excel-io)
- Markdown（GitHub Flavored Markdown） + なし（ドキュメント更新のみ） (008-update-readme)
- Azure SQL Database（スキーマ変更なし — Employees テーブルは旧テキスト列削除済み・Code列のみ） (010-employee-codemaster-summary-layout)
- Bicep (Azure CLI 2.x / azd 1.x)、PowerShell 7+ + Azure Developer CLI (azd)、Azure Bicep、Docker、SqlCmd (go-sqlcmd) (013-azd-infra-deployment)
- Azure SQL Database (Basic SKU)、Azure Blob Storage (Standard_LRS) (013-azd-infra-deployment)
- C# 12 / .NET 8 (LTS) + ASP.NET Core / Blazor Server (Interactive Server), Entity Framework Core 8 (`Microsoft.EntityFrameworkCore.SqlServer`), AngleSharp 1.x（HTML パース）, ChartJs.Blazor.Fork（グラフ）, Polly 8 / `Microsoft.Extensions.Http.Resilience`（リトライ・指数バックオフ）, Serilog + `Microsoft.ApplicationInsights.AspNetCore`（可観測性）, `Azure.Identity` / `Azure.Extensions.AspNetCore.Configuration.Secrets`（Key Vault 連携） (001-mvp-stats-dashboard)
- Azure SQL Database（SQL Server 互換）。EF Core Code First + Migrations (001-mvp-stats-dashboard)
- .NET 8, C# 12, Blazor Server (InteractiveServer) + Blazor scoped CSS (`*.razor.css`)、bUnit (テスト) (002-mobile-responsive)
- C# 13 / .NET 9 + ASP.NET Core 9 (Minimal API), Blazor Server (InteractiveServer), Entity Framework Core 9, SQL Server 2022, `Azure.AI.OpenAI` v2.x (新規追加) (007-dashboard-enhance-history)
- SQL Server — 既存 `Snapshots`/`MvpProfiles` テーブル維持、新規 `AiInsights` テーブル追加 (007-dashboard-enhance-history)
- C# 13 / .NET 9 + Blazor (InteractiveServer), MudBlazor（既存）, ApexCharts.Blazor（既存） (010-svg-bubble-population-map)
- SQL Server / Azure SQL Database（本機能では変更なし） (010-svg-bubble-population-map)

- C# / .NET 8 (001-sales-forecast-app)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

# Add commands for C# / .NET 8

## Code Style

C# / .NET 8: Follow standard conventions

## Recent Changes
- 010-svg-bubble-population-map: Added C# 13 / .NET 9 + Blazor (InteractiveServer), MudBlazor（既存）, ApexCharts.Blazor（既存）
- 010-svg-bubble-population-map: Added [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]
- 007-dashboard-enhance-history: Added C# 13 / .NET 9 + ASP.NET Core 9 (Minimal API), Blazor Server (InteractiveServer), Entity Framework Core 9, SQL Server 2022, `Azure.AI.OpenAI` v2.x (新規追加)


<!-- MANUAL ADDITIONS START -->
## 004-dapr-and-modernization: Active Feature Context

**Technologies**: C# 12 / .NET 8 LTS, ASP.NET Core 8 Minimal API, Blazor Server, EF Core 8, Dapr Input Binding (`bindings.cron`), `Microsoft.ApplicationInsights.WorkerService 2.22.0`, `ChartJs.Blazor.Fork 2.0.2`  
**Storage**: Azure SQL Server via EF Core — `Countries` テーブルに `GeoRegion tinyint` 列追加  
**Key files**:
- `src/MvpAnalize.Web/Endpoints/AdminCrawlEndpoints.cs` — Dapr `/crawl-schedule` + 地域更新エンドポイント
- `src/MvpAnalize.Domain/Entities/Country.cs` — `GeoRegion GeoRegion` プロパティ追加
- `src/MvpAnalize.Domain/Aggregations/AggregationService.cs` — `CountryRegionMap.GetRegion` → `Country.GeoRegion`
- `src/MvpAnalize.Web/Endpoints/CachedDashboardAggregator.cs` — `InvalidateGeoCache(Guid)` 追加
- `src/MvpAnalize.Web/Components/Charts/ConcentrationChart.razor` — 新規 Chart.js コンポーネント
- `src/MvpAnalize.Crawler.Cli/CompositionRoot.cs` — AppInsights WorkerService + 設定管理統一

**Config keys**: `ConnectionStrings:MvpAnalize` / `AdminApi:Key` / `ApplicationInsights:ConnectionString`  
**GeoRegion enum**: `MvpAnalize.Domain.Aggregations.CountryRegionMap` に定義（値: 0=Americas, 1=Europe, 2=AsiaPacific, 3=MEA, 4=Unknown）  
**Cache key pattern**: `"geo:{snapshotId:N}"` — `IMemoryCache.Remove()` でパージ
<!-- MANUAL ADDITIONS END -->
