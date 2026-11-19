package app.lawnchair;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.ResolveInfo;
import android.graphics.Color;
import android.os.Bundle;
import android.provider.Settings;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.text.Collator;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** A small local launcher. It does not start background services or use a network. */
public final class LawnchairLauncher extends Activity {
    private final List<ResolveInfo> all = new ArrayList<>();
    private final List<ResolveInfo> visible = new ArrayList<>();
    private final AppAdapter adapter = new AppAdapter();
    private EditText search;

    private int dp(int value) { return (int)(getResources().getDisplayMetrics().density * value + .5f); }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(24), dp(16), dp(24), dp(8));
        root.setBackgroundColor(Color.rgb(246, 248, 252));
        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = new TextView(this);
        title.setText("C30 桌面"); title.setTextSize(25); title.setTextColor(Color.rgb(25, 40, 60));
        header.addView(title, new LinearLayout.LayoutParams(0, dp(56), 1));
        Button settings = new Button(this); settings.setText("设置");
        settings.setOnClickListener(v -> {
            try { startActivity(new Intent(Settings.ACTION_SETTINGS)); }
            catch (Exception e) { Toast.makeText(this, "无法打开设置", Toast.LENGTH_SHORT).show(); }
        });
        header.addView(settings); root.addView(header);
        search = new EditText(this); search.setSingleLine(true); search.setHint("搜索应用");
        root.addView(search, new LinearLayout.LayoutParams(-1, dp(56)));
        GridView grid = new GridView(this);
        grid.setNumColumns(GridView.AUTO_FIT); grid.setColumnWidth(dp(125));
        grid.setStretchMode(GridView.STRETCH_COLUMN_WIDTH); grid.setVerticalSpacing(dp(12));
        grid.setAdapter(adapter);
        grid.setOnItemClickListener((parent, view, position, id) -> {
            ResolveInfo app = visible.get(position);
            Intent launch = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
            launch.setComponent(new ComponentName(app.activityInfo.packageName, app.activityInfo.name));
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
            try { startActivity(launch); }
            catch (Exception e) { Toast.makeText(this, "应用暂时无法打开", Toast.LENGTH_SHORT).show(); }
        });
        root.addView(grid, new LinearLayout.LayoutParams(-1, 0, 1)); setContentView(root);
        search.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            public void onTextChanged(CharSequence s, int start, int before, int count) { filter(); }
            public void afterTextChanged(Editable s) {}
        });
    }
    @Override protected void onResume() {
        super.onResume(); all.clear();
        all.addAll(getPackageManager().queryIntentActivities(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0));
        Collator collator = Collator.getInstance(Locale.CHINA);
        all.sort((a, b) -> collator.compare(a.loadLabel(getPackageManager()).toString(), b.loadLabel(getPackageManager()).toString()));
        filter();
    }
    private void filter() {
        String q = search.getText().toString().trim().toLowerCase(Locale.ROOT);
        visible.clear();
        for (ResolveInfo app : all) {
            String label = app.loadLabel(getPackageManager()).toString().toLowerCase(Locale.ROOT);
            if (label.contains(q) || app.activityInfo.packageName.toLowerCase(Locale.ROOT).contains(q)) visible.add(app);
        }
        adapter.notifyDataSetChanged();
    }
    @Override public void onBackPressed() { search.setText(""); search.clearFocus(); }
    private final class AppAdapter extends BaseAdapter {
        public int getCount() { return visible.size(); }
        public Object getItem(int p) { return visible.get(p); }
        public long getItemId(int p) { return p; }
        public View getView(int p, View recycled, ViewGroup parent) {
            LinearLayout item = new LinearLayout(LawnchairLauncher.this);
            item.setOrientation(LinearLayout.VERTICAL); item.setGravity(Gravity.CENTER);
            item.setPadding(dp(8), dp(10), dp(8), dp(10));
            ResolveInfo app = visible.get(p);
            ImageView icon = new ImageView(LawnchairLauncher.this);
            icon.setImageDrawable(app.loadIcon(getPackageManager()));
            item.addView(icon, new LinearLayout.LayoutParams(dp(48), dp(48)));
            TextView label = new TextView(LawnchairLauncher.this);
            label.setText(app.loadLabel(getPackageManager())); label.setTextSize(14); label.setMaxLines(2);
            label.setGravity(Gravity.CENTER); label.setTextColor(Color.rgb(25,40,60));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, dp(44)); lp.topMargin = dp(6);
            item.addView(label, lp); return item;
        }
    }
}
