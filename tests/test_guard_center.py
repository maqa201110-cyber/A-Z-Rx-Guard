import unittest

import guard_center


class GuardCenterContentTests(unittest.TestCase):
    def test_account_checklists_are_available_for_all_three_platforms(self):
        self.assertEqual(set(guard_center.ACCOUNT_CHECKLISTS), {"tg", "instagram", "gmail"})
        for platform, checklist in guard_center.ACCOUNT_CHECKLISTS.items():
            with self.subTest(platform=platform):
                self.assertGreaterEqual(len(checklist["items"]), 4)
                self.assertTrue(all(title and detail for title, detail in checklist["items"]))

    def test_checklist_report_counts_only_valid_marked_items_and_is_honest(self):
        report = guard_center.checklist_report("tg", [0, 2, -1, 99, "1"])
        self.assertIn("2/4 madde işaretlendi", report)
        self.assertIn("Bot hesap ayarlarını otomatik göremez", report)
        self.assertIn("Şifreni veya doğrulama kodunu buraya yazma", report)

    def test_emergency_guides_have_actionable_steps(self):
        self.assertEqual(
            set(guard_center.EMERGENCY_GUIDES),
            {"account_hacked", "suspicious_login", "shared_secret", "lost_device"},
        )
        for guide_id, guide in guard_center.EMERGENCY_GUIDES.items():
            with self.subTest(guide=guide_id):
                report = guard_center.emergency_report(guide_id)
                self.assertGreaterEqual(len(guide["steps"]), 4)
                self.assertIn("resmî", report.casefold())
                self.assertIn("doğrulama kodunu kimseye verme", report.casefold())

    def test_quiz_has_five_answerable_questions_and_button_labels_fit(self):
        self.assertEqual(len(guard_center.SCAM_QUIZ), 5)
        for question in guard_center.SCAM_QUIZ:
            self.assertEqual(len(question["options"]), 3)
            self.assertIn(question["answer"], range(len(question["options"])))
            self.assertTrue(question["explanation"])
            for index, option in enumerate(question["options"]):
                self.assertLessEqual(len(f"{chr(65 + index)}. {option}"), 64)


if __name__ == "__main__":
    unittest.main()
