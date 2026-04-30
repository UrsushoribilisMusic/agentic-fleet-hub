# Legacy Gemma Onboarding Guide

Status: superseded for the live fleet slot. The `gemma` heartbeat key now runs
Qwen Coder locally via aichat/Ollama. Keep this guide only as historical context
for adding a generic local LLM agent.

For the active runtime contract, see `AGENTS/CONTEXT/qwen_coder_runtime.md`.

# Gemma Onboarding Guide: Adding Local LLM Agents to Your Fleet

**Version**: 1.0
**Last Updated**: April 4, 2026
**Status**: Production Ready

---

## 🎯 Overview

This guide provides step-by-step instructions for onboarding Gemma (or any local LLM agent) to your agentic fleet. The process covers infrastructure setup, fleet integration, and production deployment.

---

## 📋 Prerequisites

### System Requirements
- **macOS 13+** or **Linux** (Ubuntu 22.04+ recommended)
- **Python 3.14+**
- **8GB+ RAM** (16GB recommended for smooth operation)
- **20GB+ disk space** (for models and dependencies)
- **Homebrew** (for macOS package management)

### Required Tools
```bash
# Install prerequisites
brew install git wget curl sqlite3
```

---

## 🚀 Step 1: Infrastructure Setup

### 1.1 Install aichat

```bash
# Install aichat (LLM interaction framework)
brew install aichat

# Verify installation
aichat --version
```

### 1.2 Download Gemma4 Model

```bash
# Download the Gemma4 model (e4b variant - 4.8B parameters)
aichat download gemma4:e4b

# Verify model download
aichat models list
```

**Expected Output:**
```
gemma4:e4b    4.8B    Ready    /Users/you/.cache/aichat/models/gemma4-e4b.gguf
```

### 1.3 Test Local Model

```bash
# Test Gemma4 with a simple prompt
echo "Explain agentic workflows in 3 sentences" | aichat --model gemma4:e4b
```

**Success Criteria:**
- ✅ Response within 200ms
- ✅ Coherent, relevant answer
- ✅ No errors or timeouts

---

## 🤖 Step 2: Agent Configuration

### 2.1 Create Agent Directory Structure

```bash
# Create Gemma's workspace
mkdir -p ~/fleet/gemma
mkdir -p ~/fleet/gemma/workspace
mkdir -p ~/fleet/logs
```

### 2.2 Create Core Files

#### 2.2.1 Agent Mandate (`GEMMA.md`)

```bash
cat > ~/fleet/gemma/GEMMA.md << 'EOF'
# GEMMA CORE MANDATE (Gemma4 via aichat — Fleet Agent)

You are **Gemma**, a local fleet agent running on the Mac Mini. You use function calling to interact with the filesystem, PocketBase, and git. You have no internet access — all operations are local.

---

## Heartbeat Protocol — run every session, no exceptions

### Phase 1 — Orient
1. Run heartbeat check
2. Read MISSION_CONTROL.md
3. Read AGENTS/RULES.md
4. Check inbox for messages
5. Post working heartbeat

### Phase 2 — Peer Review
1. Review peer_review tasks
2. Post feedback/approval comments
3. Never self-approve

### Phase 3 — Task Execution
1. Find assigned todo tasks
2. Complete work systematically
3. Post output comments
4. Set status to peer_review

### Phase 4 — Blockers
- Post questions with @miguel mention
- Set status to waiting_human

### Phase 5 — Knowledge Capture
- Create lessons for reusable insights
- Commit and push changes

### Phase 6 — Sign Off
- Post idle heartbeat
- Update PROGRESS.md
- Check git status and push if needed

---

## Key Paths
- Fleet: /Users/miguelrodriguez/fleet/
- Repo: /Users/miguelrodriguez/projects/agentic-fleet-hub/
- Your workspace: /Users/miguelrodriguez/fleet/gemma/workspace/
- Logs: /Users/miguelrodriguez/fleet/logs/gemma.log

## Rules
- Never commit secrets
- Push every commit immediately
- Only work on MISSION_CONTROL.md tasks
- Check inbox before anything else
- No self-approval (Rule #6)
EOF
```

#### 2.2.2 Progress Tracking (`PROGRESS.md`)

```bash
cat > ~/fleet/gemma/PROGRESS.md << 'EOF'
# Gemma Session Progress

## Onboarded: $(date +%Y-%m-%d)

Gemma is a local fleet agent running Gemma4 via aichat with RAG on the ~/fleet/gemma/ directory.

### Session History

- **Session 1**: [Date] - Initial onboarding and testing
- **Session 2**: [Date] - First task execution
- **Session 3**: [Date] - Performance optimization

### Performance Metrics

- **Tasks Completed**: 0
- **Code Committed**: 0 lines
- **Lessons Created**: 0
- **Uptime**: 0%

### Issues Encountered

- None yet

### Improvements Made

- None yet
EOF
```

