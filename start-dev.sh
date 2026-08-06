#!/bin/bash
# NuDM 开发环境启动脚本（无需 Docker / sudo / Redis / PostgreSQL）
# 使用 SQLite + 直接运行前后端进程
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

export PYTHONPATH="$BACKEND_DIR"
export PATH="/home/yjj/.conda/envs/py12/bin:/usr/local/bin:$PATH"
export DATABASE_URL="sqlite+aiosqlite:///$BACKEND_DIR/nudm.db"
export SECRET_KEY="nudm-dev-secret-key-20240724"

echo "============================================"
echo " NuDM 开发环境启动"
echo "============================================"
echo " 后端 (FastAPI):  http://localhost:8080"
echo " API 文档:        http://localhost:8080/docs"
echo " 前端 (Next.js):  http://localhost:3001"
echo " 数据库:          $BACKEND_DIR/nudm.db (SQLite)"
echo "============================================"

# ---------- 步骤 1: 安装依赖 ----------
echo ""
echo "[1/4] 检查 Python 依赖..."
cd "$BACKEND_DIR"
pip install -q sqlalchemy aiosqlite fastapi uvicorn \
  'pydantic>=2' pydantic-settings python-jose passlib \
  python-multipart httpx feedparser lxml openai \
  'bcrypt<4.1' python-dotenv 2>&1 | grep -v 'already satisfied' || true
echo "  ✅ 依赖已就绪"

# ---------- 步骤 2: 初始化 SQLite 数据库 + 种子数据 ----------
echo ""
echo "[2/4] 初始化 SQLite 数据库..."

rm -f "$BACKEND_DIR/nudm.db"

python3 << 'PYEOF'
import sqlite3, uuid, os
from datetime import datetime, timezone
from passlib.context import CryptContext

db_path = os.environ.get("DATABASE_URL", "").replace("sqlite+aiosqlite:///", "")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
now = datetime.now(timezone.utc).isoformat()

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys=ON")
c = conn.cursor()

# --- 用户表 ---
c.execute("""CREATE TABLE users (
    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, avatar_url TEXT, role TEXT DEFAULT 'user',
    is_active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT)""")

# --- 数据源表 ---
c.execute("""CREATE TABLE data_sources (
    id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, base_url TEXT NOT NULL,
    api_type TEXT NOT NULL, rate_limit INTEGER DEFAULT 60,
    is_active INTEGER DEFAULT 1, config TEXT, created_at TEXT)""")

# --- 抓取任务表 ---
c.execute("""CREATE TABLE crawl_tasks (
    id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES data_sources(id),
    keyword TEXT NOT NULL, status TEXT DEFAULT 'pending',
    papers_fetched INTEGER DEFAULT 0, papers_new INTEGER DEFAULT 0,
    error_message TEXT, started_at TEXT, finished_at TEXT, created_at TEXT)""")

# --- 论文主表 ---
c.execute("""CREATE TABLE papers (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, title_en TEXT, abstract TEXT,
    abstract_en TEXT, doi TEXT UNIQUE, arxiv_id TEXT UNIQUE, publish_date TEXT,
    citation_count INTEGER DEFAULT 0, pdf_url TEXT, source_url TEXT,
    language TEXT DEFAULT 'en', relevance_score REAL, hot_score REAL,
    is_hidden INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT)""")

c.execute("CREATE INDEX IF NOT EXISTS idx_papers_arxiv ON papers(arxiv_id)")
c.execute("CREATE INDEX IF NOT EXISTS idx_papers_date ON papers(publish_date DESC)")

# --- 论文来源表 ---
c.execute("""CREATE TABLE paper_sources (
    id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES data_sources(id),
    external_id TEXT NOT NULL, fetched_at TEXT,
    UNIQUE(paper_id, source_id))""")

# --- 作者表 ---
c.execute("""CREATE TABLE authors (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, name_normalized TEXT NOT NULL,
    affiliation TEXT, orcid TEXT UNIQUE, created_at TEXT)""")
c.execute("CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name_normalized)")

# --- 论文作者关联表 ---
c.execute("""CREATE TABLE paper_authors (
    id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    author_id TEXT NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    author_order INTEGER NOT NULL, UNIQUE(paper_id, author_id))""")

# --- 机构表 ---
c.execute("""CREATE TABLE institutions (
    id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, country TEXT, created_at TEXT)""")

# --- 论文机构关联表 ---
c.execute("""CREATE TABLE paper_institutions (
    id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    institution_id TEXT NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    UNIQUE(paper_id, institution_id))""")

# --- 专题表 ---
c.execute("""CREATE TABLE topics (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, slug TEXT UNIQUE NOT NULL,
    description TEXT, parent_id TEXT REFERENCES topics(id),
    sort_order INTEGER DEFAULT 0, icon TEXT, keywords TEXT,
    paper_count INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, created_at TEXT)""")

