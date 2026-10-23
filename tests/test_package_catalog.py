import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackageCatalogTest(unittest.TestCase):
    def test_portfolio_mapping_covers_the_physical_graph(self):
        graph = json.loads((ROOT / 'platform-packages.json').read_text())
        portfolio = json.loads((ROOT / 'packages/kit/contracts/portfolio-products.json').read_text())
        self.assertEqual(set(portfolio['platform_monorepo']['packages'].values()),
                         {spec['path'] for spec in graph['packages'].values()})


if __name__ == '__main__':
    unittest.main()