---

## 🔧 Step 3: Fleet Integration

### 3.1 Update Dispatcher

Edit `~/fleet/dispatcher.py`:

```python
# Add to AGENT_COMMANDS dictionary
AGENT_COMMANDS = {
    # ... existing agents ...
    "gemma": [
        "/opt/homebrew/bin/aichat",
        "--rag", 
        ".",  # RAG on current directory
        "Run your heartbeat protocol. Read GEMMA.md first."
    ],
}
```

### 3.2 Update Heartbeat Check

Edit `~/fleet/heartbeat_check.py`:

```python
# Add Gemma to agent aliases
AGENT_ALIASES_DEFAULT = {
    "clau": ["clau", "claude"],
    "misty": ["misty", "mistral"],
    "gem": ["gem", "gemini"],
    "codi": ["codi", "codex"],
    "gemma": ["gemma"],  # Add this line
}

# Update argument parser help
parser.add_argument("--agent", required=True, 
                   choices=AGENT_ALIASES_DEFAULT.keys(),
                   help="Agent identity (clau / misty / gem / codi / gemma)")  # Add gemma
```

### 3.3 Update Fleet Metadata

Edit `~/fleet/fleet_meta.json`:

```json
{
  "meta": {
    "installation": {
      "repo_path": "/Users/miguelrodriguez/projects/agentic-fleet-hub"
    }
  },
  "team": [
    {
      "name": "Gemma",
      "avatar": "GM",
      "roleTitle": "Code Implementation & Review",
      "roleDesc": "High-throughput coding, testing, and review with Gemma model.",
      "runtime": "Local",
      "skills": ["Implementation", "Testing", "Code Review"],
      "heartbeatKey": "gemma",
      "memoryLink": "https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/GEMMA.md"
    }
    // ... other team members ...
  ]
}
```

### 3.4 Update Telegram Bridge

Edit `~/fleet/telegram_bridge.py`:

```python
# Add Gemma to bot commands
BOT_COMMANDS = [
    # ... existing commands ...
    {"command": "gemma", "description": "Message Gemma (local Gemma4 via aichat)"},
]

# Add to agent list
AGENT_LIST = ["clau", "gem", "codi", "misty", "gemma", "openclaw"]
```

---

## 🗃 Step 4: Database Integration

### 4.1 Update PocketBase Schema

```bash
# Navigate to PocketBase directory
cd ~/fleet/pocketbase

# Create migration file
cat > pb_migrations/$(date +%s)_add_gemma_to_agents.js << 'EOF'
/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4");

  // Find and update assigned_agent field
  for (let i = 0; i < collection.schema.length; i++) {
    if (collection.schema[i].name === "assigned_agent") {
      if (!collection.schema[i].options.values.includes("gemma")) {
        collection.schema[i].options.values.push("gemma");
      }
      break;
    }
  }

  return dao.saveCollection(collection);
}, (db) => {
  // Downgrade logic
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4");

  for (let i = 0; i < collection.schema.length; i++) {
    if (collection.schema[i].name === "assigned_agent") {
      collection.schema[i].options.values = 
        collection.schema[i].options.values.filter(v => v !== "gemma");
      break;
    }
  }

  return dao.saveCollection(collection);
});
EOF

# Apply migration
./pocketbase migrate up

# Restart PocketBase
pkill pocketbase || true
nohup ./pocketbase serve --http="0.0.0.0:8090" > /dev/null 2>&1 &
```

### 4.2 Verify Schema Update

```bash
# Check the updated schema
curl -s http://localhost:8090/api/collections/tasks/schema | \
  python3 -c "import sys, json; data = json.load(sys.stdin); 
  agent_field = next(f for f in data['schema'] if f['name'] == 'assigned_agent');
  print('Valid agents:', agent_field['options']['values'])"
```

**Expected Output:**
```
Valid agents: ['scout', 'echo', 'closer', 'clau', 'gem', 'codi', 'misty', 'gemma']
```

---

## 🧪 Step 5: Testing & Validation

### 5.1 Test Heartbeat Functionality

```bash
# Test Gemma's heartbeat
cd ~/fleet/gemma
python3 ~/fleet/heartbeat_check.py --agent gemma
```

**Expected Output:**
```
[heartbeat:gemma] No changes. Going idle.
```

### 5.2 Test Task Assignment

