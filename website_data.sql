--
-- PostgreSQL database dump
--

-- Dumped from database version 12.20 (Ubuntu 12.20-0ubuntu0.20.04.1)
-- Dumped by pg_dump version 12.20 (Ubuntu 12.20-0ubuntu0.20.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: website_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.website_data (
    id integer NOT NULL,
    status integer,
    last_update timestamp without time zone,
    phish_from text,
    url text,
    phish_id bigint,
    phish_detail_url text,
    phish_ip_address character varying(50),
    cidr_block text,
    verified boolean,
    online_status boolean,
    target character varying(512),
    domain_db_inserted_at date,
    domain_id integer NOT NULL,
    domain character varying(1024),
    domain_status text,
    domain_registrar character varying(255),
    whois_date date,
    whois_domain text,
    registrant_name text,
    admin_name text,
    tech_name text,
    dig_info_a text,
    dig_info_mx text,
    dig_info_ns text,
    dig_info_ttl_a bigint,
    dig_info_ttl_ns bigint,
    dig_info_ttl_mx bigint,
    ip_address character varying(50),
    ip_info text,
    ip_retrieval_date timestamp without time zone,
    ip_organization character varying(255),
    ip_location character varying(255),
    hosting_provider character varying(255),
    whois_ip text,
    url_date date,
    url_pc_site text,
    url_pc_redirect text,
    url_mobile_site text,
    html_pc_site text,
    screenshot_iphone text,
    screenshot_android text,
    screenshot_chrome text,
    https_certificate_date date,
    https_certificate_body text,
    https_certificate_domain character varying(255),
    https_certificate_issuer character varying(255),
    https_certificate_expiry text,
    https_certificate_public_key text,
    https_certificate_signature_algorithm character varying(100),
    https_certificate_extensions text,
    phishing_flag boolean,
    phishing_flag_date date,
    phishing_confirm_flag boolean,
    phishing_confirm_flag_date date,
    actor character varying(255),
    html_mobile_site_iphone text,
    html_mobile_site_android text,
    html_pc_redirect text,
    html_mobile_redirect_iphone text,
    html_mobile_redirect_android text,
    screenshot_availability boolean,
    url_mobile_redirect_iphone text,
    url_mobile_redirect_android text,
    https_certficate_all text,
    https_certificate_all text,
    mhtml_content_pc bytea,
    mhtml_mobile_site_iphone bytea,
    mhtml_mobile_site_android bytea,
    mhtml_pc_site bytea
);


ALTER TABLE public.website_data OWNER TO postgres;

--
-- Name: website_data_domain_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.website_data_domain_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.website_data_domain_id_seq OWNER TO postgres;

--
-- Name: website_data_domain_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.website_data_domain_id_seq OWNED BY public.website_data.domain_id;


--
-- Name: website_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.website_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.website_data_id_seq OWNER TO postgres;

--
-- Name: website_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.website_data_id_seq OWNED BY public.website_data.id;


--
-- Name: website_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.website_data ALTER COLUMN id SET DEFAULT nextval('public.website_data_id_seq'::regclass);


--
-- Name: website_data domain_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.website_data ALTER COLUMN domain_id SET DEFAULT nextval('public.website_data_domain_id_seq'::regclass);


--
-- Name: website_data website_data_domain_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.website_data
    ADD CONSTRAINT website_data_domain_key UNIQUE (domain);


--
-- Name: website_data website_data_domain_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.website_data
    ADD CONSTRAINT website_data_domain_unique UNIQUE (domain);


--
-- Name: website_data website_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.website_data
    ADD CONSTRAINT website_data_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

