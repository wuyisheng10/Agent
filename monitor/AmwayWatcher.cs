// ============================================================
// 📡 C# 監看系統 — AmwayWatcher.cs
// 路徑：C:\Users\user\claude AI_Agent\monitor\AmwayWatcher.cs
// 功能：監看 output 資料夾，偵測新 JSON → 解析 → 預備 LINE Bot
// 環境：.NET 8 / Windows 11
// ============================================================

using System;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Net.Http;
using System.Threading.Tasks;
using System.Collections.Generic;

class AmwayWatcher
{
    // ---- 設定 ----
    static readonly string BaseDir    = @"C:\Users\user\claude AI_Agent";
    static readonly string WatchDir   = Path.Combine(BaseDir, "output");
    static readonly string LogFile    = Path.Combine(BaseDir, "logs", "watcher_log.txt");
    static readonly string LineToken  = Environment.GetEnvironmentVariable("LINE_CHANNEL_TOKEN") ?? "";
    static readonly bool   LineBotOn  = !string.IsNullOrEmpty(LineToken);

    static readonly HttpClient Http   = new HttpClient();

    // ================================================================
    static async Task Main(string[] args)
    {
        Log("=" + new string('=', 55));
        Log("🚀 AmwayWatcher 啟動");
        Log($"📁 監看目錄：{WatchDir}");
        Log($"🤖 LINE Bot：{(LineBotOn ? "已啟用" : "未設定（模擬模式）")}");
        Log("=" + new string('=', 55));

        // 建立 FileSystemWatcher
        using var watcher = new FileSystemWatcher(WatchDir)
        {
            Filter = "*.json",
            IncludeSubdirectories = true,
            NotifyFilter = NotifyFilters.FileName | NotifyFilters.LastWrite,
            EnableRaisingEvents = true
        };

        watcher.Created += async (s, e) => await OnFileCreated(e.FullPath);

        Log("👀 監看中...（按 Ctrl+C 停止）\n");
        Console.CancelKeyPress += (s, e) => { e.Cancel = true; Log("⛔ 手動停止"); };

        // 保持執行
        await Task.Delay(-1);
    }

    // ================================================================
    // 📂 偵測到新 JSON 檔案
    // ================================================================
    static async Task OnFileCreated(string filePath)
    {
        await Task.Delay(500); // 等待檔案寫入完成

        Log($"\n📄 偵測到新檔案：{Path.GetFileName(filePath)}");

        try
        {
            string raw = await File.ReadAllTextAsync(filePath, Encoding.UTF8);
            var doc = JsonNode.Parse(raw);
            if (doc == null) return;

            string status   = doc["status"]?.GetValue<string>() ?? "";
            string nextStep = doc["next_step"]?.GetValue<string>() ?? "";

            Log($"   狀態：{status} → 下一步：{nextStep}");

            switch (status)
            {
                case "raw":
                    await HandleRaw(doc, filePath);
                    break;

                case "scored":
                    await HandleScored(doc, filePath);
                    break;

                case "ready":
                    await HandleReady(doc, filePath);
                    break;

                default:
                    Log($"   ⚠️ 未知狀態：{status}，跳過處理");
                    break;
            }
        }
        catch (Exception ex)
        {
            Log($"   ❌ 處理失敗：{ex.Message}");
        }
    }

    // ================================================================
    // 📊 處理爬蟲原始資料（status: raw）
    // ================================================================
    static async Task HandleRaw(JsonNode doc, string filePath)
    {
        int total = doc["total"]?.GetValue<int>() ?? 0;
        Log($"   🔍 爬蟲完成：共 {total} 筆原始資料");
        Log($"   ➡ 下一步：自動執行評分Agent（02_scoring.py）");

        // 自動觸發評分腳本
        await RunPython("02_scoring.py");
    }

    // ================================================================
    // 📈 處理評分結果（status: scored）
    // ================================================================
    static async Task HandleScored(JsonNode doc, string filePath)
    {
        var stats    = doc["統計"];
        int high     = stats?["高潛力"]?.GetValue<int>() ?? 0;
        int mid      = stats?["中潛力"]?.GetValue<int>() ?? 0;
        int total    = stats?["總計"]?.GetValue<int>() ?? 0;

        Log($"   📊 評分完成：高潛力 {high} | 中潛力 {mid} | 總計 {total}");

        if (high > 0)
        {
            Log($"   ➡ 高潛力名單 {high} 人，自動生成邀約訊息...");
            await RunPython("03_templates.py");
        }
        else
        {
            Log("   ⚠️ 無高潛力客戶，本日流程結束");
        }
    }

