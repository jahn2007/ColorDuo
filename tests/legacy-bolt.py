#!/usr/bin/env python3
"""Execute the production legacy bolt handoff against native visibility snapshots."""
from pathlib import Path
import re, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
hooks=(ROOT/'app/src/main/java/io/github/yixing233/hyperduo/ColorOsHooks.java').read_text(encoding='utf-8')
match=re.search(r'^        void syncNativeBolt\([^\n]*\) \{.*?^        \}',hooks,re.M|re.S)
assert match, 'missing production native-bolt handoff'
source=r'''
import java.util.*;
class LegacyBoltTest {
 static final int VISIBLE=0, INVISIBLE=4, GONE=8;
 static int checks;
 static void check(boolean v,String message){checks++;if(!v)throw new AssertionError(message);}
 static class View {
  static final int VISIBLE=0,GONE=8;
  int visibility;List<Integer> writes=new ArrayList<>();
  View(int v){visibility=v;}int getVisibility(){return visibility;}
  void setVisibility(int v){visibility=v;writes.add(v);}
 }
 static class State {boolean charging,chargingPaused;}
 static class TrioAppearance {boolean owned;boolean hidesNativeBolt(){return owned;}}
 static class Host {
  final State state=new State();View forward,reverse;
  final Map<View,Integer> nativeVisibility=new IdentityHashMap<>(),visibilityOverrides=new IdentityHashMap<>();
  Host(int f,int r){forward=new View(f);reverse=new View(r);nativeVisibility.put(forward,f);nativeVisibility.put(reverse,r);}
  View find(String id){return id.equals("battery_charge_icon")?forward:reverse;}
@METHOD@
 }
 public static void main(String[] args){
  TrioAppearance a=new TrioAppearance();Host h=new Host(GONE,GONE);
  h.syncNativeBolt(a);check(h.forward.visibility==GONE&&h.reverse.visibility==GONE,"unplugged stays hidden");
  h.state.charging=true;h.syncNativeBolt(a);
  check(h.forward.visibility==VISIBLE&&h.reverse.visibility==GONE,"charging reveals primary when both snapshots are hidden");
  check(h.nativeVisibility.get(h.forward)==GONE,"fallback must not taint the restoration snapshot");
  check(h.visibilityOverrides.get(h.forward)==VISIBLE,"native writes cannot hide the fallback during ownership");
  h.forward.writes.clear();h.syncNativeBolt(a);
  check(h.forward.writes.isEmpty(),"periodic refresh must not flash hidden then visible");
  h.reverse.visibility=VISIBLE;h.reverse.writes.clear();
  a.owned=true;h.syncNativeBolt(a);check(h.forward.visibility==GONE&&h.reverse.visibility==VISIBLE,"custom bolt leaves wireless reverse indicator alone");
  check(h.reverse.writes.isEmpty()&&!h.visibilityOverrides.containsKey(h.reverse),"reverse status is never overridden");
  a.owned=false;h.syncNativeBolt(a);check(h.forward.visibility==VISIBLE,"changing back to native takes effect immediately");
  h.nativeVisibility.put(h.forward,VISIBLE);h.syncNativeBolt(a);
  check(h.forward.visibility==VISIBLE&&!h.visibilityOverrides.containsKey(h.forward),"native visible callback supersedes the charging fallback");
  h.state.charging=false;h.syncNativeBolt(a);
  check(h.forward.visibility==VISIBLE,"native full or unplugged state remains authoritative");
  h.nativeVisibility.put(h.forward,GONE);h.syncNativeBolt(a);
  check(h.forward.visibility==GONE,"native disconnect hides the primary bolt");
  h.state.chargingPaused=true;h.syncNativeBolt(a);check(h.forward.visibility==VISIBLE,"paused charger retains the legacy native handoff");
  h.state.chargingPaused=false;h.syncNativeBolt(a);check(h.forward.visibility==GONE,"disconnect removes only the fallback");
  Host missing=new Host(GONE,VISIBLE);missing.forward=null;missing.state.charging=true;missing.syncNativeBolt(a);
  check(missing.reverse.visibility==VISIBLE&&missing.reverse.writes.isEmpty(),"missing primary must not repurpose wireless reverse status");
  Host absent=new Host(GONE,GONE);absent.forward=null;absent.reverse=null;absent.syncNativeBolt(a);
  check(absent.visibilityOverrides.isEmpty(),"missing native views are safe");
  System.out.println("Legacy native bolt handoff: "+checks+" checks passed");
 }
}
'''.replace('@METHOD@',match.group())
with tempfile.TemporaryDirectory(prefix='colorduo-legacy-bolt-') as d:
    path=Path(d)/'LegacyBoltTest.java';path.write_text(source,encoding='utf-8')
    subprocess.run(['java',str(path)],check=True)
