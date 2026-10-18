// AssetShot: a picture of a prefab, a model, a material, a mesh or a UI prefab, for the user to see what a step is
// about. It renders the asset in a preview scene (nothing in the project or the open scene changes), framed on its
// bounds; given an object of it, it paints that object in an accent colour (a UI element: tints it) and draws a frame
// round it on the picture, so a problem in an asset shows where it is. A collider or another invisible object gets
// the frame alone.
//
// Put it in an Editor folder of the project's test folder, like the other test tools, and call it from the bridge's
// code call, or from a batch run:
//   AssetShot.Capture("Assets/Enemies/Goblin.prefab", ".ai-profile/trace/<task>/goblin-shield.png", "Body/ShieldCollider")
//   Unity -batchmode -projectPath <project> -executeMethod AssetShot.CaptureFromArgs -quit
//         -assetShot <asset path> <png path> [<object path or name>] [<size in pixels>]
// It returns (and logs) one line: where the picture went and what was highlighted, or why nothing was made, with the
// object's children when the path wasn't found. A relative png path is relative to the project's folder.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

public static class AssetShot
{
    static readonly Color Accent = new Color(1f, 0.42f, 0.16f, 1f);
    static readonly Color Back = new Color(0.17f, 0.19f, 0.23f, 1f);

    public static void CaptureFromArgs()
    {
        var args = Environment.GetCommandLineArgs();
        int i = Array.IndexOf(args, "-assetShot");
        if (i < 0 || i + 2 >= args.Length)
        {
            Debug.Log("[AssetShot] usage: -assetShot <asset path> <png path> [<object path or name>] [<size>]");
            return;
        }
        string highlight = i + 3 < args.Length && !args[i + 3].StartsWith("-") ? args[i + 3] : null;
        int size = i + 4 < args.Length && int.TryParse(args[i + 4], out int s) ? s : 768;
        Debug.Log("[AssetShot] " + Capture(args[i + 1], args[i + 2], highlight, size));
    }

    public static string Capture(string assetPath, string pngPath, string highlight = null, int size = 768)
    {
        var asset = AssetDatabase.LoadMainAssetAtPath(assetPath);
        if (asset == null) return "not found: " + assetPath;
        var made = new List<Object>();
        var pru = new PreviewRenderUtility();
        try
        {
            GameObject root = Stage(asset, made);
            if (root == null) return "not a prefab, model, material or mesh: " + assetPath;
            pru.AddSingleGO(root);
            bool ui = root.GetComponentInChildren<RectTransform>(true) != null;
            if (ui) ToWorldCanvas(root, made);

            // what to point at
            Transform target = null;
            if (!string.IsNullOrEmpty(highlight))
            {
                target = Find(root.transform, highlight);
                if (target == null)
                    return "object not found: " + highlight + "; its children: " + string.Join(", ", Paths(root.transform).Take(40));
            }
            var all = Visible(root);
            if (all.Count == 0 && !ui) return "nothing to render in " + assetPath;
            Bounds whole = ui ? RectBounds(root.transform) : Union(all.Select(r => r.bounds));
            Bounds focus = whole;
            string what = "";
            if (target != null)
            {
                var own = Visible(target.gameObject);
                if (ui) { Tint(target); focus = RectBounds(target); what = "tinted the UI element"; }
                else if (own.Count > 0) { Paint(own, made); focus = Union(own.Select(r => r.bounds)); what = "painted " + own.Count + " renderer(s)"; }
                else
                {
                    var cols = target.GetComponentsInChildren<Collider>(true);
                    if (cols.Length == 0) return "nothing to show at " + highlight + ": no renderer, collider or UI element";
                    focus = Union(cols.Select(ColliderBounds));
                    what = "framed " + cols.Length + " collider(s)";
                }
            }

            // a small object is framed with some of what is round it; else the whole asset
            Bounds frame = whole;
            if (target != null && focus.size.magnitude < whole.size.magnitude * 0.25f) { frame = focus; frame.Expand(focus.size.magnitude * 2f); }
            var cam = pru.camera;
            cam.fieldOfView = 30f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = Back;
            var dir = ui ? Vector3.forward : Quaternion.Euler(18f, -32f, 0f) * Vector3.forward;
            float radius = Mathf.Max(frame.extents.magnitude, 0.01f);
            float dist = radius / Mathf.Sin(cam.fieldOfView * 0.5f * Mathf.Deg2Rad) * 1.08f;
            cam.transform.position = frame.center - dir * dist;
            cam.transform.rotation = Quaternion.LookRotation(dir);
            cam.nearClipPlane = Mathf.Max(dist * 0.01f, 0.001f);
            cam.farClipPlane = dist * 10f;
            pru.lights[0].intensity = 1.1f;
            pru.lights[0].transform.rotation = Quaternion.Euler(40f, -30f, 0f);
            pru.lights[1].intensity = 0.6f;
            pru.ambientColor = new Color(0.35f, 0.35f, 0.38f);

            pru.BeginStaticPreview(new Rect(0, 0, size, size));
            pru.Render(true, false);
            var tex = pru.EndStaticPreview();
            made.Add(tex);
            if (target != null) DrawFrame(tex, cam, focus);

            string path = Path.IsPathRooted(pngPath) ? pngPath : Path.Combine(Directory.GetParent(Application.dataPath).FullName, pngPath);
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllBytes(path, tex.EncodeToPNG());
            return "saved " + pngPath + " (" + tex.width + "x" + tex.height + ")" + (what.Length > 0 ? "; " + what + " at " + highlight : "");
        }
        catch (Exception e)
        {
            return "failed: " + e.Message;
        }
        finally
        {
            pru.Cleanup();
            foreach (var o in made) if (o != null) Object.DestroyImmediate(o);
        }
    }