    // ================================================================
    // ✉️ 處理待發送訊息（status: ready）
    // ================================================================
    static async Task HandleReady(JsonNode doc, string filePath)
    {
        int total = doc["total"]?.GetValue<int>() ?? 0;
        var msgs  = doc["messages"]?.AsArray();

        Log($"   ✉️ 邀約訊息已生成：{total} 則");

        if (msgs == null) return;

        foreach (var m in msgs)
        {
            string title     = m?["標題"]?.GetValue<string>() ?? "（無標題）";
            string talkType  = m?["話術類型"]?.GetValue<string>() ?? "";
            string day1Msg   = m?["訊息"]?["Day1"]?.GetValue<string>() ?? "";
            var schedule     = m?["跟進時程"];

            Log($"\n   👤 客戶：{title.Substring(0, Math.Min(30, title.Length))}");
            Log($"      話術：{talkType}");
            Log($"      Day1 發送日：{schedule?["Day1"]?.GetValue<string>()}");

            if (LineBotOn)
            {
                // 🚀 真實 LINE Bot 發送
                await SendLineMessage(day1Msg);
                Log("      ✅ LINE 訊息已發送");
            }
            else
            {
                // 📋 模擬輸出（未設定 LINE Token）
                Log("      📋 [模擬] 訊息預覽：");
                Log($"      {day1Msg.Replace("\n", "\n      ")}");
            }
        }

        Log($"\n   🎉 本日流程全部完成！共處理 {total} 位高潛力客戶");
        await WriteReport(total, filePath);
    }

    // ================================================================
    // 📱 LINE Bot 發送訊息（未來功能）
    // ================================================================
    static async Task SendLineMessage(string message)
    {
        // LINE Messaging API - Push Message
        // 需要設定：LINE_CHANNEL_TOKEN 和 目標 userId
        string userId = Environment.GetEnvironmentVariable("LINE_USER_ID") ?? "";
        if (string.IsNullOrEmpty(userId)) return;

        var payload = new
        {
            to = userId,
            messages = new[] { new { type = "text", text = message } }
        };

        var content = new StringContent(
            JsonSerializer.Serialize(payload),
            Encoding.UTF8,
            "application/json"
        );

        Http.DefaultRequestHeaders.Clear();
        Http.DefaultRequestHeaders.Add("Authorization", $"Bearer {LineToken}");

        var response = await Http.PostAsync(
            "https://api.line.me/v2/bot/message/push",
            content
        );

        if (!response.IsSuccessStatusCode)
        {
            string err = await response.Content.ReadAsStringAsync();
            Log($"      ❌ LINE 發送失敗：{err}");
        }
    }

    // ================================================================
    // 🐍 自動執行 Python 腳本
    // ================================================================
    static async Task RunPython(string scriptName)
    {
        string scriptPath = Path.Combine(BaseDir, "agents", scriptName);
        Log($"   🐍 執行：{scriptName}");

        var psi = new System.Diagnostics.ProcessStartInfo
        {
            FileName               = "python",
            Arguments              = $"\"{scriptPath}\"",
            WorkingDirectory       = Path.Combine(BaseDir, "agents"),
            UseShellExecute        = false,
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
        };

        using var proc = System.Diagnostics.Process.Start(psi);
        if (proc == null) return;

        await proc.WaitForExitAsync();
        Log(proc.ExitCode == 0
            ? $"   ✅ {scriptName} 執行成功"
            : $"   ❌ {scriptName} 執行失敗（code {proc.ExitCode}）");
    }

    // ================================================================
    // 📝 寫入每日報告
    // ================================================================
    static async Task WriteReport(int count, string sourceFile)
    {
        string reportDir  = Path.Combine(BaseDir, "logs");
        string reportPath = Path.Combine(reportDir,
            $"daily_report_{DateTime.Now:yyyyMMdd}.txt");

        string content = $"""
        ========================================
        📊 安麗 AI Agent 每日報告
        日期：{DateTime.Now:yyyy-MM-dd HH:mm}
        ========================================
        今日處理高潛力客戶：{count} 人
        來源檔案：{Path.GetFileName(sourceFile)}
        LINE Bot 狀態：{(LineBotOn ? "已啟用" : "模擬模式")}
        ========================================
        """;

        await File.AppendAllTextAsync(reportPath, content, Encoding.UTF8);
        Log($"   📝 每日報告 → {reportPath}");
    }

    // ================================================================
    // 🖊 Log 工具
    // ================================================================
    static void Log(string msg)
    {
        string ts   = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        string line = $"[{ts}] {msg}";
        Console.WriteLine(line);

        Directory.CreateDirectory(Path.GetDirectoryName(LogFile)!);
        File.AppendAllText(LogFile, line + Environment.NewLine, Encoding.UTF8);
    }
}
