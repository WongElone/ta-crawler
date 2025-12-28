from .run import start_wait_stop_runner, run
import logging
import json

log = logging.getLogger(__name__)


def test_main_module():
    """Test the main module functionality."""
    log.info("Testing main module...")
    try:
        from . import main
        # Test that main function exists and is callable
        if hasattr(main, 'main') and callable(main.main):
            log.info("main.main() function is available")
            return True
        else:
            log.error("main.main() function not found")
            return False
    except Exception as e:
        log.error(f"main module test failed: {e}")
        return False

async def test_openrouter_searcher():
    log.info("Testing openrouter searcher...")
    try:
        from .source.searcher import OpenrouterSearcher
        searcher = OpenrouterSearcher()
        # result_list = searcher.search("Enumerate earnings releases of US leading companies of each financial sector from 2025-11-17 to 2025-11-24", None, None)
        result_list = await searcher.search("太興集團主席陳永安何時死的？", None, None)
        for result in result_list:
            log.info(f"result: {json.dumps(result)}")
        log.info("openrouter searcher test passed")
    except Exception as e:
        log.error(f"openrouter searcher test failed: {e}")


def run_all_tests():
    """Run all crawler tests."""
    log.info("=== Starting crawler tests ===")
    
    tests = [
        ("main_module", test_main_module),
    ]
    
    results = {}
    for test_name, test_func in tests:
        log.info(f"Running {test_name} test...")
        results[test_name] = test_func()
        log.info(f"{test_name} test: {'PASSED' if results[test_name] else 'FAILED'}")
    
    # Summary
    passed = sum(results.values())
    total = len(results)
    log.info(f"=== Test Summary: {passed}/{total} tests passed ===")
    
    if passed == total:
        log.info("All tests passed!")
    else:
        log.warning(f"{total - passed} tests failed")

def test_async_tbdm():
    import asyncio
    from .const import FlashNewsSite
    from .dao import TradebotDatabaseManagerAsync
    tbdm = TradebotDatabaseManagerAsync()
    async def async_test():
        await tbdm.open()
        result = await tbdm.get_flash_news_last_publish_time(FlashNewsSite.CHAINCATCHER)
        log.info(f"result: {result}")
        await tbdm.close()
    asyncio.run(async_test())

def test_log():
    log.info("test log")

if __name__ == "__main__":
    run(test_async_tbdm)
