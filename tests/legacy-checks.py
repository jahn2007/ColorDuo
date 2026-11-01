#!/usr/bin/env python3
"""Verify real legacy hooks, provider caller checks, entry packaging and unchanged shared rules."""
from pathlib import Path
import json,re,runpy,subprocess,tempfile,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'app/src/main/java/io/github/yixing233/hyperduo'
BASE='3143568c17f006c2bb044e485a623d181ff90889'
# Charging colours intentionally extend the renderer and settings; geometry,
# layout, radio and battery rules still match the legacy baseline.
for name in ['TrioGeometry.java','TrioZones.java','DuoPolicy.java','ColorOsPolicy.java','ColorOsRadio.java','ColorOsReadings.java','ColorOsBattery.java','ColorOsCharge.java','ColorOsCharger.java','ColorOsChargerClient.java']:
    old=subprocess.check_output(['git','show',f'{BASE}:app/src/main/java/io/github/yixing233/hyperduo/{name}'],cwd=ROOT)
    assert old.replace(b'\r\n',b'\n')==(SOURCE/name).read_bytes().replace(b'\r\n',b'\n'),name
for path in ['ui/ContentControls.kt']:
    old=subprocess.check_output(['git','show',f'{BASE}:app/src/main/java/io/github/yixing233/hyperduo/{path}'],cwd=ROOT)
    assert old.replace(b'\r\n',b'\n')==(SOURCE/path).read_bytes().replace(b'\r\n',b'\n'),path
for path in SOURCE.rglob('*'):
    if path.suffix in {'.java','.kt'}:
        assert not re.search(r'^import io\.github\.libxposed',path.read_text(encoding='utf-8-sig'),re.M),path
assert 'invokeOriginalMethod' not in (SOURCE/'LegacyHook.java').read_text(encoding='utf-8-sig')
assert not (ROOT/'app/src/main/resources/META-INF/xposed/module.prop').exists()
manifest=ET.parse(ROOT/'app/src/main/AndroidManifest.xml').getroot();ns='{http://schemas.android.com/apk/res/android}'
meta={e.get(ns+'name'):e.get(ns+'value') for e in manifest.findall('application/meta-data')}
assert meta['xposedmodule']=='true' and 'libxposed' not in meta
metadata=runpy.run_path(str(ROOT/'scripts/ci/artifacts.py'))['module_metadata']
with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'test.apk'
    with zipfile.ZipFile(p,'w') as z:z.writestr('assets/xposed_init','io.github.yixing233.hyperduo.HyperDuoModule\n')
    assert metadata(p)['api']=='legacy'
    with zipfile.ZipFile(p,'a') as z:z.writestr('META-INF/xposed/module.prop','targetApiVersion=102')
    try:metadata(p);raise AssertionError('mixed entry accepted')
    except ValueError:pass
