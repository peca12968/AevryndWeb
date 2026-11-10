using System.Buffers.Binary;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Numerics;

const int First = 0;
const double NearAxisM = 0.000001;
const ulong KeyMask = (1UL << 42) - 1;
const ulong AxisFlag = 1UL << 42;

if (args.Length != 1) throw new ArgumentException("Pass the capture directory.");
string root = Path.GetFullPath(args[0]);
RunSelfTests();
using var capture = JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "capture-source.json")));
var input = capture.RootElement;
int[] size = input.GetProperty("dimensions").EnumerateArray().Select(x => x.GetInt32()).ToArray();
int curves = size[0], knots = size[1];
if (size.Length != 3 || size[2] != 3 || knots <= First + 1 || curves * knots >= (1 << 21))
    throw new InvalidDataException("Unsupported strand dimensions.");
float[] radius = ReadRaw<float>("radius.f32");
int[] strandIds = ReadRaw<int>("curve-ids.i32");
if (radius.Length != curves * knots || strandIds.Length != curves || strandIds.Distinct().Count() != curves)
    throw new InvalidDataException("Radius or identity stream length mismatch.");

var clock = Stopwatch.StartNew();
ulong[]? rest = null;
var reports = new List<object>();
foreach (JsonElement pose in input.GetProperty("poses").EnumerateArray())
{
    string label = pose.GetProperty("label").GetString()!;
    float[] coordinates = ReadRaw<float>(pose.GetProperty("name").GetString()!);
    if (coordinates.Length != 3 * curves * knots) throw new InvalidDataException(label);
    var segments = new Segment[curves * (knots - 1 - First)];
    int cursor = 0;
    for (int i = 0; i < curves; i++)
    for (int j = First; j < knots - 1; j++)
    {
        int index = i * knots + j;
        var a = new Vector3(coordinates[3 * index], coordinates[3 * index + 1], coordinates[3 * index + 2]);
        var b = new Vector3(coordinates[3 * index + 3], coordinates[3 * index + 4], coordinates[3 * index + 5]);
        segments[cursor++] = Segment.Create(a, b, radius[index], radius[index + 1], index, i, j);
    }
    var result = Analyze(segments);
    ulong[] pairs = result.Pairs.ToArray();
    Array.Sort(pairs, Comparer<ulong>.Create((a, b) => (a & KeyMask).CompareTo(b & KeyMask)));
    for (int k = 1; k < pairs.Length; k++)
        if ((pairs[k - 1] & KeyMask) >= (pairs[k] & KeyMask))
            throw new InvalidDataException("Broad phase emitted duplicate or unsorted pairs.");
    if (rest is null)
    {
        if (label != "rest") throw new InvalidDataException("First input must be rest.");
        rest = pairs;
    }
    var comparison = Compare(rest, pairs, knots, strandIds);
    var summary = new
    {
        label, pose = pose.Clone(), segments = segments.Length, result.BroadBoxPairs, result.AdjacentSkipped,
        finiteOverlapWitnesses = pairs.Length, result.NearAxis, result.SameCurve,
        result.UnresolvedRadiusBounds, result.MinSignedM, result.Deepest,
        versusRest = comparison,
        elapsedSeconds = clock.Elapsed.TotalSeconds
    };
    reports.Add(summary);
    using (var writer = File.Create(Path.Combine(root, label + "-contact-keys.u64")))
        writer.Write(MemoryMarshal.AsBytes(pairs.AsSpan()));
    WriteJson(Path.Combine(root, label + "-result.json"), summary);
    Console.WriteLine($"R482_DONE {label} contacts={pairs.Length} nearAxis={result.NearAxis} broad={result.BroadBoxPairs} elapsed={clock.Elapsed.TotalSeconds:F2}");
}
WriteJson(Path.Combine(root, "self-contact-audit.json"), new
{
    source = input.GetProperty("source").Clone(), variant = input.GetProperty("variant").GetString(),
    curves, knots, firstSegment = First, nearAxisThresholdM = NearAxisM,
    syntheticTestsPassed = true, restRigidityControl = input.GetProperty("rigidStopCoordinatesExactlyEqualToRest").GetBoolean(),
    algorithm = "Morton-ordered segment AABB hierarchy. Distinct leaf pairs enumerated once. Segment distance minimizes over the four edges and optional interior of the parameter square.",
    interpretation = "Finite overlap witnesses use linearly interpolated endpoint radii at closest centerline points. An unsigned centerline distance minus the two maximum endpoint radii is a conservative lower bound; negative bounds without an overlap witness are unresolved. Near-axis means centerline separation <=1 micron, not exact topological intersection. Same-strand spans separated by <=2 segment indices are excluded.",
    scope = "All primary hair curve spans starting at span 0 for each supplied snapshot. Pair keys encode stable curve ordinal and span index. Complete selected hair included. No time-continuous claim, skin/garment tests, or assertion that all finite contacts are visible defects.",
    poses = reports
});

