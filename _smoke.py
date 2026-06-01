import sys, asyncio
sys.path.insert(0, "src")
sys.argv = [sys.argv[0]]  # evitar que argparse vea los args del runner

import metabase_mcp_server as srv
from application.services import DatabaseService, DashboardService


async def main():
    # 1) Registro de tools (no requiere red)
    tools = await srv.mcp.get_tools()
    print(f"TOOL_COUNT={len(tools)}  has_items={'get_dashboard_items' in tools}  has_cards={'get_dashboard_cards' in tools}")

    # 2) Llamadas reales contra Metabase
    await srv.gateway.connect()
    try:
        dbs = await DatabaseService(srv.gateway).list_databases()
        data = dbs.get("data", dbs)
        print(f"DATABASES_OK count={dbs.get('count', 'n/a')}")
        for d in (data if isinstance(data, list) else [])[:5]:
            print("   db:", d.get("id"), d.get("name"), "engine=", d.get("engine"))

        # Opcional: pasar un dashboard_id como argumento para probar get_dashboard_cards
        if len(sys.argv) > 1:
            did = int(sys.argv[1])
            cards = await DashboardService(srv.gateway).get_cards(did)
            print(f"DASHBOARD_CARDS_OK dashboard={did} count={cards.get('count')}")
    finally:
        await srv.gateway.close()


asyncio.run(main())
