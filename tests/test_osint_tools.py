import unittest
from unittest.mock import patch

import osint_tools


class OsintInputTests(unittest.TestCase):
    def test_domain_normalizes_case_and_url_path(self):
        self.assertEqual(
            osint_tools.normalize_domain("HTTPS://ExAmPle.com/profile?id=7"),
            "example.com",
        )

    def test_local_hosts_and_ip_literals_are_rejected_as_domains(self):
        for value in ("localhost", "printer.local", "127.0.0.1", "192.168.1.5"):
            with self.subTest(value=value), self.assertRaises(osint_tools.OsintInputError):
                osint_tools.normalize_domain(value)

    def test_only_public_ip_addresses_are_accepted(self):
        self.assertEqual(osint_tools.normalize_public_ip("8.8.8.8"), "8.8.8.8")
        for value in ("127.0.0.1", "10.0.0.1", "169.254.1.1", "not-an-ip"):
            with self.subTest(value=value), self.assertRaises(osint_tools.OsintInputError):
                osint_tools.normalize_public_ip(value)

    def test_link_path_and_query_are_not_in_report_or_sent_to_domain_lookup(self):
        with patch("osint_tools.inspect_domain", return_value="sample report") as lookup:
            report = osint_tools.inspect_url(
                "https://example.com/reset?token=private-value"
            )
        lookup.assert_called_once_with("example.com")
        self.assertNotIn("/reset", report)
        self.assertNotIn("private-value", report)
        self.assertIn("example.com", report)

    def test_certificate_names_are_limited_to_requested_domain(self):
        payload = [
            {"dns_names": ["example.com", "shop.example.com", "example.net"]},
        ]
        count, names = osint_tools._cert_domains(payload, "example.com")
        self.assertEqual(count, 1)
        self.assertEqual(names, ["example.com", "shop.example.com"])

    def test_domain_report_passes_each_source_its_expected_arguments(self):
        def dns_response(domain, record_type):
            return {"Status": 0, "Answer": [{"data": f"record-{record_type}"}]}

        with (
            patch("osint_tools._rdap_domain", return_value={"events": []}) as rdap,
            patch("osint_tools._dns_lookup", side_effect=dns_response) as dns,
            patch("osint_tools._certificates", return_value=[]) as certificates,
            patch("osint_tools._urlscan_search", return_value={"results": []}) as urlscan,
        ):
            report = osint_tools._domain_report_uncached("example.com")

        rdap.assert_called_once_with("example.com")
        dns.assert_any_call("example.com", "A")
        dns.assert_any_call("example.com", "AAAA")
        dns.assert_any_call("example.com", "MX")
        dns.assert_any_call("example.com", "NS")
        certificates.assert_called_once_with("example.com")
        urlscan.assert_called_once_with("example.com")
        self.assertIn("• A: record-A", report)
        self.assertIn("• NS: record-NS", report)

    def test_empty_public_archive_does_not_claim_domain_is_safe(self):
        summary = osint_tools._urlscan_summary({"results": []}, "example.com")
        self.assertIn("güvenli olduğunu kanıtlamaz", summary[0])

    def test_ip_archive_shows_malicious_labels_as_historical_signals(self):
        payload = {
            "results": [{
                "page": {"ip": "8.8.8.8"},
                "labels": [{"label": "phishing"}],
                "task": {
                    "uuid": "01a12f35-5400-747a-bebe-70c9379a4124",
                    "time": "2026-10-12T08:12:19Z",
                },
            }]
        }
        summary = osint_tools._urlscan_ip_summary(payload, "8.8.8.8")
        self.assertTrue(any("eski olabilir" in line for line in summary))
        self.assertTrue(any("urlscan.io/result/" in line for line in summary))

    def test_ipv6_archive_queries_quote_the_address(self):
        with patch("osint_tools._urlscan_query", return_value={"results": []}) as query:
            osint_tools._urlscan_ip_search("2001:4860:4860::8888")
        query.assert_called_once_with('page.ip:"2001:4860:4860::8888"')


if __name__ == "__main__":
    unittest.main()