T[] ReadRaw<T>(string name) where T : unmanaged
{
    byte[] bytes = File.ReadAllBytes(Path.Combine(root, name));
    if (bytes.Length % Marshal.SizeOf<T>() != 0) throw new InvalidDataException(name);
    return MemoryMarshal.Cast<byte, T>(bytes).ToArray();
}

static void WriteJson(string file, object report) =>
    File.WriteAllText(file, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));

static object Compare(ulong[] baseline, ulong[] sample, int knots, int[] ids)
{
    int i = 0, j = 0, retained = 0, entered = 0, exited = 0, enteredNearAxis = 0, enteredSameCurve = 0;
    var enteredStrands = new HashSet<int>();
    var examples = new List<object>();
    while (i < baseline.Length || j < sample.Length)
    {
        ulong a = i < baseline.Length ? baseline[i] & KeyMask : ulong.MaxValue;
        ulong b = j < sample.Length ? sample[j] & KeyMask : ulong.MaxValue;
        if (a == b)
        {
            retained++;
            if ((baseline[i] & AxisFlag) == 0 && (sample[j] & AxisFlag) != 0)
                enteredNearAxis++;
            i++;
            j++;
        }
        else if (a < b)
        {
            exited++;
            i++;
        }
        else
        {
            entered++;
            bool near = (sample[j++] & AxisFlag) != 0;
            if (near) enteredNearAxis++;
            int left = (int)(b >> 21), right = (int)(b & ((1UL << 21) - 1));
            enteredStrands.Add(left / knots);
            enteredStrands.Add(right / knots);
            if (left / knots == right / knots) enteredSameCurve++;
            if (near && examples.Count < 16)
                examples.Add(new { leftStrandId = ids[left / knots], leftSegment = left % knots,
                                   rightStrandId = ids[right / knots], rightSegment = right % knots });
        }
    }
    return new { retained, entered, exited, enteredNearAxis, enteredSameCurve,
                 strandsInNewContacts = enteredStrands.Count, firstNewNearAxisWitnesses = examples };
}

static Totals Analyze(Segment[] segments)
{
    var all = segments[0].Bounds;
    foreach (ref readonly var s in segments.AsSpan()) all = Box.Union(all, s.Bounds);
    var sorted = new ulong[segments.Length];
    Vector3 extent = all.Max - all.Min;
    for (int i = 0; i < sorted.Length; i++)
    {
        Vector3 center = (segments[i].A + segments[i].B) * 0.5f;
        Vector3 q = (center - all.Min) / extent;
        uint x = (uint)Math.Clamp(q.X * 1023, 0, 1023);
        uint y = (uint)Math.Clamp(q.Y * 1023, 0, 1023);
        uint z = (uint)Math.Clamp(q.Z * 1023, 0, 1023);
        ulong code = (Spread(x) << 2) | (Spread(y) << 1) | Spread(z);
        sorted[i] = (code << 32) | (uint)i;
    }
    Array.Sort(sorted);
    var tree = new Node[segments.Length / 2 + 16];
    int count = 0;
    int Build(int begin, int end)
    {
        int k = count++;
        if (end - begin <= 8)
        {
            Box box = segments[(int)(uint)sorted[begin]].Bounds;
            for (int i = begin + 1; i < end; i++) box = Box.Union(box, segments[(int)(uint)sorted[i]].Bounds);
            tree[k] = new Node(box, begin, end, -1, -1);
        }
        else
        {
            int mid = begin + (end - begin) / 2;
            int l = Build(begin, mid), r = Build(mid, end);
            tree[k] = new Node(Box.Union(tree[l].Bounds, tree[r].Bounds), begin, end, l, r);
        }
        return k;
    }
    int root = Build(0, sorted.Length);
    var jobs = new List<(int, int)>();
    Split(root, root, 0);
    void Split(int i, int j, int depth)
    {
        if (!tree[i].Bounds.Overlaps(tree[j].Bounds)) return;
        if (depth == 7 || (tree[i].Leaf && tree[j].Leaf))
        {
            jobs.Add((i, j));
            return;
        }
        if (i == j)
        {
            int l = tree[i].Left, r = tree[i].Right;
            Split(l, l, depth + 1); Split(l, r, depth + 1); Split(r, r, depth + 1);
        }
        else if (!tree[i].Leaf && (tree[j].Leaf || tree[i].Count >= tree[j].Count))
        {
            Split(tree[i].Left, j, depth + 1); Split(tree[i].Right, j, depth + 1);
        }
        else
        {
            Split(i, tree[j].Left, depth + 1); Split(i, tree[j].Right, depth + 1);
        }
    }

    var output = new Totals();
    Parallel.ForEach(jobs, new ParallelOptions { MaxDegreeOfParallelism = 4 },
        () => new Totals(),
        (job, _, local) => { Walk(job.Item1, job.Item2, local); return local; },
        local => { lock (output) output.Merge(local); });
    return output;

    void Walk(int i, int j, Totals result)
    {
        ref readonly Node u = ref tree[i];
        ref readonly Node v = ref tree[j];
        if (!u.Bounds.Overlaps(v.Bounds)) return;
        if (u.Leaf && v.Leaf)
        {
            for (int m = u.Begin; m < u.End; m++)
            for (int n = i == j ? m + 1 : v.Begin; n < v.End; n++)
            {
                ref readonly Segment sa = ref segments[(int)(uint)sorted[m]];
                ref readonly Segment sb = ref segments[(int)(uint)sorted[n]];
                if (!sa.Bounds.Overlaps(sb.Bounds)) continue;
                result.BroadBoxPairs++;
                TestPair(sa, sb, result);
            }
        }
        else if (i == j)
        {
            Walk(u.Left, u.Left, result); Walk(u.Left, u.Right, result); Walk(u.Right, u.Right, result);
        }
        else if (!u.Leaf && (v.Leaf || u.Count >= v.Count))
        {
            Walk(u.Left, j, result); Walk(u.Right, j, result);
        }
        else
        {
            Walk(i, v.Left, result); Walk(i, v.Right, result);
        }
    }
}

