# ウェブサイトデータの取得関数
def get_website_data(user_agent):
    try:
        conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        cur = conn.cursor()
        # 処理対象のウェブサイト数をカウント
        cur.execute("SELECT COUNT(*) FROM website_data WHERE status = 5 AND (url IS NOT NULL OR url_pc_site IS NOT NULL OR (domain IS NOT NULL AND ip_address IS NOT NULL))")
        total_websites = cur.fetchone()[0]
        print(f"総ウェブサイト数: {total_websites}")
        
        
        cur.execute("SELECT id, domain, url, url_pc_site, url_mobile_site FROM website_data WHERE status = 5 AND (url IS NOT NULL OR url_pc_site IS NOT NULL OR (domain IS NOT NULL AND ip_address IS NOT NULL))")
        destinations = cur.fetchall()

        website_count = 1        
        for destination in destinations:
            website_id, domain, url, url_pc_site, url_mobile_site = destination
            print(f"処理中のウェブサイト: {website_count}/{total_websites} ({domain})")


            if url is not None:
                target_url = url
            elif url_pc_site is not None:
                target_url = url_pc_site
            else:
                target_url = f"https://{domain}"
                
            if url_mobile_site is not None:
                mobile_target_url = url_mobile_site
            elif url is not None:
                mobile_target_url = url
            else:
                mobile_target_url = f"http://{domain}"

            if url_mobile_site is None:
                html_content, redirect_url = fetch_website(target_url, user_agent)
                mobile_html_content = None
                mobile_redirect_url = None
            else:
                mobile_html_content, mobile_redirect_url = fetch_website(mobile_target_url, user_agent)

            print(html_content)
            print(url)
            if html_content is not None or redirect_url is not None or mobile_html_content is not None or mobile_redirect_url is not None:
                sql = "UPDATE website_data SET html_pc_site = %s, url_pc_redirect = %s, html_mobile_site_iphone = %s, url_mobile_redirect_iphone = %s, html_mobile_site_android = %s, url_mobile_redirect_android = %s, status = 6, last_update = NOW() WHERE id = %s"
                execute_sql(sql, html_content, redirect_url, mobile_html_content, mobile_redirect_url, mobile_html_content, mobile_redirect_url, website_id)

                # スクリーンショットの取得
                now = datetime.now()
                filename_prefix = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}_{domain}_{website_id}_{hashlib.md5(url.encode()).hexdigest()}"
                screenshot_iphone = f"{filename_prefix}_iphone.png"
                screenshot_android = f"{filename_prefix}_android.png"
                screenshot_chrome = f"{filename_prefix}_chrome.png"

                #url="https://www.yahoo.co.jp"

                screenshot_iphone_success = capture_screenshot(url, user_agents['iPhone'], os.path.join(basefolder, screenshot_iphone)
                screenshot_android_success = capture_screenshot(url, user_agents['Android'], os.path.join(basefolder, screenshot_android))
                screenshot_chrome_success = capture_screenshot(url, user_agents['Chrome'], os.path.join(basefolder, screenshot_chrome))

                # データベースの更新
                if screenshot_iphone_success and screenshot_android_success and screenshot_chrome_success:
                    screenshot_availability = True
                else:
                    screenshot_availability = False

                    sql = "UPDATE website_data SET html_pc_site = %s, url_pc_redirect = %s, html_mobile_site_iphone = %s, url_mobile_redirect_iphone = %s, html_mobile_site_android = %s, url_mobile_redirect_android = %s, status = 6, last_update = NOW(), screenshot_availability = %s, screenshot_iphone = %s, screenshot_android = %s, screenshot_chrome = %s WHERE id = %s"
                    execute_sql(sql, html_content, redirect_url, mobile_html_content, mobile_redirect_url, mobile_html_content, mobile_redirect_url, screenshot_availability, screenshot_iphone if screenshot_iphone_success else None, screenshot_android if screenshot_android_success else None, screenshot_chrome if screenshot_chrome_success else None, website_id)
                    website_count += 1                

            else:
                sql = "UPDATE website_data SET status = 98 WHERE id = %s"
                execute_sql(sql, website_id)
                website_count += 1
        cur.close()
        conn.close()

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"{datetime.now().isoformat()} - Error in get_website_data function: {str(error)}")
