"""Lesson 32: offline readiness fixture and checks. Never calls an API or runs agent.py."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def create_fixture(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / 'pricing.py').write_text('''"""Pricing calculations."""\nfrom discounts import discount_amount\n\ndef final_price(subtotal, percent):\n    """Return the total after a percentage discount."""\n    return subtotal - discount_amount(subtotal, percent)\n''', encoding='utf-8')
    (root / 'discounts.py').write_text('''"""Discount calculations."""\n\ndef discount_amount(subtotal, percent):\n    """Compute a percentage discount (known bug: divides by 10)."""\n    return subtotal * percent / 10\n''', encoding='utf-8')
    (root / 'test_pricing.py').write_text('''import unittest\nfrom pricing import final_price\n\nclass PricingTests(unittest.TestCase):\n    def test_ten_percent(self):\n        self.assertEqual(final_price(100, 10), 90)\n    def test_zero_percent(self):\n        self.assertEqual(final_price(100, 0), 100)\n\nif __name__ == '__main__':\n    unittest.main()\n''', encoding='utf-8')
    return root


def run_fixture_tests(root):
    return subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(root), '-p', 'test_pricing.py', '-v'],
                          cwd=str(root), capture_output=True, text=True, timeout=15)


def evaluate(root, allowed):
    from agent_project_investigation import investigate_project
    r = investigate_project(root, 'discount_amount wrong percentage price', allowed)
    names = [c['file'] for c in r.get('candidates', [])]
    return {'status': r['status'], 'candidate_files': names,
            'discounts_discovered': 'discounts.py' in names,
            'pricing_discovered': 'pricing.py' in names,
            'read_only': True}


def allowed(root, filename):
    p = (Path(root) / filename).resolve()
    return p.is_relative_to(Path(root).resolve()) and p.suffix == '.py' and p.is_file()


def main():
    parser = argparse.ArgumentParser(description='Offline Agent 003 readiness preflight')
    parser.add_argument('--make-fixture', metavar='DIRECTORY', help='Create a disposable fixture in this directory; must not already exist')
    args = parser.parse_args()
    if args.make_fixture:
        dest = Path(args.make_fixture).resolve()
        if dest.exists():
            parser.error('Refusing to overwrite existing directory; choose a new disposable directory')
        create_fixture(dest)
        print('Fixture created:', dest)
        print('Expected failing test before an approved fix: python -m unittest discover -s . -p test_pricing.py -v')
        return
    with tempfile.TemporaryDirectory(prefix='agent003-lesson32-') as tmp:
        root = create_fixture(tmp)
        outcome = evaluate(root, allowed)
        tests = run_fixture_tests(root)
        outcome['fixture_bug_reproduced'] = tests.returncode != 0 and 'FAIL' in tests.stderr
        outcome['expected_root_cause'] = 'discounts.py: discount_amount divides by 10 instead of 100'
        outcome['pass'] = all([outcome['discounts_discovered'], outcome['pricing_discovered'], outcome['fixture_bug_reproduced']])
        print(json.dumps(outcome, indent=2))
        if not outcome['pass']:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
