using System.Text.Json;
using System.Security.Cryptography;
using Xunit;

namespace AevryndWeb.Tests;

public sealed class CharacterEditorContractTests
{
    private static string Root()
    {
        var root = new DirectoryInfo(AppContext.BaseDirectory);
        while (root is not null && !File.Exists(Path.Combine(root.FullName, "AevryndWeb.slnx"))) root = root.Parent;
        return Path.Combine(root!.FullName, "AevryndWeb");
    }

    [Fact]
    public void EditorUsesGeometryInsteadOfPantsOverlayAndFrameSwitches()
    {
        var view = File.ReadAllText(Path.Combine(Root(), "Views/Home/Showcase.cshtml"));
        var script = File.ReadAllText(Path.Combine(Root(), "wwwroot/js/character-editor.js"));
        var legacyStyles = File.ReadAllText(Path.Combine(Root(), "wwwroot/css/showcase.css"));
        Assert.DoesNotContain("character-pants-overlay", view);
        Assert.DoesNotContain("character-pants-overlay", legacyStyles);
        Assert.DoesNotContain("data-gpu-shape-sequence", view);
        Assert.DoesNotContain("data-character-sequence", view);
        Assert.Contains("使用者指定的第三版三維模型", view);
        Assert.Contains("歷史 v11 淘汰原型對照（不是目前角色）", view);
        Assert.Contains("OrbitControls", script);
        Assert.Contains("morphTargetInfluences[slot]", script);
        Assert.Contains("upper.visible = clothed", script);
        Assert.Contains("if (pants) pants.visible = clothed", script);
        Assert.Contains("const defaultValues = { chinLength: 1 }", script);
        Assert.Contains("restricted?.hasAttribute('inert')", script);
    }

    [Fact]
    public void CharacterEditorModuleGraphAndShowcaseInteractionsRespectStrictCsp()
    {
        var root = Root();
        var view = File.ReadAllText(Path.Combine(root, "Views/Home/Showcase.cshtml"));
        var showcaseScript = File.ReadAllText(Path.Combine(root, "wwwroot/js/showcase.js"));
        var controls = File.ReadAllText(Path.Combine(root, "wwwroot/lib/three/OrbitControls.js"));
        var loader = File.ReadAllText(Path.Combine(root, "wwwroot/lib/three/GLTFLoader.js"));
        var skeleton = File.ReadAllText(Path.Combine(root, "wwwroot/lib/utils/SkeletonUtils.js"));
        Assert.DoesNotContain("style=", view, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain(".style.", showcaseScript, StringComparison.Ordinal);
        Assert.DoesNotContain(".style.", controls, StringComparison.Ordinal);
        Assert.Contains("data-reveal=\"50\"", view, StringComparison.Ordinal);
        Assert.Contains("step=\"5\"", view, StringComparison.Ordinal);
        Assert.Contains("from '../utils/SkeletonUtils.js'", loader, StringComparison.Ordinal);
        Assert.Contains("from '../three/three.module.js'", skeleton, StringComparison.Ordinal);
        Assert.True(File.Exists(Path.Combine(root, "wwwroot/css/showcase-runtime.css")));
    }

    [Fact]
    public void ApprovedThirdCharacterContainsUpperSkeletonAndFaceMorphsWithoutExternalUris()
    {
        var data = File.ReadAllBytes(Path.Combine(Root(), "wwwroot/media/character-editor/character.glb"));
        Assert.Equal("9C98378086DE3128119E6BEBA2531D5A37AAA70B594E0FA3859FD93CA63FE838",
            Convert.ToHexString(SHA256.HashData(data)));
        Assert.Equal(0x46546C67u, BitConverter.ToUInt32(data, 0));
        Assert.Equal((uint)data.Length, BitConverter.ToUInt32(data, 8));
        using var document = JsonDocument.Parse(data.AsMemory(20, BitConverter.ToInt32(data, 12)));
        var json = document.RootElement;
        var nodes = json.GetProperty("nodes").EnumerateArray().ToArray();
        foreach (var name in new[] { "Body", "Eyes", "Upper", "Hair" })
            Assert.Single(nodes.Where(node => node.TryGetProperty("name", out var value) && value.GetString() == name));
        Assert.DoesNotContain(nodes, node => node.TryGetProperty("name", out var value) && value.GetString() == "Pants");
        foreach (var skin in json.GetProperty("skins").EnumerateArray()) Assert.Equal(53, skin.GetProperty("joints").GetArrayLength());
        foreach (var image in json.GetProperty("images").EnumerateArray()) Assert.False(image.TryGetProperty("uri", out _));
        var body = nodes.Single(node => node.TryGetProperty("name", out var value) && value.GetString() == "Body");
        var mesh = json.GetProperty("meshes")[body.GetProperty("mesh").GetInt32()];
        foreach (var primitive in mesh.GetProperty("primitives").EnumerateArray()) Assert.Equal(10, primitive.GetProperty("targets").GetArrayLength());
    }
}
