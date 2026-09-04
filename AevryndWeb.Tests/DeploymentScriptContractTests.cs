using Xunit;
using System.Diagnostics;
using System.Security.Cryptography;

namespace AevryndWeb.Tests;

public sealed class DeploymentScriptContractTests
{
    private static readonly string Project = FindProject();

    [Fact]
    public void IisContractIsExactAndFailClosed()
    {
        var common = Read("PublicSite.Common.ps1");
        Assert.Contains("http/127.0.0.1:8080:$script:PublicSiteDomain", common, StringComparison.Ordinal);
        Assert.Contains("$portSites.Count -ne 1", common, StringComparison.Ordinal);
        Assert.Contains("GetFullPath($script:PublicSitePublish)", common, StringComparison.Ordinal);
        Assert.Contains("managedRuntimeVersion", common, StringComparison.Ordinal);
        Assert.Contains("AlwaysRunning", common, StringComparison.Ordinal);
        Assert.Contains("Assert-IisConfiguration", common, StringComparison.Ordinal);
    }

    [Fact]
    public void LegacyShutdownRequiresListenerExecutableAndExactArguments()
    {
        var common = Read("PublicSite.Common.ps1");
        Assert.Contains("LocalPort 8792", common, StringComparison.Ordinal);
        Assert.Contains("LocalAddress -cne '127.0.0.1'", common, StringComparison.Ordinal);
        Assert.Contains("process.ExecutablePath", common, StringComparison.Ordinal);
        Assert.Contains("arguments.Count -ne 2", common, StringComparison.Ordinal);
        Assert.Contains("Paths.Assembly", common, StringComparison.Ordinal);
    }

    [Fact]
    public void InstallerWhatIfPrecedesEveryMutationAndRollbackCoversArtifacts()
    {
        var install = Read("Install-PublicSite.ps1");
        Assert.StartsWith("[CmdletBinding(SupportsShouldProcess)]", install, StringComparison.Ordinal);
        var whatIf = install.IndexOf("if ($WhatIfPreference)", StringComparison.Ordinal);
        Assert.True(whatIf >= 0 && whatIf < install.IndexOf("dotnet publish", StringComparison.Ordinal));
        Assert.True(whatIf < install.IndexOf("New-Item -ItemType Directory", StringComparison.Ordinal));
        Assert.Contains("add','backup'", install, StringComparison.Ordinal);
        Assert.Contains("backupPublish", install, StringComparison.Ordinal);
        Assert.Contains("backupScripts", install, StringComparison.Ordinal);
        Assert.Contains("previousTaskXml", install, StringComparison.Ordinal);
        Assert.Contains("restore','backup'", install, StringComparison.Ordinal);
    }

    [Fact]
    public void InstallerRequiresElevationAndCredentialInteropBeforeDeploymentWork()
    {
        var install = Read("Install-PublicSite.ps1");
        var whatIf = install.IndexOf("if ($WhatIfPreference)", StringComparison.Ordinal);
        var elevation = install.IndexOf("Assert-PublicSiteAdministrator", StringComparison.Ordinal);
        var interop = install.IndexOf("Add-PublicSiteCredentialInterop", StringComparison.Ordinal);
        var publish = install.IndexOf("dotnet publish", StringComparison.Ordinal);
        var backup = install.IndexOf("Invoke-AppCmdChecked @('add','backup',$iisBackup)", StringComparison.Ordinal);

        Assert.True(whatIf >= 0 && whatIf < elevation && elevation < interop && interop < publish && publish < backup);
        var common = Read("PublicSite.Common.ps1");
        Assert.Contains("WindowsBuiltInRole]::Administrator", common, StringComparison.Ordinal);
        Assert.Contains("Re-run PowerShell 7 as Administrator", common, StringComparison.Ordinal);
    }

    [Fact]
    public void PreBackupFailureCannotEnterProcessRollback()
    {
        var install = Read("Install-PublicSite.ps1");
        var backup = install.IndexOf("Invoke-AppCmdChecked @('add','backup',$iisBackup); $iisBackupCreated = $true; $rollbackRequired = $true", StringComparison.Ordinal);
        var catchBlock = install.IndexOf("} catch {", backup, StringComparison.Ordinal);
        var preBackupGuard = install.IndexOf("if (-not $rollbackRequired) { throw $deploymentError }", catchBlock, StringComparison.Ordinal);
        var rollbackStop = install.IndexOf("Stop-ProvenNgrok", preBackupGuard, StringComparison.Ordinal);

        Assert.True(backup >= 0 && catchBlock > backup && preBackupGuard > catchBlock && rollbackStop > preBackupGuard);
        Assert.Contains("$rollbackRequired = $false", install, StringComparison.Ordinal);
        Assert.DoesNotContain("$rollbackRequired = $true; Invoke-AppCmdChecked @('add','backup'", install, StringComparison.Ordinal);
    }