static ulong Spread(uint x)
{
    x = (x | x << 16) & 0x030000FF;
    x = (x | x << 8) & 0x0300F00F;
    x = (x | x << 4) & 0x030C30C3;
    return (x | x << 2) & 0x09249249;
}

static void TestPair(in Segment a, in Segment b, Totals output)
{
    bool same = a.Curve == b.Curve;
    if (same && Math.Abs(a.Knot - b.Knot) <= 2)
    {
        output.AdjacentSkipped++;
        return;
    }
    double reach = Math.Max(a.Ra, a.Rb) + Math.Max(b.Ra, b.Rb);
    Closest(a, b, out double squared, out double s, out double t);
    if (squared > reach * reach) return;
    double distance = Math.Sqrt(squared);
    double signed = distance - (a.Ra + (a.Rb - a.Ra) * s) - (b.Ra + (b.Rb - b.Ra) * t);
    if (signed > 0)
    {
        output.UnresolvedRadiusBounds++;
        return;
    }
    bool nearAxis = distance <= NearAxisM;
    ulong key = ((ulong)Math.Min(a.Id, b.Id) << 21) | (uint)Math.Max(a.Id, b.Id);
    output.Pairs.Add(key | (nearAxis ? AxisFlag : 0));
    if (nearAxis) output.NearAxis++;
    if (same) output.SameCurve++;
    if (output.MinSignedM is null || signed < output.MinSignedM)
    {
        output.MinSignedM = signed;
        output.Deepest = new { leftOrdinal = a.Curve, leftSegment = a.Knot, rightOrdinal = b.Curve,
            rightSegment = b.Knot, centerlineDistanceM = distance, signedM = signed,
            leftLocalM = new[] { (double)a.A.X + ((double)a.B.X - a.A.X) * s,
                                (double)a.A.Y + ((double)a.B.Y - a.A.Y) * s,
                                (double)a.A.Z + ((double)a.B.Z - a.A.Z) * s } };
    }
}

static void Closest(in Segment left, in Segment right, out double best, out double bestS, out double bestT)
{
    D3 a = D3.From(left.A), b = D3.From(right.A);
    D3 u = D3.From(left.B) - a, v = D3.From(right.B) - b, w = a - b;
    double uu = D3.Dot(u, u), vv = D3.Dot(v, v), uv = D3.Dot(u, v);
    double uw = D3.Dot(u, w), vw = D3.Dot(v, w);
    double d = double.PositiveInfinity, x = 0, y = 0;
    void Check(double s, double t)
    {
        D3 v0 = w + u * s - v * t;
        double distance = D3.Dot(v0, v0);
        if (distance < d) { d = distance; x = s; y = t; }
    }
    static double Unit(double value) => Math.Clamp(value, 0, 1);
    Check(0, vv > 0 ? Unit(vw / vv) : 0);
    Check(1, vv > 0 ? Unit((vw + uv) / vv) : 0);
    Check(uu > 0 ? Unit(-uw / uu) : 0, 0);
    Check(uu > 0 ? Unit((uv - uw) / uu) : 0, 1);
    double determinant = uu * vv - uv * uv;
    if (determinant > 1e-14 * uu * vv)
    {
        double s = (uv * vw - vv * uw) / determinant;
        double t = (uu * vw - uv * uw) / determinant;
        if (s is >= 0 and <= 1 && t is >= 0 and <= 1) Check(s, t);
    }
    best = d; bestS = x; bestT = y;
}

