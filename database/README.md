
```markdown
# Domain-based Data Retrieval from PostgreSQL

This Python script retrieves data from a PostgreSQL database based on a given `domain` value and outputs the results in the specified format. The script connects to the database, performs an SQL query on the `website_data` table, and formats the output as `"Column Name: Data"`.

## Prerequisites

Before running the script, ensure you have the following installed:

- Python 3.x
- psycopg2 (PostgreSQL adapter for Python)

### Installing psycopg2

To install `psycopg2`, run:

```bash
pip install psycopg2
```

## Database Setup

Ensure that your PostgreSQL database has the `website_data` table defined with the appropriate schema. The following columns are used in the script:

- `id`
- `status`
- `last_update`
- `phish_from`
- `url`
- `phish_id`
- `phish_detail_url`
- `phish_ip_address`
- `cidr_block`
- `verified`
- `online_status`
- `target`
- `domain_db_inserted_at`
- `domain_id`
- `domain`
- `domain_status`
- `domain_registrar`
- `whois_date`
- `whois_domain`
- `registrant_name`
- `admin_name`
- `tech_name`
- `dig_info_a`
- `dig_info_mx`
- `dig_info_ns`
- `dig_info_ttl_a`
- `dig_info_ttl_ns`
- `dig_info_ttl_mx`
- `ip_address`
- `ip_info`
- `ip_retrieval_date`
- `ip_organization`
- `ip_location`
- `hosting_provider`
- `whois_ip`
- `url_date`
- `url_pc_site`
- `url_pc_redirect`
- `url_mobile_site`
- `html_pc_site`
- `screenshot_iphone`
- `screenshot_android`
- `screenshot_chrome`
- `https_certificate_date`
- `https_certificate_body`
- `https_certificate_domain`
- `https_certificate_issuer`
- `https_certificate_expiry`
- `https_certificate_public_key`
- `https_certificate_signature_algorithm`
- `https_certificate_extensions`
- `phishing_flag`
- `phishing_flag_date`
- `phishing_confirm_flag`
- `phishing_confirm_flag_date`
- `actor`
- `html_mobile_site_iphone`
- `html_mobile_site_android`
- `html_pc_redirect`
- `html_mobile_redirect_iphone`
- `html_mobile_redirect_android`
- `screenshot_availability`
- `url_mobile_redirect_iphone`
- `url_mobile_redirect_android`
- `https_certficate_all`
- `https_certificate_all`

## Usage

1. Clone this repository or download the script file.
2. Update the database connection details in the script:

```python
conn = psycopg2.connect(
    dbname="your_db_name",
    user="your_user",
    password="your_password",
    host="your_host",
    port="your_port"
)
```

3. Modify the `search_domain` variable with the domain you want to search for:

```python
search_domain = "example.com"
```

4. Run the script:

```bash
python your_script.py
```

The script will query the database and output the results in the following format:

```
id: 1
status: 200
last_update: 2024-01-01 12:00:00
...
```

## Example Output

```plaintext
id: 1
status: 1
last_update: 2024-01-01 12:00:00
phish_from: attacker@example.com
url: http://phishing-example.com
...
```

```

---