    // the asset as something to render: a copy of a prefab or a model, a sphere with a material, an object with a mesh
    static GameObject Stage(Object asset, List<Object> made)
    {
        GameObject go = null;
        if (asset is GameObject g) go = Object.Instantiate(g);
        else if (asset is Material m)
        {
            go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            go.GetComponent<Renderer>().sharedMaterial = m;
        }
        else if (asset is Mesh mesh)
        {
            go = new GameObject("mesh");
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            go.AddComponent<MeshRenderer>().sharedMaterial = new Material(Unlit()) { color = Color.gray };
            made.Add(go.GetComponent<MeshRenderer>().sharedMaterial);
        }
        if (go == null) return null;
        go.hideFlags = HideFlags.HideAndDontSave;
        go.transform.position = Vector3.zero;
        made.Add(go);
        return go;
    }

    // a UI prefab renders through a world-space canvas, which a panel without its own canvas gets for the picture
    static void ToWorldCanvas(GameObject root, List<Object> made)
    {
        var canvases = root.GetComponentsInChildren<Canvas>(true);
        if (canvases.Length == 0)
        {
            var holder = new GameObject("canvas", typeof(RectTransform), typeof(Canvas));
            holder.hideFlags = HideFlags.HideAndDontSave;
            MoveToSceneOf(root, holder);
            holder.GetComponent<Canvas>().renderMode = RenderMode.WorldSpace;
            var rt = (RectTransform)root.transform;
            ((RectTransform)holder.transform).sizeDelta = rt.rect.size.sqrMagnitude > 0 ? rt.rect.size : new Vector2(800, 600);
            root.transform.SetParent(holder.transform, false);
            made.Add(holder);
        }
        else foreach (var c in canvases) if (c.isRootCanvas) c.renderMode = RenderMode.WorldSpace;
        Canvas.ForceUpdateCanvases();
    }

    static void MoveToSceneOf(GameObject inScene, GameObject other)
    {
        UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(other, inScene.scene);
    }

    static Transform Find(Transform root, string pathOrName)
    {
        var t = root.Find(pathOrName);
        if (t != null) return t;
        if (pathOrName.Contains("/")) return null;
        return root.GetComponentsInChildren<Transform>(true).FirstOrDefault(x => x.name == pathOrName);
    }

    static IEnumerable<string> Paths(Transform root)
    {
        foreach (var t in root.GetComponentsInChildren<Transform>(true))
        {
            if (t == root) continue;
            var parts = new List<string>();
            for (var x = t; x != null && x != root; x = x.parent) parts.Insert(0, x.name);
            yield return string.Join("/", parts);
        }
    }

    static List<Renderer> Visible(GameObject go)
    {
        return go.GetComponentsInChildren<Renderer>(true).Where(r => r.enabled && r.bounds.size.sqrMagnitude > 0f).ToList();
    }

    static Bounds Union(IEnumerable<Bounds> all)
    {
        Bounds? u = null;
        foreach (var b in all)
        {
            if (u == null) u = b;
            else { var x = u.Value; x.Encapsulate(b); u = x; }
        }
        return u ?? new Bounds(Vector3.zero, Vector3.one);
    }