static void RunSelfTests()
{
    Segment line = Segment.Create(new(-1, 0, 0), new(1, 0, 0), .04f, .04f, 0, 0, 0);
    Segment cross = Segment.Create(new(0, -1, 0), new(0, 1, 0), .04f, .04f, 1, 1, 0);
    Segment near = Segment.Create(new(-1, .05f, 0), new(1, .05f, 0), .04f, .04f, 2, 2, 0);
    Segment far = Segment.Create(new(-1, .12f, 0), new(1, .12f, 0), .04f, .04f, 3, 3, 0);
    Segment point = Segment.Create(new(2, 0, 0), new(2, 0, 0), .04f, .04f, 4, 4, 0);
    Closest(line, cross, out var d0, out var s0, out var t0);
    Closest(line, near, out var d1, out _, out _);
    Closest(line, point, out var d2, out _, out _);
    if (d0 != 0 || s0 != .5 || t0 != .5 || Math.Abs(d1 - .0025) > 1e-9 || d2 != 1)
        throw new InvalidOperationException("Analytic distance self-test failed.");
    var r = new Totals();
    TestPair(line, cross, r); TestPair(line, near, r); TestPair(line, far, r);
    if (r.Pairs.Count != 2 || r.NearAxis != 1) throw new InvalidOperationException("Overlap self-test failed.");
    var random = new Random(443);
    var small = new Segment[180];
    for (int i = 0; i < small.Length; i++)
    {
        var u = new Vector3(random.NextSingle(), random.NextSingle(), random.NextSingle());
        var v = u + new Vector3(random.NextSingle() - .5f, random.NextSingle() - .5f, random.NextSingle() - .5f) * .22f;
        small[i] = Segment.Create(u, v, .02f, .028f, i, i, 0);
    }
    var expected = new Totals();
    for (int i = 0; i < small.Length; i++)
    for (int j = i + 1; j < small.Length; j++)
        TestPair(small[i], small[j], expected);
    var actual = Analyze(small);
    if (!actual.Pairs.Order().SequenceEqual(expected.Pairs.Order()) ||
        actual.UnresolvedRadiusBounds != expected.UnresolvedRadiusBounds)
        throw new InvalidOperationException("Broad phase differs from exhaustive comparison.");
}

readonly record struct D3(double X, double Y, double Z)
{
    public static D3 From(Vector3 p) => new(p.X, p.Y, p.Z);
    public static D3 operator +(D3 a, D3 b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);
    public static D3 operator -(D3 a, D3 b) => new(a.X - b.X, a.Y - b.Y, a.Z - b.Z);
    public static D3 operator *(D3 a, double b) => new(a.X * b, a.Y * b, a.Z * b);
    public static double Dot(D3 a, D3 b) => a.X * b.X + a.Y * b.Y + a.Z * b.Z;
}
readonly record struct Box(Vector3 Min, Vector3 Max)
{
    public bool Overlaps(Box o) => Min.X <= o.Max.X && Max.X >= o.Min.X && Min.Y <= o.Max.Y &&
        Max.Y >= o.Min.Y && Min.Z <= o.Max.Z && Max.Z >= o.Min.Z;
    public static Box Union(Box a, Box b) => new(Vector3.Min(a.Min, b.Min), Vector3.Max(a.Max, b.Max));
}
readonly record struct Segment(Vector3 A, Vector3 B, float Ra, float Rb, int Id, int Curve, int Knot, Box Bounds)
{
    public static Segment Create(Vector3 a, Vector3 b, float ra, float rb, int id, int curve, int knot)
    {
        Vector3 radius = new(Math.Max(ra, rb) + 0.00000025f);
        return new Segment(a, b, ra, rb, id, curve, knot, new Box(Vector3.Min(a, b) - radius, Vector3.Max(a, b) + radius));
    }
}
readonly record struct Node(Box Bounds, int Begin, int End, int Left, int Right)
{
    public bool Leaf => Left < 0;
    public int Count => End - Begin;
}
sealed class Totals
{
    public readonly List<ulong> Pairs = new();
    public long BroadBoxPairs, AdjacentSkipped, NearAxis, SameCurve, UnresolvedRadiusBounds;
    public double? MinSignedM;
    public object? Deepest;
    public void Merge(Totals other)
    {
        Pairs.AddRange(other.Pairs);
        BroadBoxPairs += other.BroadBoxPairs;
        AdjacentSkipped += other.AdjacentSkipped;
        NearAxis += other.NearAxis;
        SameCurve += other.SameCurve;
        UnresolvedRadiusBounds += other.UnresolvedRadiusBounds;
        if (other.MinSignedM is not null && (MinSignedM is null || other.MinSignedM < MinSignedM))
        {
            MinSignedM = other.MinSignedM;
            Deepest = other.Deepest;
        }
    }
}

