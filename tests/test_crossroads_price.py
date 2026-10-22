import ast
from pathlib import Path
import re
import urllib.request
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


# Load only the scraper functions so tests do not install browser dependencies.
source = Path(__file__).resolve().parents[1] / 'main.py'
names = {
    'crossroads_is_logged_in',
    'fashiongo_is_logged_in',
    'crossroads_price_after_sku',
    'crossroads_scent_description',
    'crossroads_price_hidden_by_login',
    'crossroads_scrape_product_page',
    'crossroads_extract_price',
    'crossroads_extract_product_metadata',
    'crossroads_image_file_size',
    'crossroads_sort_images_by_file_size',
    'crossroads_scrape_quick_view',
    'crossroads_close_quick_view',
    'crossroads_quick_view_count',
    'crossroads_upgrade_image_url',
    'fivebelow_product_in_stock',
    'fivebelow_extract_price',
    'fivebelow_collect_variant_options',
}
tree = ast.parse(source.read_text())
functions = ast.Module(
    body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names],
    type_ignores=[],
)
namespace = {
    're': re,
    'urllib': urllib,
    'By': SimpleNamespace(CSS_SELECTOR='css selector'),
    'sleep': Mock(),
    'CROSSROADS_PRICE_SWEEP_JS': 'return []',
    'CROSSROADS_IMAGES_JS': 'return []',
    'CROSSROADS_QUICK_VIEW_COUNT_JS': 'QV_COUNT',
    'CROSSROADS_QUICK_VIEW_OPEN_JS': 'QV_OPEN',
    'CROSSROADS_QUICK_VIEW_DATA_JS': 'QV_DATA',
    'CROSSROADS_QUICK_VIEW_CLOSE_JS': 'QV_CLOSE',
    'CROSSROADS_QUICK_VIEW_VISIBLE_JS': 'QV_VISIBLE',
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
            False,
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
            False,
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

    def test_ignores_stale_case_price_before_product_price_in_same_text_block(self):
        driver = Mock()
        driver.execute_script.side_effect = [
            ['$5.20\nCase price $5.20\nProduct $6.25'],
            '<html><body>product</body></html>',
        ]
        self.assertEqual(namespace['crossroads_extract_price'](driver), '$6.25')

    def test_ignores_stale_case_price_after_product_price_in_same_text_block(self):
        driver = Mock()
        driver.execute_script.side_effect = [
            ['Product $6.25\nCase price $5.20'],
            '<html><body>product</body></html>',
        ]
        self.assertEqual(namespace['crossroads_extract_price'](driver), '$6.25')

    def test_ignores_related_product_price_when_real_product_price_is_present(self):
        driver = Mock()
        driver.execute_script.side_effect = [
            ['Product $6.25', 'Related Products $5.20'],
            '<html><body>product</body></html>',
        ]
        self.assertEqual(namespace['crossroads_extract_price'](driver), '$6.25')

    def test_prefers_highest_visible_price_when_multiple_prices_are_present(self):
        driver = Mock()
        driver.execute_script.side_effect = [
            ['Showcase $5.20', 'Product price $6.25', 'Case price $5.20'],
            '<html><body>product</body></html>',
        ]
        self.assertEqual(namespace['crossroads_extract_price'](driver), '$6.25')

    def test_ignores_retail_msrp_and_compare_prices(self):
        driver = Mock()
        driver.execute_script.side_effect = [
            ['MSRP $5.20', 'Was $5.50', 'Our Price $6.25'],
            '<html><body>product</body></html>',
        ]
        self.assertEqual(namespace['crossroads_extract_price'](driver), '$6.25')

    def test_missing_price_does_not_use_earlier_price(self):
        driver = Mock()
        driver.find_element.side_effect = LookupError
        body = 'SKU: ABC\nRelated Products\n$5.20'
        driver.execute_script.side_effect = [False, body, '', [], '<html></html>', []]
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

    def test_ignores_stale_tier_listing_price_when_real_price_is_visible(self):
        driver = Mock()
        driver.find_element.side_effect = LookupError
        driver.execute_script.side_effect = [
            False,
            'SKU: ABC\nCase price $5.20\n$40.00',
            '$40.00',
        ]
        row = namespace['crossroads_scrape_product_page'](driver, 'https://example.com/product', listing_price='$5.20')
        self.assertEqual(row[2], '$40.00')

    def test_detects_login_gated_price_text(self):
        for text in [
            'Please log in to view price',
            'Login to view pricing',
            'member pricing requires login',
            'Price hidden until sign in',
        ]:
            with self.subTest(text=text):
                self.assertTrue(namespace['crossroads_price_hidden_by_login'](text))

    def test_detects_logged_in_state_for_fashiongo_and_crossroads(self):
        fake = Mock()
        fake.execute_script.side_effect = [
            True,
            True,
            False,
        ]
        self.assertTrue(namespace['fashiongo_is_logged_in'](fake))
        self.assertTrue(namespace['crossroads_is_logged_in'](fake))

