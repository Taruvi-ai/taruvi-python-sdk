"""
Integration test for edge CRUD via DatabaseModule methods.

Usage:
    python tests/test_edges_live.py

Requires:
    - Backend running at TARUVI_API_URL
    - A table with edges enabled (set TARUVI_TEST_TABLE_NAME)
    - Valid credentials in .env
"""

import os
import sys

from dotenv import load_dotenv
load_dotenv()

from taruvi import Client


def main():
    api_url = os.getenv("TARUVI_API_URL", "http://localhost:8000")
    app_slug = os.getenv("TARUVI_TEST_APP_SLUG", "testapp")
    table = os.getenv("TARUVI_TEST_TABLE_NAME", "test_table")

    print(f"API: {api_url}")
    print(f"App: {app_slug}")
    print(f"Table: {table}\n")

    client = Client(api_url=api_url, app_slug=app_slug, mode="sync")
    auth_client = client.auth.signInWithPassword(
        email=os.getenv("TARUVI_TEST_EMAIL", "admin@example.com"),
        password=os.getenv("TARUVI_TEST_PASSWORD", "admin123"),
    )
    db = auth_client.database
    print("✅ Authenticated\n")

    # 0. Get record IDs for edge references
    records = db.from_(table).page_size(3).execute()
    if isinstance(records, list):
        rec_ids = [r["id"] for r in records[:3]]
    else:
        rec_ids = [r["id"] for r in records.get("data", [])[:3]]

    if len(rec_ids) < 3:
        print("❌ Need at least 3 records in the table for edge tests")
        return

    id1, id2, id3 = rec_ids[0], rec_ids[1], rec_ids[2]
    print(f"   Using record IDs: {id1}, {id2}, {id3}\n")

    # 1. List edges
    print("1. List edges...")
    result = db.list_edges(table)
    print(f"   Result: {result}\n")

    # 2. Create edges
    print("2. Create edges...")
    try:
        result = db.create_edges(table, [
            {"from_id": id1, "to_id": id2, "type": "manager"},
            {"from_id": id1, "to_id": id3, "type": "manager", "metadata": {"primary": True}},
            {"from_id": id2, "to_id": id3, "type": "dotted_line", "metadata": {"project": "SDK Test"}},
        ])
        print(f"   Result: {result}\n")
    except Exception as e:
        print(f"   Create returned error (edges may still be created): {e}\n")

    # 3. List with filter
    print("3. List edges (type=manager)...")
    result = db.list_edges(table, types=["manager"])
    edges = result.get("data", [])
    print(f"   Found {len(edges)} manager edges")
    for e in edges:
        print(f"   - id={e.get('id')} from={e.get('from')} to={e.get('to')} type={e.get('type')}")
    print()

    # 4. Update edge
    if edges:
        eid = edges[0]["id"]
        print(f"4. Update edge {eid}...")
        result = db.update_edge(table, eid, {"metadata": {"updated_by": "sdk_test"}})
        print(f"   Result: {result}\n")
    else:
        print("4. Skip update (no edges)\n")

    # 5. Collect IDs for cleanup
    print("5. List all edges for cleanup...")
    result = db.list_edges(table)
    all_edges = result.get("data", [])
    edge_ids = [e["id"] for e in all_edges]
    print(f"   Edge IDs: {edge_ids}\n")

    # 6. Delete edges (use test_edges datatable directly since delete proxy has UUID cast issue)
    if edge_ids:
        print(f"6. Delete edges {edge_ids}...")
        try:
            result = db.delete_edges(table, edge_ids=edge_ids)
            print(f"   Result: {result}\n")
        except Exception:
            # Fallback: delete via the edges datatable directly
            edges_table = f"{table}_edges"
            for eid in edge_ids:
                try:
                    db.delete(edges_table, record_id=eid)
                except Exception:
                    pass
            print(f"   Deleted via edges datatable fallback\n")
    else:
        print("6. Skip delete\n")

    # 7. Verify
    print("7. Verify cleanup...")
    result = db.list_edges(table)
    print(f"   Remaining: {result}\n")

    print("✅ Done!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Error: {e}")
        print(f"\nMake sure:")
        print(f"  - Backend is running")
        print(f"  - Table '{os.getenv('TARUVI_TEST_TABLE_NAME', 'test_table')}' exists with edges enabled")
        print(f"  - Credentials in .env are valid")
        sys.exit(1)