stubs={
'de/robv/android/xposed/XC_MethodHook.java':'''package de.robv.android.xposed;
public class XC_MethodHook {
 public static class MethodHookParam {public Object thisObject;public Object[] args;public Object result;public Throwable error;
  final java.util.Map<String,Object> extras=new java.util.HashMap<>();
  public void setObjectExtra(String k,Object v){extras.put(k,v);}public Object getObjectExtra(String k){return extras.get(k);}
  public boolean hasThrowable(){return error!=null;}public Object getResult(){return result;}}
 protected void beforeHookedMethod(MethodHookParam p)throws Throwable{}protected void afterHookedMethod(MethodHookParam p)throws Throwable{}
 public void before(MethodHookParam p)throws Throwable{beforeHookedMethod(p);}public void after(MethodHookParam p)throws Throwable{afterHookedMethod(p);}
}''',
'de/robv/android/xposed/XposedBridge.java':'''package de.robv.android.xposed;
public class XposedBridge {public static final java.util.List<XC_MethodHook> callbacks=new java.util.ArrayList<>();
 public static void hookMethod(java.lang.reflect.Member m,XC_MethodHook c){callbacks.add(c);}public static void log(Throwable t){} }''',
'android/os/Bundle.java':'''package android.os; public class Bundle {public int api;public boolean enabled=true;public int getInt(String k,int d){return api;}}''',
'android/os/Binder.java':'package android.os; public class Binder {public static int uid;public static int getCallingUid(){return uid;}}',
'android/os/Process.java':'package android.os; public class Process {public static int myUid(){return 10088;}}',
'android/content/pm/PackageManager.java':'''package android.content.pm; public class PackageManager {public String[] packages;public String[] getPackagesForUid(int uid){return packages;}}''',
'android/content/Context.java':'''package android.content;public class Context {public android.content.pm.PackageManager pm=new android.content.pm.PackageManager();
 public android.content.pm.PackageManager getPackageManager(){return pm;}public android.content.res.Resources getResources(){return new android.content.res.Resources();}}''',
'android/content/res/Resources.java':'''package android.content.res;public class Resources {public static class Metrics {public float density=1;}public Metrics getDisplayMetrics(){return new Metrics();}}''',
'android/content/ContentProvider.java':'''package android.content; public abstract class ContentProvider {public Context context=new Context();public Context getContext(){return context;}
 public abstract boolean onCreate();public abstract android.database.Cursor query(android.net.Uri u,String[] p,String s,String[] a,String o);
 public abstract String getType(android.net.Uri u);public abstract android.net.Uri insert(android.net.Uri u,ContentValues v);
 public abstract int update(android.net.Uri u,ContentValues v,String s,String[] a);public abstract int delete(android.net.Uri u,String s,String[] a);
 public android.os.Bundle call(String m,String a,android.os.Bundle b){return null;}}''',
'android/content/ContentValues.java':'package android.content;public class ContentValues {}',
'android/database/Cursor.java':'package android.database;public interface Cursor {}',
'android/net/Uri.java':'package android.net;public class Uri {}',
'io/github/yixing233/hyperduo/Prefs.java':'package io.github.yixing233.hyperduo;class Prefs {static final String SYSTEMUI_PACKAGE="com.android.systemui";}',
'io/github/yixing233/hyperduo/LegacySettings.java':'''package io.github.yixing233.hyperduo;class LegacySettings {static int beats;static void heartbeat(Object c,int a){beats++;}static Object preferences(Object c){return c;}}''',
'io/github/yixing233/hyperduo/TrioSettings.java':'''package io.github.yixing233.hyperduo;class TrioSettings {static TrioSettings from(Object p,float d){return new TrioSettings();}android.os.Bundle toBundle(){return new android.os.Bundle();}}''',
'io/github/yixing233/hyperduo/LegacyTest.java':r'''
package io.github.yixing233.hyperduo;
import de.robv.android.xposed.*;import java.util.*;import android.os.*;
public class LegacyTest {
 static final List<String> order=new ArrayList<>();static int checks;
 static void check(boolean v,String s){checks++;if(!v)throw new AssertionError(s);}
 static void target(){}static void observed(){}
 public static void main(String[] a)throws Throwable {
  var method=LegacyTest.class.getDeclaredMethod("target");
  check(LegacyHook.around(method,f->{order.add("before");f.data="state";f.param.args[0]=7;},f->{
   check(f.data.equals("state"),"per invocation state");order.add("after");})==1,"hook installed");
  check(LegacyHook.after(method,p->{})==0,"duplicate installation ignored");
  var callback=XposedBridge.callbacks.get(0);var p=new XC_MethodHook.MethodHookParam();p.args=new Object[]{1};
  callback.before(p);order.add("other-before");check(p.args[0].equals(7),"arguments forwarded through legacy chain");
  order.add("native");p.result="native-result";order.add("other-after");callback.after(p);
  check(order.equals(List.of("before","other-before","native","other-after","after")),"other hooks and original stay in normal order");
  check(p.result.equals("native-result"),"native result preserved");
  order.clear();var failing=new XC_MethodHook.MethodHookParam();failing.args=new Object[]{1};
  callback.before(failing);failing.error=new IllegalStateException("native");callback.after(failing);
  check(failing.error instanceof IllegalStateException&&order.contains("after"),"cleanup also runs on native exception");
  int[] captured={0};LegacyHook.after(LegacyTest.class.getDeclaredMethod("observed"),q->captured[0]++);
  var observe=XposedBridge.callbacks.get(1);var bad=new XC_MethodHook.MethodHookParam();bad.error=new IllegalStateException();
  observe.before(bad);observe.after(bad);check(captured[0]==0,"failed native call cannot publish stale result");
  var provider=new LegacySettingsProvider();Binder.uid=10000;provider.context.pm.packages=new String[]{"untrusted.app"};
  try{provider.call("snapshot",null,null);throw new AssertionError("unauthorized read");}catch(SecurityException expected){}
  check(LegacySettings.beats==0,"untrusted UID cannot update activation heartbeat");
  Binder.uid=10184;provider.context.pm.packages=new String[]{"com.android.systemui"};
  Bundle forged=new Bundle();forged.enabled=false;
  check(provider.call("snapshot",null,forged).enabled,"provider reads storage instead of sender-supplied settings");
  check(LegacySettings.beats==1,"actual SystemUI heartbeat accepted");
  Binder.uid=10088;check(provider.call("snapshot",null,null)!=null,"own settings app allowed");
  try{provider.call("write",null,null);throw new AssertionError("remote write");}catch(IllegalArgumentException expected){}
  System.out.println("Legacy hook ordering, exception cleanup and provider identity: "+checks+" checks passed");
 }
}
'''
}
with tempfile.TemporaryDirectory(prefix='colorduo-legacy-') as d:
    root=Path(d);files=[]
    for name,text in stubs.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8');files.append(str(path))
    for name in ['LegacyHook.java','LegacySettingsProvider.java']:
        path=root/'io/github/yixing233/hyperduo'/name;path.write_text((SOURCE/name).read_text(encoding='utf-8-sig'),encoding='utf-8');files.append(str(path))
    subprocess.run(['javac','-encoding','UTF-8','-d',str(root),*files],check=True)
    subprocess.run(['java','-cp',str(root),'io.github.yixing233.hyperduo.LegacyTest'],check=True)
print('Legacy metadata and unchanged modern drawing/network rules verified')
