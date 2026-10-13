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

    def test_subdomain_report_lists_only_names_under_the_requested_domain(self):
        certificates = [
            {
                "dns_names": [
                    "example.com",
                    "api.example.com",
                    "*.example.com",
                    "www.example.com",
                    "example.net",
                ]
            }
        ]
        with patch("osint_tools._certificates", return_value=certificates) as lookup:
            report = osint_tools._subdomains_report_uncached("example.com")

        lookup.assert_called_once_with("example.com", limit=100)
        self.assertIn("api.example.com", report)
        self.assertIn("www.example.com", report)
        self.assertIn("*.example.com", report)
        self.assertNotIn("example.net", report)
        self.assertIn("şu an açık olduğunu göstermez", report)


class OsintGmailAndNameTests(unittest.TestCase):
    def test_gmail_accepts_gmail_domains_and_rejects_other_or_malformed_addresses(self):
        self.assertEqual(
            osint_tools.normalize_gmail("User.Name+tag@gmail.com"),
            "gmail.com",
        )
        self.assertEqual(
            osint_tools.normalize_gmail("user@googlemail.com"),
            "googlemail.com",
        )
        for value in (
            "person@yahoo.com",
            "person@gmail.com.",
            "person..name@gmail.com",
            "@gmail.com",
            "person@@gmail.com",
        ):
            with self.subTest(value=value), self.assertRaises(osint_tools.OsintInputError):
                osint_tools.normalize_gmail(value)

    def test_gmail_check_sends_only_domain_to_dns_and_does_not_echo_address(self):
        address = "sample.user+tag@gmail.com"
        dns_response = {"Status": 0, "Answer": [{"data": "10 gmail-smtp.example."}]}
        with (
            patch(
                "osint_tools._cache_get_or_create",
                side_effect=lambda _key, builder: builder(),
            ),
            patch("osint_tools._dns_lookup", return_value=dns_response) as dns_lookup,
        ):
            report = osint_tools.inspect_gmail(address)

        dns_lookup.assert_called_once_with("gmail.com", "MX")
        self.assertNotIn(address, report)
        self.assertIn("tam e-posta adresi dış kaynağa gönderilmez", report.casefold())
        self.assertIn("sızıntıda bulunup bulunmadığını göstermez", report.casefold())

    def test_name_search_shows_only_titles_containing_all_name_terms(self):
        payload = {
            "query": {
                "search": [
                    {"title": "Ada Lovelace"},
                    {"title": "Ada Lovelace Day"},
                    {"title": "Nvidia RTX"},
                ]
            }
        }
        with patch("osint_tools._wikipedia_search", return_value=payload) as search:
            report = osint_tools.inspect_name("Ada Lovelace")

        self.assertEqual(search.call_count, 2)
        search.assert_any_call("tr", "Ada Lovelace")
        search.assert_any_call("en", "Ada Lovelace")
        self.assertIn("Ada Lovelace: https://tr.wikipedia.org/wiki/Ada_Lovelace", report)
        self.assertIn("Ada Lovelace Day", report)
        self.assertNotIn("Nvidia RTX", report)
        self.assertIn("Aranan ifade Wikipedia'nın arama servisine gönderilir", report)
        self.assertIn("özel kişi bilgisi/iletişim bilgisi toplamaz", report)

    def test_wikipedia_search_uses_an_exact_phrase_query(self):
        with (
            patch("osint_tools._json_get", return_value={"query": {}}) as json_get,
            patch("osint_tools.time.monotonic", return_value=100.0),
        ):
            osint_tools._wikipedia_search("tr", "Ada Lovelace")

        json_get.assert_called_once()
        self.assertEqual(
            json_get.call_args.kwargs["params"]["srsearch"],
            '"Ada Lovelace"',
        )
        self.assertEqual(json_get.call_args.kwargs["params"]["srlimit"], 10)

    def test_name_queries_reject_urls_and_overlong_input(self):
        for value in ("https://example.com", "x" * 81):
            with self.subTest(value=value), self.assertRaises(osint_tools.OsintInputError):
                osint_tools.normalize_name_query(value)


if __name__ == "__main__":
    unittest.main()
