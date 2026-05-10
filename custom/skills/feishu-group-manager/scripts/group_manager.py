#!/usr/bin/env python3
"""飞书群-Agent 绑定管理工具

用法:
  python group_manager.py list                    # 列出所有绑定
  python group_manager.py bind <group_id> <agent_id> [群名]  # 绑定群到Agent
  python group_manager.py unbind <group_id>       # 解除群绑定
  python group_manager.py reassign <group_id> <agent_id>  # 重新分配群
  python group_manager.py info <group_id>         # 查询群信息
  python group_manager.py agents                  # 列出所有Agent
"""
import sys, json, os, shutil

CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
GROUPS_DB = os.path.expanduser("~/.openclaw/workspace/groups.json")

def load_config():
    with open(CONFIG) as f:
        return json.load(f)

def save_config(cfg):
    shutil.copy2(CONFIG, CONFIG + ".bak")
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def load_groups():
    if os.path.exists(GROUPS_DB):
        with open(GROUPS_DB) as f:
            return json.load(f)
    return {"groups": {}}

def save_groups(data):
    with open(GROUPS_DB, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def find_binding(cfg, group_id):
    for i, b in enumerate(cfg["bindings"]):
        m = b.get("match", {})
        p = m.get("peer", {})
        if p.get("id") == group_id:
            return i, b
    return -1, None

def cmd_list():
    cfg = load_config()
    groups = load_groups()
    result = []
    for b in cfg["bindings"]:
        m = b.get("match", {})
        p = m.get("peer", {})
        if p.get("kind") == "group":
            gid = p["id"]
            info = groups["groups"].get(gid, {})
            result.append({
                "group_id": gid,
                "group_name": info.get("name", "未知"),
                "agent_id": b["agentId"],
                "comment": b.get("comment", "")
            })
        elif "peer" not in m:
            result.append({
                "group_id": "*",
                "group_name": "所有未绑定群",
                "agent_id": b["agentId"],
                "comment": b.get("comment", "catch-all")
            })
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_bind(group_id, agent_id, group_name=""):
    cfg = load_config()
    idx, existing = find_binding(cfg, group_id)
    if existing:
        print(json.dumps({"error": f"群 {group_id} 已绑定到 {existing['agentId']}，请用 reassign", "current_agent": existing["agentId"]}, ensure_ascii=False))
        return
    # Insert before catch-all (last binding without peer)
    insert_pos = len(cfg["bindings"])
    for i, b in enumerate(cfg["bindings"]):
        if "peer" not in b.get("match", {}):
            insert_pos = i
            break
    new_binding = {
        "agentId": agent_id,
        "comment": f"{agent_id} 对接飞书群 {group_name or group_id}",
        "match": {"channel": "feishu", "peer": {"kind": "group", "id": group_id}}
    }
    cfg["bindings"].insert(insert_pos, new_binding)
    save_config(cfg)
    # Update groups DB
    groups = load_groups()
    groups["groups"][group_id] = {"name": group_name or group_id, "agent_id": agent_id}
    save_groups(groups)
    print(json.dumps({"ok": True, "action": "bind", "group_id": group_id, "agent_id": agent_id, "position": insert_pos}, ensure_ascii=False))

def cmd_unbind(group_id):
    cfg = load_config()
    idx, existing = find_binding(cfg, group_id)
    if not existing:
        print(json.dumps({"error": f"群 {group_id} 无绑定"}, ensure_ascii=False))
        return
    cfg["bindings"].pop(idx)
    save_config(cfg)
    groups = load_groups()
    if group_id in groups["groups"]:
        del groups["groups"][group_id]
        save_groups(groups)
    print(json.dumps({"ok": True, "action": "unbind", "group_id": group_id}, ensure_ascii=False))

def cmd_reassign(group_id, agent_id):
    cfg = load_config()
    idx, existing = find_binding(cfg, group_id)
    if not existing:
        print(json.dumps({"error": f"群 {group_id} 无绑定，请用 bind"}, ensure_ascii=False))
        return
    old_agent = existing["agentId"]
    cfg["bindings"][idx]["agentId"] = agent_id
    cfg["bindings"][idx]["comment"] = f"{agent_id} 对接飞书群 {group_id}"
    save_config(cfg)
    groups = load_groups()
    groups["groups"][group_id] = {"name": groups["groups"].get(group_id, {}).get("name", group_id), "agent_id": agent_id}
    save_groups(groups)
    print(json.dumps({"ok": True, "action": "reassign", "group_id": group_id, "from": old_agent, "to": agent_id}, ensure_ascii=False))

def cmd_info(group_id):
    cfg = load_config()
    groups = load_groups()
    idx, existing = find_binding(cfg, group_id)
    info = groups["groups"].get(group_id, {})
    result = {
        "group_id": group_id,
        "group_name": info.get("name", "未知"),
        "bound": existing is not None,
        "agent_id": existing["agentId"] if existing else None,
        "all_info": info
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_agents():
    cfg = load_config()
    result = []
    for a in cfg["agents"]["list"]:
        ident = a.get("identity", {})
        result.append({
            "id": a["id"],
            "name": ident.get("name", "?"),
            "emoji": ident.get("emoji", "?"),
            "theme": ident.get("theme", "?")
        })
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    cmd = args[0]
    if cmd == "list":
        cmd_list()
    elif cmd == "bind":
        if len(args) < 3:
            print('用法: bind <group_id> <agent_id> [群名]')
            sys.exit(1)
        cmd_bind(args[1], args[2], args[3] if len(args) > 3 else "")
    elif cmd == "unbind":
        if len(args) < 2:
            print('用法: unbind <group_id>')
            sys.exit(1)
        cmd_unbind(args[1])
    elif cmd == "reassign":
        if len(args) < 3:
            print('用法: reassign <group_id> <agent_id>')
            sys.exit(1)
        cmd_reassign(args[1], args[2])
    elif cmd == "info":
        if len(args) < 2:
            print('用法: info <group_id>')
            sys.exit(1)
        cmd_info(args[1])
    elif cmd == "agents":
        cmd_agents()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
