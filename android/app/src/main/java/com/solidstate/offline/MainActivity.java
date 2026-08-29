package com.solidstate.offline;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.database.Cursor;
import android.graphics.Color;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;

import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class MainActivity extends Activity {
    private static final int PICK_PDF = 7001;
    private static final String ASSET_NAME = "runtime333.zip";
    private static final String ZIP_SHA256 = "3f9e9e6c302e03fe6df5e8a43658d644c4a135190fc2acdb56d59453133e814e";
    private static final String CHECKPOINT_RECORD_SHA1 = "965695bdc3ebe13f7337bb491796f6a193bd8fa6";
    private static final int ANDROID_RUNTIME_FLOOR = 333;
    private static final String ROOT_DIR = "runtime333";
    private static final String NESTED_ROOT = "SolidState_Offline_Runtime_Checkpoint333";
    private TextView status;
    private WebView web;
    private File runtimeRoot;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(245,245,245));
        status = new TextView(this);
        status.setPadding(24,18,24,18);
        status.setText("Solid State Offline — initialisation Checkpoint 333…");
        root.addView(status, new LinearLayout.LayoutParams(-1,-2));

        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        Button importPdf = new Button(this);
        importPdf.setText("Importer PDF source");
        importPdf.setOnClickListener(v -> pickPdf());
        Button reload = new Button(this);
        reload.setText("Actualiser");
        reload.setOnClickListener(v -> { if (web != null) web.reload(); });
        bar.addView(importPdf, new LinearLayout.LayoutParams(0,-2,1));
        bar.addView(reload, new LinearLayout.LayoutParams(0,-2,1));
        root.addView(bar, new LinearLayout.LayoutParams(-1,-2));

        web = new WebView(this);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.setWebViewClient(new WebViewClient() {
            private boolean allowed(Uri u) {
                return u != null && "http".equals(u.getScheme()) && "127.0.0.1".equals(u.getHost()) && u.getPort() == 8787;
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !allowed(request.getUrl());
            }
        });
        root.addView(web, new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);

        new Thread(this::initializeRuntime, "SolidStateInit").start();
    }

    private void initializeRuntime() {
        try {
            File assetCopy = new File(getCacheDir(), ASSET_NAME);
            try (InputStream in = getAssets().open(ASSET_NAME); OutputStream out = new FileOutputStream(assetCopy)) {
                byte[] b = new byte[65536]; int n; while ((n=in.read(b))>0) out.write(b,0,n);
            }
            String actual = sha256(assetCopy);
            if (!ZIP_SHA256.equals(actual)) throw new SecurityException("RUNTIME_ZIP_SHA256_MISMATCH");

            File base = new File(getFilesDir(), ROOT_DIR);
            File marker = new File(base, ".cp333_runtime_sha256");
            if (!marker.exists() || !ZIP_SHA256.equals(readText(marker))) {
                deleteRec(base); base.mkdirs(); unzipSafe(assetCopy, base);
                File nested = new File(base, NESTED_ROOT);
                runtimeRoot = nested.isDirectory() ? nested : base;
                writeText(new File(runtimeRoot, ".cp333_runtime_sha256"), ZIP_SHA256);
                if (!runtimeRoot.equals(base)) writeText(marker, ZIP_SHA256);
            } else {
                File nested = new File(base, NESTED_ROOT);
                runtimeRoot = nested.isDirectory() ? nested : base;
            }

            verifyAuthority(runtimeRoot);
            new File(runtimeRoot, "sources").mkdirs();
            new File(runtimeRoot, "saves").mkdirs();
            new File(runtimeRoot, "data").mkdirs();

            Python py = Python.getInstance();
            PyObject mod = py.getModule("android_entry");
            String reply = mod.callAttr("start_server", runtimeRoot.getAbsolutePath(), 8787).toString();
            JSONObject obj = new JSONObject(reply);
            if (!"READY".equals(obj.optString("status"))) throw new IllegalStateException(obj.toString());
            runOnUiThread(() -> {
                status.setText("Checkpoint 333 vérifié — runtime intégré — sources privées locales uniquement");
                web.loadUrl("http://127.0.0.1:8787/");
            });
        } catch (Exception e) {
            runOnUiThread(() -> status.setText("FAIL_CLOSED — " + e.getClass().getSimpleName() + ": " + e.getMessage()));
        }
    }

    private static void verifyAuthority(File root) throws Exception {
        File f = new File(new File(root, "certification"), "android_runtime_authority_333.json");
        if (!f.isFile()) throw new SecurityException("ANDROID_RUNTIME_AUTHORITY_MISSING");
        JSONObject a = new JSONObject(readText(f));
        if (a.optInt("release_checkpoint", -1) != ANDROID_RUNTIME_FLOOR) {
            throw new SecurityException("ANDROID_RUNTIME_CHECKPOINT_MISMATCH");
        }
        if (a.optInt("android_runtime_floor", -1) != ANDROID_RUNTIME_FLOOR) {
            throw new SecurityException("ANDROID_RUNTIME_FLOOR_MISMATCH");
        }
        if (!CHECKPOINT_RECORD_SHA1.equals(a.optString("release_checkpoint_record_git_blob_sha1"))) {
            throw new SecurityException("ANDROID_RUNTIME_AUTHORITY_HASH_MISMATCH");
        }
        if (a.optBoolean("private_sources_embedded", true)) {
            throw new SecurityException("PRIVATE_SOURCE_EMBEDDING_FORBIDDEN");
        }
        if (!a.optBoolean("automatic_downgrade_forbidden", false)) {
            throw new SecurityException("ANTI_ROLLBACK_POLICY_MISSING");
        }
    }

    private void pickPdf() {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("application/pdf");
        startActivityForResult(i, PICK_PDF);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != PICK_PDF || resultCode != RESULT_OK || data == null || data.getData() == null) return;
        if (runtimeRoot == null) { Toast.makeText(this,"Runtime non prêt",Toast.LENGTH_SHORT).show(); return; }
        Uri uri = data.getData();
        new Thread(() -> importPdf(uri), "SolidStateImport").start();
    }

    private void importPdf(Uri uri) {
        try {
            String display = displayName(uri);
            String safe = display.replaceAll("[^A-Za-z0-9._-]", "_");
            if (!safe.toLowerCase(Locale.ROOT).endsWith(".pdf")) safe += ".pdf";
            File target = new File(new File(runtimeRoot,"sources"), System.currentTimeMillis()+"_"+safe);
            try (InputStream in = getContentResolver().openInputStream(uri); OutputStream out = new FileOutputStream(target)) {
                if (in == null) throw new IllegalStateException("SOURCE_OPEN_FAILED");
                byte[] b = new byte[65536]; int n; while ((n=in.read(b))>0) out.write(b,0,n);
            }
            runOnUiThread(() -> {
                status.setText("PDF importé localement. Solid State valide son SHA-256 à l’actualisation.");
                web.reload();
            });
        } catch (Exception e) {
            runOnUiThread(() -> status.setText("Import FAIL_CLOSED — " + e.getClass().getSimpleName()));
        }
    }

    private String displayName(Uri uri) {
        try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (c != null && c.moveToFirst()) return c.getString(0);
        } catch (Exception ignored) {}
        return "source.pdf";
    }

    private static String sha256(File f) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new FileInputStream(f)) { byte[] b=new byte[65536]; int n; while((n=in.read(b))>0) md.update(b,0,n); }
        StringBuilder s=new StringBuilder(); for(byte x:md.digest()) s.append(String.format(Locale.ROOT,"%02x",x)); return s.toString();
    }

    private static void unzipSafe(File zip, File dest) throws Exception {
        String root = dest.getCanonicalPath() + File.separator;
        try (ZipInputStream zin = new ZipInputStream(new FileInputStream(zip))) {
            ZipEntry e; byte[] b=new byte[65536];
            while((e=zin.getNextEntry())!=null) {
                File out=new File(dest,e.getName()); String canon=out.getCanonicalPath();
                if(!canon.startsWith(root)) throw new SecurityException("ZIP_PATH_TRAVERSAL");
                if(e.isDirectory()) { out.mkdirs(); continue; }
                File p=out.getParentFile(); if(p!=null) p.mkdirs();
                try(OutputStream os=new FileOutputStream(out)){int n;while((n=zin.read(b))>0)os.write(b,0,n);}
            }
        }
    }
    private static void deleteRec(File f) { if(!f.exists())return; if(f.isDirectory()){File[] a=f.listFiles();if(a!=null)for(File x:a)deleteRec(x);} f.delete(); }
    private static void writeText(File f,String s) throws Exception { try(FileOutputStream o=new FileOutputStream(f)){o.write(s.getBytes("UTF-8"));} }
    private static String readText(File f) { try(FileInputStream in=new FileInputStream(f)){byte[] b=new byte[(int)f.length()];int n=in.read(b);return new String(b,0,Math.max(n,0),"UTF-8");}catch(Exception e){return "";} }
}
