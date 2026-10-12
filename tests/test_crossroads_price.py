import ast
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


# Load only the scraper functions so tests do not install browser dependencies.
source = Path(__file__).resolve().parents[1] / 'main.py'
names = {
    'crossroads_price_after_sku',
    'crossroads_price_hidden_by_login',
    'crossroads_scrape_product_page',
    'crossroads_extract_price',
}
tree = ast.parse(source.read_text())
functions = ast.Module(
    body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names],
    type_ignores=[],
)
namespace = {
    're': re,
    'By': SimpleNamespace(CSS_SELECTOR='css selector'),
    'sleep': Mock(),
    'CROSSROADS_PRICE_SWEEP_JS': 'return []',
}
exec(compile(functions, str(source), 'exec'), namespace)
price_after_sku = namespace['crossroads_price_after_sku']


class CrossroadsPriceTests(unittest.TestCase):
    def test_uses_first_dollar_amount_after_sku(self):
        text = '$5.20\nCandle\nSKU: CANDLE-12\n$6.25\nCase price $5.20'
        self.assertEqual(price_after_sku(text, 'CANDLE-12'), '$6.25')

    def test_accepts_labeled_sku_and_inline_price(self):
        self.assertEqual(price_after_sku('SKU: ABC-12 $6.25', 'SKU: ABC-12'), '$6.25')

    def test_prefers_sku_label_over_sku_mentioned_earlier(self):
        self.assertEqual(price_after_sku('ABC-12 candle $5.20\nSKU: ABC-12\n$6.25', 'ABC-12'), '$6.25')

    def test_accepts_unlabeled_sku_on_its_own_line(self):
        self.assertEqual(price_after_sku('$5.20\nABC-12\n$6.25', 'ABC-12'), '$6.25')

    def test_preserves_currency_format(self):
        self.assertEqual(price_after_sku('SKU: ABC\n$ 1,250.00', 'ABC'), '$ 1,250.00')

    def test_does_not_match_sku_prefix(self):
        self.assertEqual(price_after_sku('SKU: ABC-123\n$5.20\nSKU: ABC-12\n$6.25', 'ABC-12'), '$6.25')

    def test_missing_sku_or_price_stays_empty(self):
        for text, sku in [('$5.20', ''), ('$5.20', 'ABC')]:
            with self.subTest(text=text, sku=sku):
                self.assertEqual(price_after_sku(text, sku), '')

    def test_uses_price_above_sku_in_same_block(self):
        # Emun pages often render the displayed price above the SKU line.
        self.assertEqual(price_after_sku('$5.20\nSKU: ABC', 'ABC'), '$5.20')
        self.assertEqual(price_after_sku('SKU: OTHER\n$5.20\n$6.25\nSKU: ABC', 'ABC'), '$6.25')

    def test_does_not_borrow_related_product_price(self):
        for heading in ['Related Products', 'Recommended Products', 'Similar Products', 'You May Also Like', 'SKU: OTHER', 'Item # OTHER']:
            with self.subTest(heading=heading):
                self.assertEqual(price_after_sku(f'SKU: ABC\n{heading}\n$5.20', 'ABC'), '')

    def test_listing_price_overrides_page_heuristics(self):
        driver = Mock()
        driver.find_element.side_effect = LookupError
        driver.execute_script.side_effect = [
            '$5.20\nSKU: ABC\n$5.20',
            [],
        ]
        row = namespace['crossroads_scrape_product_page'](
            driver, 'https://example.com/product', listing_price='$6.25')
        self.assertEqual(row[2], '$6.25')

    def test_prefers_visible_product_price_over_sku_text(self):
        driver = Mock()
        driver.find_element.side_effect = LookupError
        driver.execute_script.side_effect = [
            'Loading\nSKU: ABC',
            '$6.25',
        ]
        row = namespace['crossroads_scrape_product_page'](driver, 'https://example.com/product')
        self.assertEqual(row[1:3], ['ABC', '$6.25'])
        self.assertGreaterEqual(driver.execute_script.call_count, 2)

    def test_ignores_stale_case_price_tier_value(self):
        driver = Mock()
        driver.execute_script.side_effect = [
            ['Case price $5.20', 'Product $6.25'],
            '<html><body>product</body></html>',
        ]
        self.assertEqual(namespace['crossroads_extract_price'](driver), '$6.25')

    def test_missing_price_does_not_use_earlier_price(self):
        driver = Mock()
        driver.find_element.side_effect = LookupError
        body = 'SKU: ABC\nRelated Products\n$5.20'
        driver.execute_script.side_effect = [body, '', [], '<html></html>', []]
        row = namespace['crossroads_scrape_product_page'](driver, 'https://example.com/product')
        self.assertEqual(row[2], '')

    def test_extracts_price_from_data_title_attribute(self):
        driver = Mock()
        driver.execute_script.side_effect = [
            [
                'Snowed In - 12 oz. Pint Candle (SIP) $6.25',
                'Related Products $5.20',
            ],
            '<html><body>product</body></html>',
        ]
        self.assertEqual(namespace['crossroads_extract_price'](driver), '$6.25')


if __name__ == '__main__':
    unittest.main()
