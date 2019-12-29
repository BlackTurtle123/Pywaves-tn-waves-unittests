import random
import string
import time

import pywaves as py
import unittest


py.setNode('https://apitnetworktest.blackturtle.eu', 'testnetTN', 'l')
py.setMatcher('https://tntestnetmatcher.blackturtle.eu')
py.DEFAULT_CURRENCY='TN'

address = py.Address(seed='input a seed here')
address2 = py.Address(
    seed="seed seed seed seed seed seed seed seed seed seed seed seed seed seed seed seed seed seed seed seed seed seed")

ASSET = "2GRJaVYhhQPKVoWQFyJfTfx3eB5DD7CPdG7ZYx3Cs6Mk"
PAIR = py.AssetPair(py.Asset(ASSET), py.Asset("TN"))
py.THROW_EXCEPTION_ON_ERROR = True


class TNTest(unittest.TestCase):
    currentResult = None  # holds last result object passed to run method

    @classmethod
    def setResult(cls, amount, errors, failures, skipped):
        cls.amount, cls.errors, cls.failures, cls.skipped = \
            amount, errors, failures, skipped

    def tearDown(self):
        amount = self.currentResult.testsRun
        errors = self.currentResult.errors
        failures = self.currentResult.failures
        skipped = self.currentResult.skipped
        self.setResult(amount, errors, failures, skipped)

    @classmethod
    def tearDownClass(cls):
        print("\ntests run: " + str(cls.amount))
        print("errors: " + str(len(cls.errors)))
        print("failures: " + str(len(cls.failures)))
        print("success: " + str(cls.amount - len(cls.errors) - len(cls.failures)))
        print("skipped: " + str(len(cls.skipped)))

    def run(self, result=None):
        self.currentResult = result  # remember result for use in tearDown
        unittest.TestCase.run(self, result)  # call superclass run method

    def gen_random_str(self, stringLength=30):
        """Generate a random string of fixed length """
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))

    # Transfer tests
    def test_tx_fail(self):
        output = address.sendWaves(address, 1)
        self.assertIn("error", str(output))

    def test_tx_just_not_enough(self):
        output = address.sendWaves(address, 1, txFee=1999999)
        self.assertIn("error", str(output))

    def test_tx_right(self):
        output = address.sendWaves(address, 1, txFee=2000000)
        self.assertNotIn("error", str(output))

    def test_tx_spam(self):
        for i in range(1000):
            output = address.sendWaves(address, 1, txFee=2000000)
            self.assertNotIn("error", str(output))

    def test_create_alias_error_not_enough_fee(self):
        output = address.createAlias("not_enough_fee" + self.gen_random_str(10))
        self.assertIn("does not exceed minimal value of ", str(output))

    def test_create_alias_to_long(self):
        output = address.createAlias(self.gen_random_str(40), txFee=1000000000)
        self.assertIn("length should be between 4 and 30", str(output))

    def test_alias(self):
        output = address.createAlias(self.gen_random_str(29), txFee=1000000000)
        self.assertNotIn("error", str(output))

    def test_create_order_not_enough_fee(self):
        with self.assertRaises(Exception):
            address.buy(PAIR, 100000, 1000000, matcherFee=3999999)
        address.cancelOpenOrders(PAIR)

    def test_create_order_enough_fee(self):
        address.cancelOpenOrders(PAIR)
        output = address.buy(PAIR, 100000, 1000000, matcherFee=4000000)
        address.cancelOpenOrders(PAIR)
        self.assertNotIn("error", str(output))

    def test_lease_not_enough_fee(self):
        output = address.lease(address2, 1)
        self.assertIn("does not exceed minimal value of ", str(output))

    def test_lease_enough_fee_and_cancel(self):
        lease_output = address.lease(address2, 1, txFee=2000000)
        self.assertNotIn("error", str(lease_output))
        time.sleep(60)
        output = address.leaseCancel(str(lease_output['id']))
        self.assertEqual(None, output)
        output = address.leaseCancel(str(lease_output['id']), txFee=20000000)
        self.assertNotIn("error", str(output))

    def test_create_reissue_burn_asset(self):
        random_amount = random.randint(1, 10000000000000000)
        random_fee = random.randint(1, random_amount)
        with self.assertRaises(Exception):
            asset_create = address.issueAsset(self.gen_random_str(16), self.gen_random_str(16), random_amount, 8,
                                              reissuable=True)

        asset_create = address.issueAsset(self.gen_random_str(16), self.gen_random_str(16), random_amount, 8,
                                          reissuable=True,
                                          txFee=100000000000)

        self.assertNotIn("error", str(asset_create))
        asset_id = asset_create.assetId
        time.sleep(60)
        asset_reissue = address.reissueAsset(py.Asset(asset_id), 10000, reissuable=True, txFee=99900000000)
        self.assertIn("ERROR", str(asset_reissue))
        asset_reissue = address.reissueAsset(py.Asset(asset_id), 10000, reissuable=True, txFee=100000000000)
        self.assertNotIn("ERROR", str(asset_reissue))

        asset_burn = address.burnAsset(py.Asset(asset_id), 10, txFee=1999999)
        self.assertIn("ERROR", str(asset_burn))
        asset_burn = address.burnAsset(py.Asset(asset_id), 10, txFee=2000000)
        self.assertNotIn("ERROR", str(asset_burn))

        sponsor = address.sponsorAsset(asset_id, random_fee, 1000000000 - 1)
        self.assertIn("error", str(sponsor))
        sponsor = address.sponsorAsset(asset_id, random_fee, 1000000000)
        self.assertNotIn("error", str(sponsor))
        time.sleep(60)
        transfer_sponsor = address.sendAsset(address2, py.Asset(asset_id), 100, attachment='testing sponsorhsip',
                                             feeAsset=py.Asset(asset_id), txFee=random_fee, timestamp=0)
        self.assertNotIn("error", str(transfer_sponsor))
        self.assertIn("'fee': " + str(random_fee), str(transfer_sponsor))

    def test_create_reissue_burn_smart_asset(self):
        script = 'match tx { \n' + \
                 '  case _ => true\n' + \
                 '}'

        asset_create = address.issueSmartAsset(self.gen_random_str(16), self.gen_random_str(16), 10000000000,
                                               script, 8,
                                               reissuable=True)
        self.assertIn("does not exceed minimal value of", str(asset_create))

        asset_create = address.issueSmartAsset(self.gen_random_str(16), self.gen_random_str(16), 10000000000, script, 8,
                                               reissuable=True,
                                               txFee=100000000000)

        self.assertNotIn("error", str(asset_create))
        asset_id = asset_create['id']
        time.sleep(60)
        asset_reissue = address.reissueAsset(py.Asset(asset_id), 10000, reissuable=True, txFee=99900000000 + 4000000)
        self.assertIn("ERROR", str(asset_reissue))
        asset_reissue = address.reissueAsset(py.Asset(asset_id), 10000, reissuable=True, txFee=100000000000 + 4000000)
        self.assertNotIn("ERROR", str(asset_reissue))

        asset_burn = address.burnAsset(py.Asset(asset_id), 10, txFee=1999999 + 4000000)
        self.assertIn("ERROR", str(asset_burn))
        asset_burn = address.burnAsset(py.Asset(asset_id), 10, txFee=2000000 + 4000000)
        self.assertNotIn("ERROR", str(asset_burn))

        set_script = address.setAssetScript(py.Asset(asset_id), script)
        self.assertIn("does not exceed minimal value of", str(set_script))
        set_script = address.setAssetScript(py.Asset(asset_id), script, txFee=104000000)
        self.assertNotIn("ERROR", str(set_script))

    def test_create_data_transaction_error(self):
        data = [{
            'type': 'string',
            'key': 'test',
            'value': 'testval'
        }]
        data_tx = address.dataTransaction(data)
        self.assertIn("does not exceed minimal value of ", str(data_tx))

    def test_create_data_transaction_(self):
        data = [{
            'type': 'string',
            'key': 'test',
            'value': 'testval' + str(datetime.datetime.now())
        }]
        data_tx = address.dataTransaction(data, baseFee=2000000, minimalFee=2100000)
        self.assertNotIn("does not exceed minimal value of ", str(data_tx))

    def test_create_mass_transfer_error(self):
        transfers = [
            # {'recipient': '3JcB4Ux7akWqVHeSjvdqrB151LG812qk4qX', 'amount': 1},
            # {'recipient': '3JcB4Ux7akWqVHeSjvdqrB151LG812qk4qX', 'amount': 2},
            # {'recipient': '3JcB4Ux7akWqVHeSjvdqrB151LG812qk4qX', 'amount': 3}
            {'recipient': '3XcE4knb13yyXKpdNvWhwvjrYsgMXsoicQM', 'amount': 1},
            {'recipient': '3XcE4knb13yyXKpdNvWhwvjrYsgMXsoicQM', 'amount': 2},
            {'recipient': '3XcE4knb13yyXKpdNvWhwvjrYsgMXsoicQM', 'amount': 3}
        ]
        mass_tx = address.massTransferWaves(transfers, baseFee=1999999)

        self.assertIn("does not exceed minimal value of ", str(mass_tx))

    def test_create_mass_transfer(self):
        transfers = [
            # {'recipient': '3JcB4Ux7akWqVHeSjvdqrB151LG812qk4qX', 'amount': 1},
            # {'recipient': '3JcB4Ux7akWqVHeSjvdqrB151LG812qk4qX', 'amount': 2},
            # {'recipient': '3JcB4Ux7akWqVHeSjvdqrB151LG812qk4qX', 'amount': 3}
            {'recipient': '3XcE4knb13yyXKpdNvWhwvjrYsgMXsoicQM', 'amount': 1},
            {'recipient': '3XcE4knb13yyXKpdNvWhwvjrYsgMXsoicQM', 'amount': 2},
            {'recipient': '3XcE4knb13yyXKpdNvWhwvjrYsgMXsoicQM', 'amount': 3}
        ]
        mass_tx = address.massTransferWaves(transfers, baseFee=2000000)
        self.assertNotIn("does not exceed minimal value of", str(mass_tx))
        self.assertNotIn("error", str(mass_tx))
        self.assertIn("id", str(mass_tx))

    def test_create_nft_buy_sell_and_burn(self):
        with self.assertRaises(Exception):
            nft_create = address.issueAsset("nft " + self.gen_random_str(12), "nft " + self.gen_random_str(12), 1, 0,
                                            reissuable=False, txFee=9999999)

        nft_create = address.issueAsset("nft " + self.gen_random_str(12), "nft " + self.gen_random_str(12), 1, 0,
                                        reissuable=False, txFee=10000000)

        self.assertNotIn("error", str(nft_create))

        asset_id = nft_create.assetId
        time.sleep(60)

        PAIR = py.AssetPair(py.Asset(asset_id), py.Asset("TN"))
        address.cancelOpenOrders(PAIR)

        output = address.sell(PAIR, 1, 100,maxLifetime=60000, matcherFee=4000000)
        address.cancelOpenOrders(PAIR)
        self.assertNotIn("error", str(output))

        output = address.buy(PAIR, 1, 100,maxLifetime=60000, matcherFee=4000000)
        address.cancelOpenOrders(PAIR)
        self.assertNotIn("error", str(output))

        nft_burn = address.burnAsset(py.Asset(asset_id), 1, txFee=1999999)
        self.assertIn("ERROR", str(nft_burn))

        nft_burn = address.burnAsset(py.Asset(asset_id), 1, txFee=2000000)
        self.assertNotIn("ERROR", str(nft_burn))

if __name__ == '__main__':
    unittest.main()

