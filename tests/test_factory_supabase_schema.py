"""Fail-closed contract for CODEN's free Supabase control-plane migration.

No Supabase credentials, cloud calls or model execution are needed in CI.
The live database is checked separately after an operator-approved migration.
"""
from pathlib import Path
import re
import unittest


SQL = Path(__file__).resolve().parents[1] / "supabase" / "migrations" / "20261121032502_coden_factory_control_plane.sql"


class FactorySupabaseSchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8").lower()

    def test_is_private_separate_from_existing_coden_internal(self):
        self.assertIn("create schema if not exists coden_factory", self.sql)
        self.assertNotRegex(self.sql, r"\b(?:alter|drop|truncate)\s+(?:table|schema)\s+(?:if exists\s+)?coden_internal\b")
        self.assertNotIn("create table public.", self.sql)

    def test_migration_has_only_two_bounded_metadata_tables(self):
        names = re.findall(r"create table if not exists (coden_factory\.\w+)", self.sql)
        self.assertCountEqual(names, ["coden_factory.jobs", "coden_factory.job_events"])
        self.assertIn("references coden_factory.jobs(task_id)", self.sql)
        self.assertIn("check (estimated_cost_usd = 0)", self.sql)
        self.assertIn("check (data_classification = 'synthetic')", self.sql)
        self.assertIn("'pending_review'", self.sql)

    def test_rls_for_every_table_and_no_anon_or_authenticated_exposure(self):
        for name in ("jobs", "job_events"):
            self.assertIn(f"alter table coden_factory.{name} enable row level security", self.sql)
            self.assertIn(f"alter table coden_factory.{name} force row level security", self.sql)
            self.assertRegex(self.sql, rf"revoke all on coden_factory\.{name} from public, anon, authenticated")
        self.assertIn("revoke all on schema coden_factory from public, anon, authenticated", self.sql)
        self.assertNotRegex(self.sql, r"grant\s+(?:all|select|insert|update|delete).*\bto\s+(?:anon|authenticated|public)\b")

    def test_no_automatic_provider_execution_or_paid_calls(self):
        forbidden = ("http_post", "net.http", "cron.schedule", "pgmq.create", "webhook",
                     "security definer", "execute program", "create policy")
        for item in forbidden:
            with self.subTest(item=item):
                self.assertNotIn(item, self.sql)
        self.assertIn("execution_authorized boolean not null default false", self.sql)
        self.assertIn("provider_approved boolean not null default false", self.sql)
        self.assertIn("check (execution_authorized = false)", self.sql)
        self.assertIn("check (provider_approved = false)", self.sql)


if __name__ == "__main__":
    unittest.main()