    static Bounds RectBounds(Transform t)
    {
        var rt = t as RectTransform;
        if (rt == null) return new Bounds(t.position, Vector3.one);
        var c = new Vector3[4];
        rt.GetWorldCorners(c);
        var b = new Bounds(c[0], Vector3.zero);
        foreach (var p in c) b.Encapsulate(p);
        return b;
    }

    // a collider's box from its own shape: it isn't in a physics world here, so its bounds can't be asked
    static Bounds ColliderBounds(Collider col)
    {
        var t = col.transform;
        Vector3 center = Vector3.zero, size = Vector3.one;
        if (col is BoxCollider box) { center = box.center; size = box.size; }
        else if (col is SphereCollider sph) { center = sph.center; size = Vector3.one * sph.radius * 2f; }
        else if (col is CapsuleCollider cap)
        {
            center = cap.center;
            size = Vector3.one * cap.radius * 2f;
            size[cap.direction] = Mathf.Max(cap.height, cap.radius * 2f);
        }
        else if (col is MeshCollider mc && mc.sharedMesh != null) { center = mc.sharedMesh.bounds.center; size = mc.sharedMesh.bounds.size; }
        var b = new Bounds(t.TransformPoint(center), Vector3.zero);
        for (int i = 0; i < 8; i++)
        {
            var corner = center + Vector3.Scale(size * 0.5f, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
            b.Encapsulate(t.TransformPoint(corner));
        }
        return b;
    }

    // the object under question in the accent colour: on the copy's renderers only, with materials made for the picture
    static void Paint(List<Renderer> rs, List<Object> made)
    {
        var mat = new Material(Unlit());
        foreach (var p in new[] { "_BaseColor", "_UnlitColor", "_Color" }) if (mat.HasProperty(p)) mat.SetColor(p, Accent);
        made.Add(mat);
        foreach (var r in rs) r.sharedMaterials = Enumerable.Repeat(mat, Mathf.Max(1, r.sharedMaterials.Length)).ToArray();
    }

    // through the canvas renderer, which every UI element draws with: no dependence on the UI package
    static void Tint(Transform t)
    {
        foreach (var cr in t.GetComponentsInChildren<CanvasRenderer>(true)) cr.SetColor(Color.Lerp(cr.GetColor(), Accent, 0.6f));
    }

    static Shader Unlit()
    {
        var pipeline = GraphicsSettings.currentRenderPipeline;
        var names = pipeline == null
            ? new[] { "Unlit/Color", "Hidden/Internal-Colored" }
            : new[] { "Universal Render Pipeline/Unlit", "HDRP/Unlit", "Unlit/Color", "Hidden/Internal-Colored" };
        foreach (var n in names) { var s = Shader.Find(n); if (s != null) return s; }
        return Shader.Find("Hidden/Internal-Colored");
    }

    // a frame round the object on the picture: its bounds' corners as the camera sees them
    static void DrawFrame(Texture2D tex, Camera cam, Bounds b)
    {
        float x0 = float.MaxValue, y0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue;
        for (int i = 0; i < 8; i++)
        {
            var c = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
            var v = cam.WorldToViewportPoint(c);
            x0 = Mathf.Min(x0, v.x); y0 = Mathf.Min(y0, v.y); x1 = Mathf.Max(x1, v.x); y1 = Mathf.Max(y1, v.y);
        }
        int w = tex.width, h = tex.height, pad = Mathf.Max(4, w / 100), line = Mathf.Max(2, w / 250);
        int ax = Mathf.Clamp((int)(x0 * w) - pad, 0, w - 1), bx = Mathf.Clamp((int)(x1 * w) + pad, 0, w - 1);
        int ay = Mathf.Clamp((int)(y0 * h) - pad, 0, h - 1), by = Mathf.Clamp((int)(y1 * h) + pad, 0, h - 1);
        for (int k = 0; k < line; k++)
        {
            for (int x = ax; x <= bx; x++) { Set(tex, x, ay + k); Set(tex, x, by - k); }
            for (int y = ay; y <= by; y++) { Set(tex, ax + k, y); Set(tex, bx - k, y); }
        }
        tex.Apply();
    }

    static void Set(Texture2D tex, int x, int y)
    {
        if (x >= 0 && y >= 0 && x < tex.width && y < tex.height) tex.SetPixel(x, y, Accent);
    }
}
