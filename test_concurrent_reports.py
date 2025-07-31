#!/usr/bin/env python3
"""
동시 리포트 생성 테스트 스크립트
여러 사용자가 동시에 리포트를 요청했을 때 충돌이 발생하지 않는지 테스트합니다.
"""

import asyncio
import aiohttp
import time
import logging
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def generate_report(session: aiohttp.ClientSession, ticker: str, user_id: int) -> dict:
    """단일 리포트 생성 요청"""
    url = "http://localhost:8000/generate_report"
    payload = {"ticker": ticker, "report_type": "summary"}
    
    start_time = time.time()
    try:
        async with session.post(url, json=payload) as response:
            duration = time.time() - start_time
            if response.status == 200:
                data = await response.json()
                logging.info(f"사용자 {user_id}: {ticker} 리포트 생성 성공 ({duration:.2f}초)")
                return {"user_id": user_id, "ticker": ticker, "success": True, "duration": duration}
            else:
                error_text = await response.text()
                logging.error(f"사용자 {user_id}: {ticker} 리포트 생성 실패 ({response.status}) - {error_text}")
                return {"user_id": user_id, "ticker": ticker, "success": False, "duration": duration, "error": error_text}
    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"사용자 {user_id}: {ticker} 요청 중 예외 발생 - {e}")
        return {"user_id": user_id, "ticker": ticker, "success": False, "duration": duration, "error": str(e)}

async def test_concurrent_reports():
    """동시 리포트 생성 테스트"""
    # 테스트 시나리오: 5명의 사용자가 동시에 AAPL 리포트 요청
    tasks = []
    
    async with aiohttp.ClientSession() as session:
        logging.info("=== 동시성 테스트 시작 ===")
        logging.info("시나리오: 5명의 사용자가 동시에 AAPL 리포트 요청")
        
        start_time = time.time()
        
        # 5개의 동시 요청 생성
        for i in range(1, 6):
            task = generate_report(session, "AAPL", i)
            tasks.append(task)
        
        # 모든 요청을 동시에 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        
        # 결과 분석
        successes = [r for r in results if isinstance(r, dict) and r.get("success")]
        failures = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if not isinstance(r, dict)]
        
        logging.info("=== 테스트 결과 ===")
        logging.info(f"전체 소요 시간: {total_duration:.2f}초")
        logging.info(f"성공: {len(successes)}개")
        logging.info(f"실패: {len(failures)}개")
        logging.info(f"예외: {len(exceptions)}개")
        
        if successes:
            avg_duration = sum(r["duration"] for r in successes) / len(successes)
            logging.info(f"평균 응답 시간: {avg_duration:.2f}초")
        
        if failures:
            logging.warning("실패한 요청들:")
            for failure in failures:
                logging.warning(f"  사용자 {failure['user_id']}: {failure.get('error', '알 수 없는 오류')}")
        
        if exceptions:
            logging.error("예외가 발생한 요청들:")
            for exc in exceptions:
                logging.error(f"  {exc}")
        
        return len(successes) == 5  # 모든 요청이 성공했는지 반환

async def test_different_tickers():
    """서로 다른 종목으로 동시 요청 테스트"""
    tickers = ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL"]
    tasks = []
    
    async with aiohttp.ClientSession() as session:
        logging.info("=== 다른 종목 동시 요청 테스트 시작 ===")
        
        start_time = time.time()
        
        # 각각 다른 종목으로 요청
        for i, ticker in enumerate(tickers, 1):
            task = generate_report(session, ticker, i)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time
        
        successes = [r for r in results if isinstance(r, dict) and r.get("success")]
        logging.info(f"다른 종목 테스트 - 성공: {len(successes)}/{len(tickers)}, 소요시간: {total_duration:.2f}초")
        
        return len(successes) == len(tickers)

async def main():
    """메인 테스트 실행"""
    logging.info("리포트 동시성 테스트를 시작합니다...")
    
    try:
        # 1. 같은 종목 동시 요청 테스트
        test1_success = await test_concurrent_reports()
        
        # 잠시 대기
        await asyncio.sleep(2)
        
        # 2. 다른 종목 동시 요청 테스트
        test2_success = await test_different_tickers()
        
        # 최종 결과
        logging.info("=== 전체 테스트 결과 ===")
        logging.info(f"동일 종목 동시 요청: {'통과' if test1_success else '실패'}")
        logging.info(f"다른 종목 동시 요청: {'통과' if test2_success else '실패'}")
        
        if test1_success and test2_success:
            logging.info("✅ 모든 동시성 테스트가 성공했습니다!")
        else:
            logging.warning("❌ 일부 테스트가 실패했습니다.")
            
    except Exception as e:
        logging.error(f"테스트 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())