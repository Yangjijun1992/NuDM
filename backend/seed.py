import asyncio
import uuid
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.topic import Topic, Experiment
from app.models.datasource import DataSource
from app.models.user import User
from app.core.security import get_password_hash


TOPICS_SEED = [
    {
        "name": "暗物质直接探测",
        "slug": "dark-matter-direct",
        "description": "通过地下实验室的高灵敏探测器直接寻找暗物质粒子与普通物质相互作用产生的微弱信号。",
        "sort_order": 1,
        "keywords": ["direct detection", "WIMP-nucleon", "liquid xenon", "low background", "TPC", "nuclear recoil"],
    },
    {
        "name": "暗物质间接探测",
        "slug": "dark-matter-indirect",
        "description": "通过天文观测寻找暗物质湮灭或衰变产生的标准模型粒子信号，包括伽马射线、正电子、反质子、中微子等。",
        "sort_order": 2,
        "keywords": ["indirect detection", "gamma-ray", "cosmic ray", "positron excess", "dwarf galaxy", "galactic center"],
    },
    {
        "name": "WIMP",
        "slug": "wimp",
        "description": "弱相互作用大质量粒子（Weakly Interacting Massive Particles）是最受关注的冷暗物质候选者。",
        "sort_order": 3,
        "keywords": ["WIMP", "thermal relic", "SUSY", "freeze-out", "spin-independent", "spin-dependent"],
    },
    {
        "name": "Axion",
        "slug": "axion",
        "description": "轴子是为解决强 CP 问题而预言的赝标量粒子，同时也是冷暗物质的天然候选者。",
        "sort_order": 4,
        "keywords": ["axion", "ALP", "strong CP", "haloscope", "helioscope", "light-shining-through-wall"],
    },
    {
        "name": "Light-Mediator Dark Matter",
        "slug": "light-mediator-dark-matter",
        "description": "轻媒介暗物质模型假设存在一个 MeV-GeV 量级的轻玻色子作为暗物质与标准模型粒子之间的媒介。",
        "sort_order": 5,
        "keywords": ["light mediator", "dark photon", "vector portal", "scalar portal", "fixed target", "missing energy"],
    },
    {
        "name": "CEvNS",
        "slug": "cevns",
        "description": "中微子相干弹性散射（Coherent Elastic Neutrino-Nucleus Scattering）是低能中微子与原子核的相干过程。",
        "sort_order": 6,
        "keywords": ["CEvNS", "coherent scattering", "nuclear recoil", "reactor neutrino", "spallation neutron source"],
    },
    {
        "name": "0νββ",
        "slug": "0nubb",
        "description": "无中微子双贝塔衰变（Neutrinoless Double Beta Decay）是验证轻子数不守恒的关键过程。",
        "sort_order": 7,
        "keywords": ["neutrinoless double beta decay", "Majorana", "lepton number violation", "0νββ", "germanium", "xenon"],
    },
    {
        "name": "Sterile Neutrino",
        "slug": "sterile-neutrino",
        "description": "惰性中微子是超出标准模型的额外中微子态，不与规范玻色子直接相互作用。",
        "sort_order": 8,
        "keywords": ["sterile neutrino", "short baseline", "oscillation anomaly", "reactor antineutrino", "eV-scale", "keV-scale"],
    },
]

EXPERIMENTS_SEED = [
    {"name": "XENONnT", "full_name": "XENONnT Dark Matter Experiment", "slug": "dark-matter-direct"},
    {"name": "LZ", "full_name": "LUX-ZEPLIN", "slug": "dark-matter-direct"},
    {"name": "PandaX-4T", "full_name": "PandaX-4T", "slug": "dark-matter-direct"},
    {"name": "DarkSide-20k", "full_name": "DarkSide-20k", "slug": "dark-matter-direct"},
    {"name": "Fermi-LAT", "full_name": "Fermi Large Area Telescope", "slug": "dark-matter-indirect"},
    {"name": "AMS-02", "full_name": "Alpha Magnetic Spectrometer", "slug": "dark-matter-indirect"},
    {"name": "IceCube", "full_name": "IceCube Neutrino Observatory", "slug": "dark-matter-indirect"},
    {"name": "DAMPE", "full_name": "DArk Matter Particle Explorer", "slug": "dark-matter-indirect"},
    {"name": "ADMX", "full_name": "Axion Dark Matter eXperiment", "slug": "axion"},
    {"name": "CAST", "full_name": "CERN Axion Solar Telescope", "slug": "axion"},
    {"name": "NA64", "full_name": "NA64", "slug": "light-mediator-dark-matter"},
    {"name": "Belle II", "full_name": "Belle II", "slug": "light-mediator-dark-matter"},
    {"name": "COHERENT", "full_name": "COHERENT", "slug": "cevns"},
    {"name": "CONUS", "full_name": "COherent NeUtrino Scattering", "slug": "cevns"},
    {"name": "LEGEND", "full_name": "LEGEND", "slug": "0nubb"},
    {"name": "CUORE", "full_name": "Cryogenic Underground Observatory for Rare Events", "slug": "0nubb"},
    {"name": "KamLAND-Zen", "full_name": "KamLAND-Zen", "slug": "0nubb"},
    {"name": "MiniBooNE", "full_name": "MiniBooNE", "slug": "sterile-neutrino"},
    {"name": "MicroBooNE", "full_name": "MicroBooNE", "slug": "sterile-neutrino"},
    {"name": "STEREO", "full_name": "STEREO", "slug": "sterile-neutrino"},
]

DATA_SOURCES_SEED = [
    {
        "name": "arXiv",
        "base_url": "https://export.arxiv.org/api/query",
        "api_type": "arxiv",
        "rate_limit": 60,
    },
    {
        "name": "INSPIRE-HEP",
        "base_url": "https://inspirehep.net/api",
        "api_type": "inspire",
        "rate_limit": 100,
    },
]


async def seed():
    async with async_session_factory() as db:
        result = await db.execute(select(Topic).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded, skipping...")
            return

        topics_map: dict[str, uuid.UUID] = {}
        for data in TOPICS_SEED:
            topic = Topic(**data)
            db.add(topic)
            await db.flush()
            topics_map[data["slug"]] = topic.id

        for data in EXPERIMENTS_SEED:
            slug = data.pop("slug")
            data["topic_id"] = topics_map.get(slug)
            db.add(Experiment(**data))

        for data in DATA_SOURCES_SEED:
            db.add(DataSource(**data))

        db.add(User(
            email="admin@nudm.dev",
            username="admin",
            password_hash=get_password_hash("admin123"),
            role="admin",
        ))

        await db.commit()
        print(f"Seeded {len(TOPICS_SEED)} topics, {len(EXPERIMENTS_SEED)} experiments, {len(DATA_SOURCES_SEED)} data sources, and 1 admin user.")


if __name__ == "__main__":
    asyncio.run(seed())
