from product_reco_bot.collectors.pdd_collector import PddCollector


class FakePddClient:
    def search_goods(self, keyword: str, page: int, page_size: int):
        assert page == 1
        assert page_size > 0
        return {
            "goods_search_response": {
                "goods_list": [
                    {
                        "goods_id": 123,
                        "goods_sign": "signed-goods",
                        "goods_name": f"{keyword}爆款",
                        "goods_desc": "测试商品",
                        "goods_thumbnail_url": "https://example.com/pdd.jpg",
                        "min_group_price": 1299,
                        "sales_tip": "1.2万+",
                        "mall_name": "测试店铺",
                    }
                ]
            }
        }

    def promotion_url(self, goods_sign: str):
        assert goods_sign == "signed-goods"
        return {
            "goods_promotion_url_generate_response": {
                "goods_promotion_url_list": [{"mobile_short_url": "https://p.pinduoduo.com/demo"}]
            }
        }


def test_pdd_collector_normalizes_goods() -> None:
    products = PddCollector(FakePddClient()).collect_keywords(["玩具"], limit=5)

    assert len(products) == 1
    assert products[0].product_id == "PDD-123"
    assert products[0].category == "玩具"
    assert products[0].price == 12.99
    assert products[0].sales_7d == 12_000
    assert products[0].supplier_name == "测试店铺"
    assert products[0].purchase_url == "https://p.pinduoduo.com/demo"