```bash
# Create a test task for Gemma
curl -X POST http://localhost:8090/api/collections/tasks/records \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Gemma Test Task",
    "assigned_agent": "gemma",
    "status": "todo",
    "description": "Test task to verify Gemma integration",
    "source": "test"
  }'
```

### 5.3 Test Telegram Integration

```bash
# Send a test message to Gemma via Telegram
# (Replace with your actual Telegram setup)
echo "Testing Gemma integration" | 
  curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
  -d "chat_id=$TELEGRAM_CHAT_ID" \
  -d "text=/gemma Testing Gemma integration"
```

---

## 🚀 Step 6: Production Deployment

### 6.1 Start Fleet Services

```bash
# Start dispatcher
cd ~/fleet
nohup python3 dispatcher.py > logs/dispatcher.log 2>&1 &

# Start Telegram bridge
nohup python3 telegram_bridge.py > logs/telegram_bridge.log 2>&1 &

# Verify services are running
ps aux | grep -E "dispatcher|telegram_bridge" | grep -v grep
```

### 6.2 Monitor Initial Operation

```bash
# Monitor Gemma's log
tail -f ~/fleet/logs/gemma.log

# Check dispatcher log
tail -f ~/fleet/logs/dispatcher.log

# Verify heartbeat
curl -s "http://localhost:8090/api/collections/heartbeats/records?filter=agent%3D%22gemma%22" | \
  python3 -m json.tool
```

### 6.3 Create First Production Task

```bash
# Assign a real task to Gemma
curl -X POST http://localhost:8090/api/collections/tasks/records \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Implement documentation analyzer",
    "assigned_agent": "gemma",
    "status": "todo",
    "description": "Create a Python script to analyze documentation completeness and generate health reports. See DOCUMENTATION_MAP.md template.",
    "source": "production",
    "priority": "high",
    "required_skills": ["Implementation", "Code Review"]
  }'
```

---

## 📊 Step 7: Performance Tuning

### 7.1 Optimize aichat Configuration

```bash
# Create aichat config for Gemma
mkdir -p ~/.config/aichat
cat > ~/.config/aichat/config.json << 'EOF'
{
  "models": {
    "gemma4:e4b": {
      "temperature": 0.3,
      "top_p": 0.9,
      "max_tokens": 4096,
      "repeat_penalty": 1.1
    }
  },
  "default_model": "gemma4:e4b",
  "rag": {
    "enabled": true,
    "chunk_size": 512,
    "chunk_overlap": 64
  }
}
EOF
```

### 7.2 Monitor Resource Usage

```bash
# Monitor Gemma's resource consumption
top -pid $(pgrep -f "aichat.*gemma")

# Check memory usage
ps -p $(pgrep -f "aichat.*gemma") -o %mem,cmd
```

### 7.3 Adjust Based on Performance

**Optimization Guide:**

| Issue | Symptom | Solution |
|-------|---------|----------|
| High CPU | >80% CPU usage | Reduce temperature to 0.2 |
| High Memory | >2GB RAM usage | Limit max_tokens to 2048 |
| Slow Response | >500ms response | Enable RAG caching |
| Hallucinations | Incorrect facts | Increase repeat_penalty to 1.2 |

---

## 🎯 Step 8: Ongoing Maintenance

### 8.1 Regular Updates

```bash
# Update Gemma model (quarterly)
aichat update gemma4:e4b

# Update aichat (monthly)
brew upgrade aichat
```

### 8.2 Performance Monitoring

```bash
# Create monitoring script
cat > ~/fleet/monitor_gemma.sh << 'EOF'
#!/bin/bash

# Check Gemma's heartbeat
echo "=== Gemma Heartbeat ==="
curl -s "http://localhost:8090/api/collections/heartbeats/records?filter=agent%3D%22gemma%22&sort=-updated&perPage=1" | \
  jq -r '.items[0] | "Status: \(.status), Last seen: \(.updated)"' || echo "No heartbeat found"

# Check active tasks
echo -e "\n=== Gemma's Tasks ==="
curl -s "http://localhost:8090/api/collections/tasks/records?filter=assigned_agent%3D%22gemma%22%20&&%20status%3D%22in_progress%22" | \
  jq -r '.items[] | "\(.id): \(.title) - \(.status)"' || echo "No active tasks"

# Check resource usage
echo -e "\n=== Resource Usage ==="
ps -p $(pgrep -f "aichat.*gemma" 2>/dev/null) -o %cpu,%mem,cmd 2>/dev/null || echo "Gemma not running"
EOF

chmod +x ~/fleet/monitor_gemma.sh
```

### 8.3 Backup and Recovery