    [Fact]
    public void AppCmdBackupUsesDocumentedPositionalIdentifierAndPreservesDiagnostics()
    {
        var install = Read("Install-PublicSite.ps1");
        Assert.Contains("Invoke-AppCmdChecked @('add','backup',$iisBackup)", install, StringComparison.Ordinal);
        Assert.Contains("IIS operation failed (exit $exitCode)", install, StringComparison.Ordinal);
        Assert.Contains("if ($detail.Length -gt 512)", install, StringComparison.Ordinal);
    }

    [Fact]
    public void NgrokStopRequiresRuntimeOwnershipOrExactIisUpstream()
    {
        var install = Read("Install-PublicSite.ps1"); var stop = Read("Stop-PublicSite.ps1");
        Assert.Contains("Get-PublicSiteRuntimeState -AllowLegacy", install, StringComparison.Ordinal);
        Assert.Contains("Get-VerifiedPublicSiteProcess", install, StringComparison.Ordinal);
        Assert.Contains("-UpstreamPort 8080", install, StringComparison.Ordinal);
        Assert.Contains("unexpected upstream or executable", install, StringComparison.Ordinal);
        Assert.Contains("unexpected executable or upstream; nothing was stopped", stop, StringComparison.Ordinal);
        Assert.DoesNotContain("Stop-Process -Name", install, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("Stop-Process -Name", stop, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void NgrokIdentityUsesTrustedAppxImageExactArgumentsAndHash()
    {
        var common = Read("PublicSite.Common.ps1");
        Assert.Contains("ngrok.ngrok_1g87z0zv29zzc", common, StringComparison.Ordinal);
        Assert.Contains("CN=933CF6B5-07F8-4D54-9831-0ADEF7F6CC73", common, StringComparison.Ordinal);
        Assert.Contains("arguments.Count -ne $expected.Count", common, StringComparison.Ordinal);
        Assert.Contains("Get-FileHash -LiteralPath $process.ExecutablePath", common, StringComparison.Ordinal);
        Assert.Contains("ngrokImageSha256", common, StringComparison.Ordinal);
        Assert.DoesNotContain("ExecutablePath,$expectedExecutable", common, StringComparison.Ordinal);
    }

    [Fact]
    public void RunningWindowsAliasNgrokResolvesToTrustedAppxImage()
    {
        if (!OperatingSystem.IsWindows()) return;
        var common = Path.Combine(Project, "scripts", "PublicSite.Common.ps1");
        var command = $". '{common.Replace("'", "''")}'; Add-PublicSiteCredentialInterop; $paths=Get-PublicSitePaths; $candidate=@(Get-CimInstance Win32_Process -Filter \"Name='ngrok.exe'\" | Where-Object {{$_.CommandLine.Contains('--domain='+$script:PublicSiteDomain,[StringComparison]::Ordinal) -and $_.CommandLine.Contains('http://127.0.0.1:8792',[StringComparison]::Ordinal)}}); if($candidate.Count-eq0){{exit 0}}; if($candidate.Count-ne1){{exit 4}}; if($null-eq(Get-VerifiedPublicSiteProcess -ProcessId $candidate[0].ProcessId -Paths $paths -UpstreamPort 8792)){{exit 5}}";
        var encoded = Convert.ToBase64String(System.Text.Encoding.Unicode.GetBytes(command));
        Assert.Equal(0, Run(@"C:\Program Files\PowerShell\7\pwsh.exe", $"-NoProfile -EncodedCommand {encoded}").ExitCode);
    }

    [Fact]
    public void PowerShellFiveRejectsTelemetryScriptsBeforeExecution()
    {
        if (!OperatingSystem.IsWindows()) return;
        foreach (var script in new[] { "Publish-OperationsTelemetry.ps1", "Install-OperationsTelemetry.ps1" })
        {
            var arguments = script.StartsWith("Publish", StringComparison.Ordinal) ? $"-NoProfile -ExecutionPolicy Bypass -File \"{Path.Combine(Project, "scripts", script)}\" -NodeId taichung -Once -WhatIf" : $"-NoProfile -ExecutionPolicy Bypass -File \"{Path.Combine(Project, "scripts", script)}\" -NodeId taichung -WhatIf";
            var result = Run("powershell.exe", arguments);
            Assert.NotEqual(0, result.ExitCode); Assert.Contains("ScriptRequiresUnmatchedPSVersion", result.Output, StringComparison.Ordinal); Assert.Contains("7.0", result.Output, StringComparison.Ordinal);
        }
    }

    [Fact]
    public void TelemetryScriptsParseInPowerShellSeven()
    {
        if (!OperatingSystem.IsWindows()) return;
        foreach (var name in new[] { "Install-OperationsTelemetry.ps1", "Publish-OperationsTelemetry.ps1", "Stop-OperationsTelemetry.ps1" })
        {
            var path = Path.Combine(Project, "scripts", name).Replace("'", "''");
            var command = $"$tokens=$null;$errors=$null;[Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$tokens,[ref]$errors)|Out-Null;if($errors.Count-ne0){{$errors|% ToString;exit 9}}";
            var encoded = Convert.ToBase64String(System.Text.Encoding.Unicode.GetBytes(command));
            var result = Run(@"C:\Program Files\PowerShell\7\pwsh.exe", $"-NoProfile -EncodedCommand {encoded}");
            Assert.Equal(0, result.ExitCode);
        }
    }

    [Fact]
    public void TelemetryInstallerWhatIfHasNoKeyOrFilesystemMutation()
    {
        if (!OperatingSystem.IsWindows()) return;
        var path = Path.Combine(Project, "scripts", "Install-OperationsTelemetry.ps1");
        var keyName = "Aevrynd-WhatIf-" + Guid.NewGuid().ToString("N");
        var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "Aevrynd", "OperationsTelemetry");
        var before = Directory.Exists(root) ? Directory.GetLastWriteTimeUtc(root) : DateTime.MinValue;
        var result = Run(@"C:\Program Files\PowerShell\7\pwsh.exe", $"-NoProfile -File \"{path}\" -NodeId taichung -KeyName {keyName} -WhatIf");
        var after = Directory.Exists(root) ? Directory.GetLastWriteTimeUtc(root) : DateTime.MinValue;
        Assert.Equal(0, result.ExitCode); Assert.Contains("non-exportable ECDSA P-256", result.Output, StringComparison.Ordinal);
        Assert.Equal(before, after);
        Assert.False(CngKey.Exists(keyName, CngProvider.MicrosoftSoftwareKeyStorageProvider, CngKeyOpenOptions.UserKey));
    }

    [Fact]
    public void TelemetryPublisherContainsNoSharedSecretOrPrivateKeyExportPath()
    {
        var publisher = Read("Publish-OperationsTelemetry.ps1"); var installer = Read("Install-OperationsTelemetry.ps1");
        Assert.DoesNotContain("Credential", publisher, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("HMAC", publisher, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("ExportPkcs8", publisher + installer, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("ExportECPrivateKey", publisher + installer, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("CngExportPolicies]::None", installer, StringComparison.Ordinal);
        Assert.Contains("X-Aevrynd-Key-Id", publisher, StringComparison.Ordinal);
    }

    [Fact]
    public void EveryCommittedBackupCleanupFailureIsNonFatal()
    {
        if (!OperatingSystem.IsWindows()) return;
        var common = Path.Combine(Project, "scripts", "PublicSite.Common.ps1");
        var command = $". '{common.Replace("'", "''")}'; $count=0; foreach($label in @('publish','scripts','iis')){{ $ok=Invoke-NonFatalCommittedCleanup -Label $label -Action {{ $script:count++; throw 'injected' }}; if($ok){{exit 2}} }}; if($count-ne3){{exit 3}}";
        var encoded = Convert.ToBase64String(System.Text.Encoding.Unicode.GetBytes(command));
        var result = Run(@"C:\Program Files\PowerShell\7\pwsh.exe", $"-NoProfile -EncodedCommand {encoded}");
        Assert.Equal(0, result.ExitCode); Assert.Equal(3, result.Output.Split("injected", StringSplitOptions.None).Length - 1);
    }

    [Fact]
    public void IisBackupDeleteRequiresSuccessfulDeploymentOrCompleteRollback()
    {
        var install = Read("Install-PublicSite.ps1");
        var restore = install.IndexOf("Invoke-AppCmdChecked @('restore','backup',$iisBackup)", StringComparison.Ordinal);
        var rollbackComplete = install.IndexOf("$rollbackSucceeded = $true", StringComparison.Ordinal);
        var rollbackFailure = install.IndexOf("Deployment failed and rollback failed.", StringComparison.Ordinal);
        var finallyBlock = install.IndexOf("} finally {", StringComparison.Ordinal);
        var guardedDelete = install.IndexOf("if ($iisBackupCreated -and ($deploymentSucceeded -or $rollbackSucceeded))", StringComparison.Ordinal);

        Assert.True(restore >= 0 && restore < rollbackComplete && rollbackComplete < rollbackFailure && rollbackFailure < finallyBlock && finallyBlock < guardedDelete);
        Assert.Contains("$rollbackSucceeded = $false", install, StringComparison.Ordinal);
        Assert.DoesNotContain("if ($iisBackupCreated) { & $paths.AppCmd delete backup", install, StringComparison.Ordinal);
    }

    private static (int ExitCode, string Output) Run(string fileName, string arguments)
    {
        using var process = Process.Start(new ProcessStartInfo(fileName, arguments) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true })!;
        var output = process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd(); process.WaitForExit(); return (process.ExitCode, output);
    }

    private static string Read(string name) => File.ReadAllText(Path.Combine(Project, "scripts", name));
    private static string FindProject()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            var candidate = Path.Combine(directory.FullName, "AevryndWeb", "AevryndWeb.csproj");
            if (File.Exists(candidate)) return Path.GetDirectoryName(candidate)!;
            directory = directory.Parent;
        }
        throw new DirectoryNotFoundException("AevryndWeb project was not found.");
    }
}
