#!/usr/bin/env python3
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
T=ROOT/".architecture"/"technical.json"; C=ROOT/".architecture"/"commercial.json"; TV=ROOT/"TECHNICAL_ARCHITECTURE.md"; CV=ROOT/"COMMERCIAL_ARCHITECTURE.md"
def nid(v): return re.sub(r"[^A-Za-z0-9_]","_",v)
def tech(t):
 n=t["repository"]["full_name"].split("/")[-1]; a=t["architecture"]; l=[f"# Technical Architecture — {n}","","> Generated from `.architecture/technical.json`. Do not edit directly; run `python .architecture/generate.py`.","",f"Status: **{a['status']}**  ",f"Scope: **{a['scope']}**","","## System schema","","```mermaid","flowchart LR"]
 cs=a.get("components",[])
 if cs:
  for x in cs:l.append(f'    {nid(x["id"])}["{x["name"]}\\n{x["type"]}"]')
 else:l.append('    empty["No components declared"]')
 for x in cs:
  for d in x.get("depends_on",[]):l.append(f"    {nid(x['id'])} --> {nid(d)}")
 for s in a.get("external_services",[]):l.append(f'    {nid(s["id"])}[["{s["name"]}\\nexternal-service"]]')
 l += ["```","","## Inventory","",f"- Components: **{len(a.get('components', []))}**",f"- Interfaces: **{len(a.get('interfaces', []))}**",f"- Data stores: **{len(a.get('data_stores', []))}**",f"- External services: **{len(a.get('external_services', []))}**",f"- Internal dependencies: **{len(a.get('dependencies',{}).get('internal',[]))}**",f"- External dependencies: **{len(a.get('dependencies',{}).get('external',[]))}**",f"- Architecture decisions: **{len(a.get('decisions', []))}**","","## Deployment schema","","```mermaid","flowchart LR"]
 p=None; es=a.get("deployment",{}).get("environments",[])
 if es:
  for e in es:
   i="env_"+nid(e["name"]); ps=", ".join(e.get("providers",[])) or "unassigned"; l.append(f'    {i}["{e["name"]}\\nproviders: {ps}"]');
   if p:l.append(f"    {p} --> {i}")
   p=i
 else:l.append('    noenv["No deployment environments declared"]')
 l += ["```","","## Update rule","","Architecture-impacting commits must update `.architecture/technical.json` and/or `.architecture/commercial.json`, then regenerate both architecture views.",""]
 return "\n".join(l)
def commercial(c):
 n=c["repository"]["full_name"].split("/")[-1]; a=c["commercial_architecture"]; o=a["offering"]; l=[f"# Commercial Architecture — {n}","","> Generated from `.architecture/commercial.json`. Do not edit directly; run `python .architecture/generate.py`.","",f"Status: **{a['status']}**","","## Commercial schema","","```mermaid","flowchart LR",f'    offering["{o["name"]}\\n{o["type"]}"]']
 for x in a.get("actors",[]):l.append(f'    {nid(x["id"])}(("{x["name"]}")) --> offering')
 for x in a.get("capabilities",[]):l.append(f'    offering --> cap_{nid(x["id"])}["{x["name"]}\\ncapability"]')
 for x in a.get("channels",[]):l.append(f'    offering --> channel_{nid(x["id"])}[["{x["name"]}\\nchannel"]]')
 l += ["```","","## Inventory","",f"- Actors: **{len(a.get('actors', []))}**",f"- Capabilities: **{len(a.get('capabilities', []))}**",f"- Value streams: **{len(a.get('value_streams', []))}**",f"- Channels: **{len(a.get('channels', []))}**",f"- Commercial dependencies: **{len(a.get('commercial_dependencies', []))}**",f"- Revenue streams: **{len(a.get('revenue_model',{}).get('streams',[]))}**",f"- Cost drivers: **{len(a.get('cost_drivers', []))}**",f"- Risks: **{len(a.get('risks', []))}**","","## Update rule","","Commercial facts remain `UNASSESSED` until validated. Architecture-impacting commits must update the relevant raw source and regenerate this view.",""]
 return "\n".join(l)
t=json.loads(T.read_text()); c=json.loads(C.read_text());
if t["repository"]["full_name"]!=c["repository"]["full_name"]:raise SystemExit("repository identity mismatch")
TV.write_text(tech(t)); CV.write_text(commercial(c)); print("generated architecture views")
