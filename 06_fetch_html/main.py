import asyncio
import logging
import os
from datetime import datetime
import hashlib
from config import USER_AGENTS, BASEFOLDER, BASEFOLDER_MHTML
from database import execute_sql, get_websites_to_process
from screenshot import capture_screenshot
from mhtml import fetch_website_as_mhtml
from urllib.parse import urlparse
from check_write_status import check_write_status  # インポート


# 07_certificateの関数をインポート
from ssl_certificate import get_ssl_certificate_info, save_ssl_certificate_info, update_status_to_97

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def process_website(destination, semaphore, progress_tracker):
    """
    1つのウェブサイトを処理する非同期関数
    
    :param destination: 処理対象のウェブサイト情報（タプル）
    :param semaphore: 同時実行数を制限するためのセマフォ
    :param progress_tracker: 進捗状況を追跡するための辞書
    """
    website_id, domain, url, url_pc_site, url_mobile_site = destination
    logging.info(f"Processing website: {domain}")

    target_url = url or url_pc_site or f"https://{domain}"
    mobile_target_url = url_mobile_site or url or f"http://{domain}"

    async with semaphore:
        # MHTMLコンテンツの取得
        await fetch_website_as_mhtml(target_url, USER_AGENTS['Chrome'], website_id)
        await fetch_website_as_mhtml(target_url, USER_AGENTS['iPhone'], website_id)
        await fetch_website_as_mhtml(target_url, USER_AGENTS['Android'], website_id)

        # スクリーンショットの取得
        now = datetime.now()
        filename_prefix = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}_{domain}_{website_id}_{hashlib.md5(url.encode()).hexdigest()}"
        
        screenshot_results = await asyncio.gather(
            capture_screenshot(target_url, USER_AGENTS['iPhone'], os.path.join(BASEFOLDER, f"{filename_prefix}_iphone.png")),
            capture_screenshot(target_url, USER_AGENTS['Android'], os.path.join(BASEFOLDER, f"{filename_prefix}_android.png")),
            capture_screenshot(target_url, USER_AGENTS['Chrome'], os.path.join(BASEFOLDER, f"{filename_prefix}_chrome.png"))
        )

        screenshot_availability = any(screenshot_results)
        
        # スクリーンショット情報の更新
        await update_screenshot_info(website_id, screenshot_availability, *screenshot_results, filename_prefix)

        # ドメイン名抽出
        def extract_domain(url):
            parsed_url = urlparse(url)
            domain_for_ssl = parsed_url.netloc
            return domain_for_ssl
        
        # SSL証明書情報の取得と保存
        resolved_domain = extract_domain(url)
        ssl_certificate_info = await get_ssl_certificate_info(resolved_domain)
        if ssl_certificate_info:
            await save_ssl_certificate_info(website_id, resolved_domain, ssl_certificate_info)
            print(website_id)
        else:
            await update_status_to_97(website_id)

        # 書き込み確認
        is_successful = check_write_status(website_id)
        if is_successful:
            logging.info(f"ID {website_id} のデータベース書き込みが成功しました。")
        else:
            logging.warning(f"ID {website_id} のデータベース書き込みに問題があります。")
            
        # 進捗状況の更新
        progress_tracker['completed'] += 1
        logging.info(f"Progress: {progress_tracker['completed']}/{progress_tracker['total']} websites processed.")

async def update_screenshot_info(website_id, screenshot_availability, iphone_success, android_success, chrome_success, filename_prefix):
    """
    スクリーンショット情報をデータベースに更新する
    
    :param website_id: ウェブサイトのID
    :param screenshot_availability: スクリーンショットが利用可能かどうか
    :param iphone_success: iPhoneでのスクリーンショット取得成功フラグ
    :param android_success: Androidでのスクリーンショット取得成功フラグ
    :param chrome_success: Chromeでのスクリーンショット取得成功フラグ
    :param filename_prefix: ファイル名のプレフィックス
    """
    sql = """
    UPDATE website_data SET 
        screenshot_availability = %s, 
        screenshot_iphone = %s, 
        screenshot_android = %s, 
        screenshot_chrome = %s 
    WHERE id = %s
    """
    try:
        await execute_sql(sql, screenshot_availability, 
                          f"{filename_prefix}_iphone.png" if iphone_success else None, 
                          f"{filename_prefix}_android.png" if android_success else None, 
                          f"{filename_prefix}_chrome.png" if chrome_success else None, 
                          website_id)
        logging.info(f"Updated website_data for {website_id} with screenshots")
        await execute_sql("UPDATE website_data SET status = 98 WHERE id = %s", website_id)
        logging.info(f"Updated website_data for {website_id} with status 98")
    except Exception as e:
        logging.error(f"Failed to update website_data for {website_id}: {e}")

async def main():
    """
    メイン実行関数
    """
    semaphore = asyncio.Semaphore(6)  # 同時実行数を6に制限
    destinations = get_websites_to_process()
    progress_tracker = {'total': len(destinations), 'completed': 0}
    tasks = [process_website(destination, semaphore, progress_tracker) for destination in destinations]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