# --- 论文专题关联表 ---
c.execute("""CREATE TABLE paper_topics (
    id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    confidence REAL DEFAULT 1.0, is_ai_classified INTEGER DEFAULT 0,
    created_at TEXT, UNIQUE(paper_id, topic_id))""")

# --- 实验组表 ---
c.execute("""CREATE TABLE experiments (
    id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, full_name TEXT,
    description TEXT, topic_id TEXT REFERENCES topics(id),
    website TEXT, is_active INTEGER DEFAULT 1, created_at TEXT)""")

# --- 论文实验组关联表 ---
c.execute("""CREATE TABLE paper_experiments (
    id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    experiment_id TEXT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    UNIQUE(paper_id, experiment_id))""")

# --- 标签表 ---
c.execute("""CREATE TABLE tags (
    id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, slug TEXT UNIQUE NOT NULL, created_at TEXT)""")

# --- 论文标签关联表 ---
c.execute("""CREATE TABLE paper_tags (
    id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    tag_id TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(paper_id, tag_id))""")

# --- AI 摘要表 ---
c.execute("""CREATE TABLE ai_summaries (
    id TEXT PRIMARY KEY, paper_id TEXT UNIQUE NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    summary_cn TEXT, summary_en TEXT, keywords_extracted TEXT,
    contribution TEXT, method TEXT, result TEXT,
    model TEXT, tokens_used INTEGER, quality_flag TEXT DEFAULT 'unreviewed',
    generated_at TEXT, reviewed_by TEXT REFERENCES users(id), reviewed_at TEXT)""")

# --- 收藏表 ---
c.execute("""CREATE TABLE favorites (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    note TEXT, created_at TEXT, UNIQUE(user_id, paper_id))""")

# --- 订阅表 ---
c.execute("""CREATE TABLE subscriptions (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL, target_id TEXT, keyword TEXT,
    frequency TEXT DEFAULT 'daily', is_active INTEGER DEFAULT 1,
    created_at TEXT, updated_at TEXT)""")

# --- 通知表 ---
c.execute("""CREATE TABLE notifications (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL, title TEXT NOT NULL, content TEXT,
    reference_id TEXT, reference_type TEXT,
    is_read INTEGER DEFAULT 0, created_at TEXT, read_at TEXT)""")
c.execute("CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id, is_read, created_at DESC)")

# --- 操作日志表 ---
c.execute("""CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id),
    action TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id TEXT,
    detail TEXT, ip_address TEXT, created_at TEXT)""")

# --- 人工反馈表 ---
c.execute("""CREATE TABLE human_feedback (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
    entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL, content TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    resolved_by TEXT REFERENCES users(id), resolved_at TEXT, created_at TEXT)""")

# --- 种子数据 ---
uid = str(uuid.uuid4)

# 管理员
c.execute("INSERT INTO users (id,email,username,password_hash,role,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
    (uid, "admin@nudm.dev", "admin", pwd_context.hash("admin123"), "admin", now, now))

# 8 个专题
topics_seed = [
    (str(uuid.uuid4()), "暗物质直接探测", "dark-matter-direct", "通过地下实验室直接探测暗物质粒子。", 1, "direct detection,WIMP-nucleon,liquid xenon,low background,TPC,nuclear recoil"),
    (str(uuid.uuid4()), "暗物质间接探测", "dark-matter-indirect", "通过天文观测寻找暗物质信号。", 2, "indirect detection,gamma-ray,cosmic ray,dwarf galaxy"),
    (str(uuid.uuid4()), "WIMP", "wimp", "弱相互作用大质量粒子。", 3, "WIMP,thermal relic,SUSY,freeze-out"),
    (str(uuid.uuid4()), "Axion", "axion", "轴子与类轴子粒子。", 4, "axion,ALP,strong CP,haloscope,helioscope"),
    (str(uuid.uuid4()), "Light-Mediator DM", "light-mediator-dark-matter", "轻媒介暗物质模型。", 5, "light mediator,dark photon,vector portal,fixed target"),
    (str(uuid.uuid4()), "CEvNS", "cevns", "中微子相干弹性散射。", 6, "CEvNS,coherent scattering,nuclear recoil,reactor neutrino"),
    (str(uuid.uuid4()), "0νββ", "0nubb", "无中微子双贝塔衰变。", 7, "neutrinoless double beta decay,Majorana,lepton number violation"),
    (str(uuid.uuid4()), "Sterile Neutrino", "sterile-neutrino", "惰性中微子理论与实验。", 8, "sterile neutrino,short baseline,oscillation anomaly,reactor antineutrino"),
]
topic_map = {}
for tid, name, slug, desc, sort_order, keywords in topics_seed:
    topic_map[slug] = tid
    c.execute("INSERT INTO topics (id,name,slug,description,sort_order,keywords,created_at) VALUES (?,?,?,?,?,?,?)",
        (tid, name, slug, desc, sort_order, keywords, now))

