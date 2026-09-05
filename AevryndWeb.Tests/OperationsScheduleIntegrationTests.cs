using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using AevryndWeb.Security;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class OperationsScheduleIntegrationTests
{
    [Theory]
    [InlineData("slime12968@gmail.com")]
    [InlineData("en531@livemail.tw")]
    public async Task AllowedRolesSeeChineseScheduleFromSameSnapshot(string email)
    {
        var directory=Path.Combine(Path.GetTempPath(),"aevrynd-schedule-integration-"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        var path=Path.Combine(directory,"queue.json");
        var now=DateTimeOffset.UtcNow;
        var tasks=new[]{"local","taichung","taoyuan"}.Select((node,index)=>new {
            id=$"TASK-{index}",nodeId=node,title="驗證遊戲畫面"+index,description="檢查相機畫面並保留測試證據。",
            state=index==0?"running":index==1?"acknowledged":"queued",reason="依實際來源顯示，不推估工作狀態。",dependsOn=Array.Empty<string>(),
            assignedAt=now.AddMinutes(-5),updatedAt=now.AddMinutes(-1),evidence="隔離測試的已驗證來源。"
        }).ToArray();
        await File.WriteAllTextAsync(path,JsonSerializer.Serialize(new {schemaVersion=1,observedAt=now,tasks}));
        using var baseFactory=new LoginFactory();
        using var factory=baseFactory.WithWebHostBuilder(builder=>builder.ConfigureTestServices(services=>
            services.AddSingleton(new OperationsScheduleProvider(new ConfigurationBuilder().AddInMemoryCollection(
                new Dictionary<string,string?>{["Operations:SchedulePath"]=path}).Build()))));
        using var client=factory.CreateClient(new WebApplicationFactoryClientOptions {BaseAddress=new Uri("https://console.test"),AllowAutoRedirect=false,HandleCookies=true});
        Assert.Equal(HttpStatusCode.Redirect,(await client.GetAsync("/Operations")).StatusCode);
        var csrf=await (await client.GetAsync("/api/auth/csrf")).Content.ReadFromJsonAsync<JsonElement>();
        using var request=new HttpRequestMessage(HttpMethod.Post,"/api/auth/verify") {Content=JsonContent.Create(new {email,code="TESTCODE"})};
        request.Headers.Add("Origin","https://console.test");request.Headers.Add("X-CSRF-TOKEN",csrf.GetProperty("token").GetString());
        Assert.Equal(HttpStatusCode.OK,(await client.SendAsync(request)).StatusCode);
        var page=await client.GetAsync("/Operations");
        var html=WebUtility.HtmlDecode(await page.Content.ReadAsStringAsync());
        Assert.Equal(HttpStatusCode.OK,page.StatusCode);
        Assert.Contains("三台主機任務排程",html);
        foreach(var task in tasks) Assert.Contains(task.title,html);
        Assert.Contains("已接單",html);Assert.Contains("等待中",html);Assert.Contains("執行中",html);
        var response=await client.GetAsync("/Operations/snapshot");
        var json=await response.Content.ReadFromJsonAsync<JsonElement>();
        var schedule=json.GetProperty("schedule");
        Assert.True(schedule.GetProperty("sourceAvailable").GetBoolean());
        Assert.Equal(3,schedule.GetProperty("tasks").GetArrayLength());
        Assert.Contains("no-store",response.Headers.CacheControl!.ToString());
    }
}
