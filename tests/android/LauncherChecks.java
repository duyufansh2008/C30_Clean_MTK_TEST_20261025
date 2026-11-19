package com.fundot.p4bu;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.GridView;
import android.view.View;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.List;

/** Runs against the actual Activity, without a test library or network access. */
public final class LauncherChecks extends Instrumentation {
    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        start();
    }

    private static Object field(Object target, String name) throws Exception {
        Field field = target.getClass().getDeclaredField(name);
        field.setAccessible(true);
        return field.get(target);
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        Activity activity = null;
        int code = Activity.RESULT_CANCELED;
        try {
            Intent intent = new Intent(Intent.ACTION_MAIN);
            intent.setComponent(new ComponentName(getTargetContext(), "app.lawnchair.LawnchairLauncher"));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity = startActivitySync(intent);
            final Activity launcher = activity;
            final Throwable[] failure = new Throwable[1];
            runOnMainSync(() -> {
                try {
                    List<?> all = (List<?>) field(launcher, "all");
                    require(!all.isEmpty(), "Emulator must have at least one launchable app");
                    Object first = all.get(0);
                    BaseAdapter adapter = (BaseAdapter) field(launcher, "adapter");
                    GridView parent = new GridView(launcher);
                    View initial = adapter.getView(0, null, parent);
                    Object icon = field(first, "icon");
                    require(icon != null, "First bind must load an icon");
                    require(adapter.getView(0, initial, parent) == initial, "Grid cell must be reused");
                    require(field(first, "icon") == icon, "Repeated binding must reuse the icon");
                    Method resume = launcher.getClass().getDeclaredMethod("onResume");
                    resume.setAccessible(true);
                    resume.invoke(launcher);
                    require(all.get(0) == first, "Returning home must preserve app metadata");
                    EditText search = (EditText) field(launcher, "search");
                    search.setText("c30-no-such-app-4f9b");
                    require(adapter.getCount() == 0, "Unmatched search must hide all apps");
                    search.setText("");
                    require(adapter.getCount() == all.size(), "Clearing search must restore apps");
                    BroadcastReceiver receiver = (BroadcastReceiver) field(launcher, "packagesChanged");
                    receiver.onReceive(launcher, new Intent(Intent.ACTION_PACKAGE_CHANGED));
                    require(all.get(0) != first, "Package changes must invalidate metadata and icons");
                } catch (Throwable error) {
                    failure[0] = error;
                }
            });
            if (failure[0] != null) throw new AssertionError("Launcher checks failed", failure[0]);
            result.putString("c30_checks", "passed");
            code = Activity.RESULT_OK;
        } catch (Throwable error) {
            result.putString("c30_checks", "failed: " + error);
        } finally {
            if (activity != null) {
                final Activity launcher = activity;
                runOnMainSync(launcher::finish);
            }
        }
        finish(code, result);
    }
}