# 20 个实验组
experiments_seed = [
    ("XENONnT", "XENONnT Dark Matter Experiment", "dark-matter-direct"),
    ("LZ", "LUX-ZEPLIN", "dark-matter-direct"),
    ("PandaX-4T", "PandaX-4T", "dark-matter-direct"),
    ("DarkSide-20k", "DarkSide-20k", "dark-matter-direct"),
    ("Fermi-LAT", "Fermi Large Area Telescope", "dark-matter-indirect"),
    ("AMS-02", "Alpha Magnetic Spectrometer", "dark-matter-indirect"),
    ("IceCube", "IceCube Neutrino Observatory", "dark-matter-indirect"),
    ("DAMPE", "DArk Matter Particle Explorer", "dark-matter-indirect"),
    ("ADMX", "Axion Dark Matter eXperiment", "axion"),
    ("CAST", "CERN Axion Solar Telescope", "axion"),
    ("NA64", "NA64", "light-mediator-dark-matter"),
    ("Belle II", "Belle II", "light-mediator-dark-matter"),
    ("COHERENT", "COHERENT", "cevns"),
    ("CONUS", "COherent NeUtrino Scattering", "cevns"),
    ("LEGEND", "LEGEND", "0nubb"),
    ("CUORE", "Cryogenic Underground Observatory for Rare Events", "0nubb"),
    ("KamLAND-Zen", "KamLAND-Zen", "0nubb"),
    ("MiniBooNE", "MiniBooNE", "sterile-neutrino"),
    ("MicroBooNE", "MicroBooNE", "sterile-neutrino"),
    ("STEREO", "STEREO", "sterile-neutrino"),
]
for name, full_name, slug in experiments_seed:
    c.execute("INSERT INTO experiments (id,name,full_name,topic_id,created_at) VALUES (?,?,?,?,?)",
        (str(uuid.uuid4()), name, full_name, topic_map[slug], now))

# 数据源
c.execute("INSERT INTO data_sources (id,name,base_url,api_type,rate_limit,created_at) VALUES (?,?,?,?,?,?)",
    (str(uuid.uuid4()), "arXiv", "https://export.arxiv.org/api/query", "arxiv", 60, now))
c.execute("INSERT INTO data_sources (id,name,base_url,api_type,rate_limit,created_at) VALUES (?,?,?,?,?,?)",
    (str(uuid.uuid4()), "INSPIRE-HEP", "https://inspirehep.net/api", "inspire", 100, now))

conn.commit()
t_count = c.execute("SELECT count(*) FROM topics").fetchone()[0]
e_count = c.execute("SELECT count(*) FROM experiments").fetchone()[0]
ds_count = c.execute("SELECT count(*) FROM data_sources").fetchone()[0]
u_count = c.execute("SELECT count(*) FROM users").fetchone()[0]
print(f"  写入: {t_count} 专题 + {e_count} 实验组 + {ds_count} 数据源 + {u_count} 用户")
conn.close()
PYEOF

echo "  ✅ SQLite 数据库初始化完成"

# ---------- 步骤 3: 启动后端 ----------
echo ""
echo "[3/4] 启动 FastAPI 后端 (端口 8080)..."
cd "$BACKEND_DIR"

# 杀掉旧进程
kill $(lsof -ti:8080) 2>/dev/null || true
sleep 1

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"

# 等待后端启动
for i in $(seq 1 10); do
    sleep 1
    curl -s http://localhost:8080/health &>/dev/null && echo "  ✅ 后端已就绪" && break
    [ $i -eq 10 ] && echo "  ⚠️ 后端启动超时，查看日志"
done

# 验证 API
echo "  测试 API:"
curl -s http://localhost:8080/topics | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'    专题数: {len(d)}')" 2>/dev/null || true
curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@nudm.dev","password":"admin123"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'    登录成功: {d[\"user\"][\"username\"]} ({d[\"user\"][\"role\"]})')" 2>/dev/null || true

# ---------- 步骤 4: 启动前端 ----------
echo ""
echo "[4/4] 启动 Next.js 前端 (端口 3001)..."
cd "$FRONTEND_DIR"

kill $(lsof -ti:3001) 2>/dev/null || true
sleep 1

node_modules/.bin/next dev -p 3001 &
FRONTEND_PID=$!
echo "  前端 PID: $FRONTEND_PID"

sleep 5

echo ""
echo "============================================"
echo " ✅ NuDM 开发环境已启动"
echo ""
echo " 前端:    http://localhost:3001"
echo " 后端:    http://localhost:8080"
echo " API 文档: http://localhost:8080/docs"
echo " 管理员:  admin@nudm.dev / admin123"
echo " 数据库:  $BACKEND_DIR/nudm.db"
echo ""
echo " 按 Ctrl+C 停止"
echo "============================================"

trap "echo '正在停止...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