    def test_extracts_product_metadata_fields(self):
        metadata = namespace['crossroads_extract_product_metadata'](
            'ITEM #: 12345\nMINIMUM QTY: 12\nDIMENSIONS: 8 x 8\nDESIGNER: River\nDescription: Premium candle'
        )
        self.assertEqual(metadata['ITEM #'], '12345')
        self.assertEqual(metadata['MINIMUM QTY'], '12')
        self.assertEqual(metadata['DIMENSIONS'], '8 x 8')
        self.assertEqual(metadata['DESIGNER'], 'River')


class FiveBelowVariationTests(unittest.TestCase):
    def test_filters_out_of_stock_pages(self):
        self.assertFalse(namespace['fivebelow_product_in_stock']('Out of stock'))
        self.assertTrue(namespace['fivebelow_product_in_stock']('In stock'))

    def test_extracts_price_and_variant_meta(self):
        self.assertEqual(namespace['fivebelow_extract_price']('$6.25'), '$6.25')
        self.assertEqual(
            namespace['fivebelow_collect_variant_options']({
                'variants': [
                    {'size': 'S', 'color': 'Blue'},
                    {'size': 'M', 'color': 'Blue'},
                    {'style': 'Classic'}
                ]
            }),
            {'sizes': ['S', 'M'], 'colors': ['Blue'], 'styles': ['Classic']}
        )


class CrossroadsQuickViewTests(unittest.TestCase):
    def _driver(self, data, open_result=None):
        driver = Mock()
        def execute_script(script, *args):
            if script == 'QV_OPEN':
                return {'ok': True, 'productId': '101'} if open_result is None else open_result
            if script == 'QV_DATA':
                return data
            if script == 'QV_VISIBLE':
                return False
            if script == 'QV_CLOSE':
                return True
            return None
        driver.execute_script.side_effect = execute_script
        driver.get_cookies.return_value = []
        return driver

    def test_upgrade_image_url_swaps_stencil_size_for_original(self):
        self.assertEqual(
            namespace['crossroads_upgrade_image_url'](
                'https://cdn11.bigcommerce.com/s-abc/images/stencil/500x659/products/101/900/jar.jpg'),
            'https://cdn11.bigcommerce.com/s-abc/images/stencil/original/products/101/900/jar.jpg',
        )
        self.assertEqual(
            namespace['crossroads_upgrade_image_url']('https://example.com/img/jar.jpg'),
            'https://example.com/img/jar.jpg',
        )

    def test_scrapes_quick_view_modal_fields(self):
        driver = self._driver({
            'title': 'Buttered Maple Syrup 26 oz Jar',
            'sku': 'BMS-26',
            'price': '$12.50',
            'description': 'Our famous  buttered maple\nsyrup candle.',
            'url': 'https://crossroadscandles.com/buttered-maple-syrup-26-oz-jar/',
            'images': ['https://cdn11.bigcommerce.com/s-abc/images/stencil/500x659/products/101/900/jar.jpg'],
        })
        row, dedup_key = namespace['crossroads_scrape_quick_view'](driver, 0)
        self.assertEqual(dedup_key, '101')
        self.assertEqual(row[0], 'Buttered Maple Syrup 26 oz Jar')
        self.assertEqual(row[1], 'BMS-26')
        self.assertEqual(row[2], '$12.50')
        self.assertEqual(row[5], 'Our famous buttered maple syrup candle.')
        self.assertEqual(row[7], 'https://cdn11.bigcommerce.com/s-abc/images/stencil/original/products/101/900/jar.jpg')

    def test_quick_view_description_uses_scent_description_only(self):
        driver = self._driver({
            'title': 'Buttered Maple Syrup 26 oz Jar',
            'sku': 'BMS-26',
            'price': '$12.50',
            'description': 'Burn Time: 100 hours\nScent Description: Warm buttered maple\nsyrup over pancakes.\nWeight: 26 oz',
            'url': 'https://crossroadscandles.com/buttered-maple-syrup-26-oz-jar/',
            'images': [],
        })
        row, _ = namespace['crossroads_scrape_quick_view'](driver, 0)
        self.assertEqual(row[5], 'Warm buttered maple syrup over pancakes.')

    def test_scent_description_helper(self):
        helper = namespace['crossroads_scent_description']
        self.assertEqual(
            helper('Scent Description: Fresh linen breeze\n\nITEM #: 123'),
            'Fresh linen breeze',
        )
        self.assertEqual(helper('No label here'), '')

    def test_quick_view_without_data_returns_none(self):
        row, dedup_key = namespace['crossroads_scrape_quick_view'](self._driver(None), 0)
        self.assertIsNone(row)
        self.assertEqual(dedup_key, '')

    def test_quick_view_dedup_key_falls_back_to_url_then_title_sku(self):
        data = {'title': 'Jar', 'sku': 'BMS', 'price': '$5', 'description': '', 'url': 'https://x.com/p/', 'images': []}
        _, dedup_key = namespace['crossroads_scrape_quick_view'](self._driver(data, open_result={'ok': True, 'productId': ''}), 0)
        self.assertEqual(dedup_key, 'https://x.com/p/')
        data['url'] = ''
        _, dedup_key = namespace['crossroads_scrape_quick_view'](self._driver(data, open_result={'ok': True, 'productId': ''}), 0)
        self.assertEqual(dedup_key, 'Jar|BMS')


if __name__ == '__main__':
    unittest.main()
