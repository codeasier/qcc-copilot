import unittest

from qcc_copilot import contracts
from qcc_copilot.errors import ContractError, UnknownFormatVersion


class TestContracts(unittest.TestCase):
    def test_all_types_loadable(self):
        self.assertEqual(
            set(contracts.KNOWN_TYPES),
            {"topic", "sources_doc", "claim", "calculation", "delivery_snapshot",
             "summary", "feedback", "candidate"},
        )

    def test_valid_object(self):
        obj = contracts.blank("claim", claim_id="c1", text="x", origin="record", support="unverified")
        self.assertEqual(contracts.validate("claim", obj)["claim_id"], "c1")

    def test_unknown_format_version_is_distinct(self):
        with self.assertRaises(UnknownFormatVersion) as ctx:
            contracts.validate("claim", {"schema_version": "9.9", "claim_id": "c",
                                         "text": "x", "origin": "record", "support": "unverified"})
        self.assertEqual(ctx.exception.code, "unknown_format_version")

    def test_missing_identifier(self):
        with self.assertRaises(ContractError) as ctx:
            contracts.validate("claim", {"schema_version": "1.0", "text": "x",
                                         "origin": "record", "support": "unverified"})
        self.assertIn("identifier", ctx.exception.message)

    def test_wrong_type(self):
        with self.assertRaises(ContractError) as ctx:
            contracts.validate("topic", {"schema_version": "1.0", "topic_id": "t",
                                         "revision": "one", "rule_profile": {}, "claims": [],
                                         "tasks": [], "next": "n"})
        self.assertIn("wrong type", ctx.exception.message)

    def test_enum_constraint(self):
        with self.assertRaises(ContractError) as ctx:
            contracts.validate("claim", {"schema_version": "1.0", "claim_id": "c", "text": "x",
                                         "origin": "magic", "support": "unverified"})
        self.assertIn("origin", ctx.exception.message)

    def test_missing_schema_version(self):
        with self.assertRaises(ContractError):
            contracts.validate("claim", {"claim_id": "c", "text": "x",
                                         "origin": "record", "support": "unverified"})


if __name__ == "__main__":
    unittest.main()