```bash
# Backup Gemma's data
cat > ~/fleet/backup_gemma.sh << 'EOF'
#!/bin/bash

# Backup Gemma's files
BACKUP_DIR="~/fleet/backups/gemma/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

cp -r ~/fleet/gemma/* "$BACKUP_DIR/"
echo "Gemma backup created: $BACKUP_DIR"
EOF

chmod +x ~/fleet/backup_gemma.sh
```

---

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Issue 1: Gemma not responding to tasks

**Symptoms:**
- Tasks assigned to Gemma stay in "todo" status
- No heartbeat records
- Dispatcher logs show "No command configured"

**Solutions:**
1. Verify `AGENT_COMMANDS` in `dispatcher.py` includes Gemma
2. Check `aichat` is installed: `which aichat`
3. Test Gemma manually: `echo "test" | aichat --model gemma4:e4b`
4. Check dispatcher logs: `tail -f ~/fleet/logs/dispatcher.log`

#### Issue 2: PocketBase rejects Gemma assignment

**Symptoms:**
- "Invalid value gemma" error when assigning tasks
- Task creation fails with validation error

**Solutions:**
1. Verify schema migration was applied
2. Check current valid values:
   ```bash
   curl -s http://localhost:8090/api/collections/tasks/schema | jq '.schema[] | select(.name == "assigned_agent") | .options.values'
   ```
3. If missing, apply migration manually or restart PocketBase

#### Issue 3: High resource usage

**Symptoms:**
- CPU > 90% for extended periods
- Memory > 4GB usage
- System becomes unresponsive

**Solutions:**
1. Limit Gemma's token usage: `--max-tokens 2048`
2. Reduce temperature: `--temperature 0.2`
3. Add swap space if on Linux
4. Consider smaller model if resources are constrained

#### Issue 4: RAG not working

**Symptoms:**
- Gemma doesn't reference local files
- Responses seem generic
- No file access evident

**Solutions:**
1. Verify RAG is enabled: `aichat --rag . "test query"`
2. Check file permissions: `ls -la ~/fleet/gemma/`
3. Test with explicit files: `aichat --rag GEMMA.md "what's my mandate?"`
4. Verify file formats are supported (`.md`, `.txt`, `.py`)

---

## ✅ Checklist: Gemma Onboarding Complete

- [ ] **Infrastructure**: aichat installed and Gemma4 model downloaded
- [ ] **Configuration**: Agent directory created with GEMMA.md and PROGRESS.md
- [ ] **Fleet Integration**: dispatcher.py, heartbeat_check.py, telegram_bridge.py updated
- [ ] **Metadata**: fleet_meta.json includes Gemma profile
- [ ] **Database**: PocketBase schema updated with "gemma" option
- [ ] **Testing**: Heartbeat, task assignment, and Telegram integration verified
- [ ] **Deployment**: Services restarted and monitoring configured
- [ ] **Documentation**: Onboarding process documented

---

## 📚 Additional Resources

### Official Documentation
- [aichat Documentation](https://github.com/sigoden/aichat)
- [Gemma4 Model Card](https://ai.google.dev/gemma)
- [Ollama Documentation](https://ollama.ai)

### Fleet-Specific Resources
- [Gemma Mandate Template](fleet/gemma/GEMMA.md)
- [Agent Rules](AGENTS/RULES.md)
- [Dispatcher Configuration](dispatcher.py)

### Community Support
- **Telegram**: `/help` for command reference
- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Share experiences and best practices

---

## 🎉 Success! What's Next?

With Gemma successfully onboarded, you now have a **local, high-performance coding agent** in your fleet. Here are some ideas for leveraging Gemma's capabilities:

### Immediate Next Steps
1. **Assign documentation tasks** to Gemma
2. **Set up regular code review** rotations
3. **Create onboarding tasks** for new agents
4. **Establish performance baselines**

### Advanced Integrations
1. **Continuous Integration**: Hook Gemma into your CI pipeline
2. **Code Quality**: Automated code reviews and suggestions
3. **Knowledge Base**: Build a fleet-specific RAG corpus
4. **Specialization**: Train Gemma on domain-specific codebases

### Long-Term Roadmap
1. **Multi-Agent Collaboration**: Gemma + Clau pair programming
2. **Autonomous Development**: Full feature implementation
3. **Self-Improvement**: Gemma optimizing her own performance
4. **Fleet Expansion**: Onboard additional local agents

---

> "The future of software development is not humans vs. AI, but humans AND AI working together in perfect harmony."
> — Agentic Fleet Manifesto

By completing this onboarding guide, you've taken a major step toward that future. Gemma is now an integral part of your engineering team—ready to tackle implementation tasks, perform code reviews, and help build the next generation of software.

**Welcome to the future of autonomous engineering!** 🚀
