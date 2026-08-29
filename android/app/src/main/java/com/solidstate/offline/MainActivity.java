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
    private static final String ZIP_SHA256 = "75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add";
    private static final String ROOT_DIR = "runtime329";
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
        status.setText("Solid State Offline — initialisation…");
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
            File assetCopy = new File(getCacheDir(), "runtime329.zip");
            try (InputStream in = getAssets().open("runtime329.zip"); OutputStream out = new FileOutputStream(assetCopy)) {
                byte[] b = new byte[65536]; int n; while ((n=in.read(b))>0) out.write(b,0,n);
            }
            String actual = sha256(assetCopy);
            if (!ZIP_SHA256.equals(actual)) throw new SecurityException("RUNTIME_ZIP_SHA256_MISMATCH");
            File base = new File(getFilesDir(), ROOT_DIR);
            File marker = new File(base, ".cp329_sha256");
            if (!marker.exists() || !ZIP_SHA256.equals(readText(marker))) {
                deleteRec(base); base.mkdirs(); unzipSafe(assetCopy, base);
                File nested = new File(base, "SolidState_Offline_Runtime_Checkpoint329");
                runtimeRoot = nested.isDirectory() ? nested : base;
                writeText(new File(runtimeRoot, ".cp329_sha256"), ZIP_SHA256);
                if (!runtimeRoot.equals(base)) writeText(marker, ZIP_SHA256);
            } else {
                File nested = new File(base, "SolidState_Offline_Runtime_Checkpoint329");
                runtimeRoot = nested.isDirectory() ? nested : base;
            }
            new File(runtimeRoot, "sources").mkdirs();
            new File(runtimeRoot, "saves").mkdirs();
            new File(runtimeRoot, "data").mkdirs();
            Python py = Python.getInstance();
            PyObject mod = py.getModule("android_entry");
            String reply = mod.callAttr("start_server", runtimeRoot.getAbsolutePath(), 8787).toString();
            JSONObject obj = new JSONObject(reply);
            if (!"READY".equals(obj.optString("status"))) throw new IllegalStateException(obj.toString());
            runOnUiThread(() -> {
                status.setText("Checkpoint 329 vérifié — serveur local 127.0.0.1 — sources privées uniquement");
                web.loadUrl("http://127.0.0.1:8787/");
            });
        } catch (Exception e) {
            runOnUiThread(() -> status.setText("FAIL_CLOSED — " + e.getClass().getSimpleName() + ": " + e.getMessage()));
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
                status.setText("PDF importé dans le stockage privé. Validation SHA-256 par Solid State à l’actualisation.");
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
